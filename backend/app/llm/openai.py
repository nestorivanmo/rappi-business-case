import json
from typing import AsyncIterator

from openai import AsyncOpenAI

from app.llm.types import (
    Message, ToolDefinition, LLMResponse, StreamChunk, ToolCall, TokenUsage,
)


def _messages_to_openai(messages: list[Message], system_prompt: str) -> list[dict]:
    """Convert unified messages to OpenAI format."""
    result = [{"role": "system", "content": system_prompt}]
    for msg in messages:
        if msg.role == "user":
            result.append({"role": "user", "content": msg.content or ""})
        elif msg.role == "assistant":
            entry: dict = {"role": "assistant"}
            if msg.content:
                entry["content"] = msg.content
            if msg.tool_calls:
                entry["tool_calls"] = [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.name,
                            "arguments": json.dumps(tc.arguments),
                        },
                    }
                    for tc in msg.tool_calls
                ]
            result.append(entry)
        elif msg.role == "tool":
            result.append({
                "role": "tool",
                "tool_call_id": msg.tool_call_id or "",
                "content": msg.content or "",
            })
    return result


def _tools_to_openai(tools: list[ToolDefinition]) -> list[dict]:
    return [
        {
            "type": "function",
            "function": {
                "name": t.name,
                "description": t.description,
                "parameters": t.parameters,
            },
        }
        for t in tools
    ]


class OpenAIProvider:
    def __init__(self, model: str = "gpt-4o", api_key: str = ""):
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = model

    async def chat(
        self,
        messages: list[Message],
        system_prompt: str,
        tools: list[ToolDefinition] | None = None,
        temperature: float = 0.7,
    ) -> LLMResponse:
        kwargs: dict = {
            "model": self.model,
            "messages": _messages_to_openai(messages, system_prompt),
            "temperature": temperature,
        }
        if tools:
            kwargs["tools"] = _tools_to_openai(tools)

        response = await self.client.chat.completions.create(**kwargs)
        choice = response.choices[0]

        tool_calls = None
        if choice.message.tool_calls:
            tool_calls = [
                ToolCall(
                    id=tc.id,
                    name=tc.function.name,
                    arguments=json.loads(tc.function.arguments),
                )
                for tc in choice.message.tool_calls
            ]

        usage = None
        if response.usage:
            usage = TokenUsage(
                input_tokens=response.usage.prompt_tokens,
                output_tokens=response.usage.completion_tokens,
            )

        return LLMResponse(
            content=choice.message.content,
            tool_calls=tool_calls,
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
        kwargs: dict = {
            "model": self.model,
            "messages": _messages_to_openai(messages, system_prompt),
            "temperature": temperature,
            "stream": True,
        }
        if tools:
            kwargs["tools"] = _tools_to_openai(tools)

        stream = await self.client.chat.completions.create(**kwargs)
        async for chunk in stream:
            delta = chunk.choices[0].delta if chunk.choices else None
            if not delta:
                continue
            if delta.content:
                yield StreamChunk(content=delta.content)
            if delta.tool_calls:
                for tc in delta.tool_calls:
                    if tc.function and tc.function.name:
                        yield StreamChunk(tool_calls=[ToolCall(
                            id=tc.id or "",
                            name=tc.function.name,
                            arguments=json.loads(tc.function.arguments) if tc.function.arguments else {},
                        )])

        yield StreamChunk(finish_reason="stop")
