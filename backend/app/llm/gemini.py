import asyncio
import json
import uuid
from typing import AsyncIterator

from google import genai
from google.genai import types
from google.genai.errors import ClientError

from app.llm.types import (
    Message, ToolDefinition, LLMResponse, StreamChunk, ToolCall, TokenUsage,
)

MAX_RETRIES = 3
RETRY_BASE_DELAY = 10  # seconds


async def _retry_on_rate_limit(coro_fn, *args, **kwargs):
    """Retry a coroutine on 429 rate limit errors with exponential backoff."""
    for attempt in range(MAX_RETRIES):
        try:
            return await coro_fn(*args, **kwargs)
        except ClientError as e:
            if e.code == 429 and attempt < MAX_RETRIES - 1:
                delay = RETRY_BASE_DELAY * (2 ** attempt)
                print(f"[Gemini] Rate limited, retrying in {delay}s (attempt {attempt + 1}/{MAX_RETRIES})")
                await asyncio.sleep(delay)
            else:
                raise


def _messages_to_contents(messages: list[Message]) -> list[types.Content]:
    """Convert unified messages to Gemini Content objects."""
    contents = []
    for msg in messages:
        if msg.role == "user":
            contents.append(types.Content(
                role="user",
                parts=[types.Part.from_text(text=msg.content or "")],
            ))
        elif msg.role == "assistant":
            parts = []
            if msg.content:
                parts.append(types.Part.from_text(text=msg.content))
            if msg.tool_calls:
                for tc in msg.tool_calls:
                    parts.append(types.Part.from_function_call(
                        name=tc.name,
                        args=tc.arguments,
                    ))
            contents.append(types.Content(role="model", parts=parts))
        elif msg.role == "tool":
            # Gemini expects function responses as model-role content
            result = json.loads(msg.content) if isinstance(msg.content, str) else msg.content
            # Find the corresponding tool call name from the previous assistant message
            tool_name = msg.tool_call_id or "unknown"
            # Look back for the tool call name
            for prev in reversed(contents):
                if prev.role == "model" and prev.parts:
                    for part in prev.parts:
                        if hasattr(part, "function_call") and part.function_call:
                            if not msg.tool_call_id or part.function_call.name == msg.tool_call_id:
                                tool_name = part.function_call.name
                                break
                    break
            contents.append(types.Content(
                role="user",
                parts=[types.Part.from_function_response(
                    name=tool_name,
                    response=result if isinstance(result, dict) else {"result": result},
                )],
            ))
    return contents


def _tools_to_declarations(tools: list[ToolDefinition]) -> list[types.Tool]:
    """Convert unified tool definitions to Gemini tool declarations."""
    declarations = []
    for tool in tools:
        declarations.append(types.FunctionDeclaration(
            name=tool.name,
            description=tool.description,
            parameters=tool.parameters,
        ))
    return [types.Tool(function_declarations=declarations)]


def _extract_tool_calls(response) -> list[ToolCall]:
    """Extract tool calls from Gemini response."""
    tool_calls = []
    if response.candidates and response.candidates[0].content:
        for part in response.candidates[0].content.parts:
            if part.function_call:
                tool_calls.append(ToolCall(
                    id=part.function_call.name,  # Gemini uses name as ID
                    name=part.function_call.name,
                    arguments=dict(part.function_call.args) if part.function_call.args else {},
                ))
    return tool_calls


class GeminiProvider:
    def __init__(self, model: str = "gemini-2.5-flash", api_key: str = ""):
        self.client = genai.Client(api_key=api_key)
        self.model = model

    async def chat(
        self,
        messages: list[Message],
        system_prompt: str,
        tools: list[ToolDefinition] | None = None,
        temperature: float = 0.7,
    ) -> LLMResponse:
        contents = _messages_to_contents(messages)
        config = types.GenerateContentConfig(
            system_instruction=system_prompt,
            temperature=temperature,
        )
        if tools:
            config.tools = _tools_to_declarations(tools)

        response = await _retry_on_rate_limit(
            self.client.aio.models.generate_content,
            model=self.model,
            contents=contents,
            config=config,
        )

        tool_calls = _extract_tool_calls(response)
        content = None
        if response.candidates and response.candidates[0].content:
            text_parts = [
                p.text for p in response.candidates[0].content.parts
                if p.text
            ]
            if text_parts:
                content = "".join(text_parts)

        usage = None
        if response.usage_metadata:
            usage = TokenUsage(
                input_tokens=response.usage_metadata.prompt_token_count or 0,
                output_tokens=response.usage_metadata.candidates_token_count or 0,
            )

        return LLMResponse(
            content=content,
            tool_calls=tool_calls if tool_calls else None,
            usage=usage,
            finish_reason="tool_calls" if tool_calls else "stop",
        )

    async def chat_stream(
        self,
        messages: list[Message],
        system_prompt: str,
        tools: list[ToolDefinition] | None = None,
        temperature: float = 0.7,
    ) -> AsyncIterator[StreamChunk]:
        contents = _messages_to_contents(messages)
        config = types.GenerateContentConfig(
            system_instruction=system_prompt,
            temperature=temperature,
        )
        if tools:
            config.tools = _tools_to_declarations(tools)

        stream = await _retry_on_rate_limit(
            self.client.aio.models.generate_content_stream,
            model=self.model,
            contents=contents,
            config=config,
        )
        async for chunk in stream:
            if chunk.candidates and chunk.candidates[0].content:
                for part in chunk.candidates[0].content.parts:
                    if part.text:
                        yield StreamChunk(content=part.text)
                    if part.function_call:
                        yield StreamChunk(tool_calls=[ToolCall(
                            id=part.function_call.name,
                            name=part.function_call.name,
                            arguments=dict(part.function_call.args) if part.function_call.args else {},
                        )])

        yield StreamChunk(finish_reason="stop")
