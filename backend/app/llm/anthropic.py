import json
from typing import AsyncIterator

from anthropic import AsyncAnthropic

from app.llm.types import (
    Message, ToolDefinition, LLMResponse, StreamChunk, ToolCall, TokenUsage,
)


def _messages_to_anthropic(messages: list[Message]) -> list[dict]:
    """Convert unified messages to Anthropic format."""
    result = []
    for msg in messages:
        if msg.role == "user":
            result.append({"role": "user", "content": msg.content or ""})
        elif msg.role == "assistant":
            content = []
            if msg.content:
                content.append({"type": "text", "text": msg.content})
            if msg.tool_calls:
                for tc in msg.tool_calls:
                    content.append({
                        "type": "tool_use",
                        "id": tc.id,
                        "name": tc.name,
                        "input": tc.arguments,
                    })
            result.append({"role": "assistant", "content": content})
        elif msg.role == "tool":
            result.append({
                "role": "user",
                "content": [{
                    "type": "tool_result",
                    "tool_use_id": msg.tool_call_id or "",
                    "content": msg.content or "",
                }],
            })
    return result


def _tools_to_anthropic(tools: list[ToolDefinition]) -> list[dict]:
    return [
        {
            "name": t.name,
            "description": t.description,
            "input_schema": t.parameters,
        }
        for t in tools
    ]


class AnthropicProvider:
    def __init__(self, model: str = "claude-sonnet-4-20250514", api_key: str = ""):
        self.client = AsyncAnthropic(api_key=api_key)
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
            "max_tokens": 4096,
            "system": system_prompt,
            "messages": _messages_to_anthropic(messages),
            "temperature": temperature,
        }
        if tools:
            kwargs["tools"] = _tools_to_anthropic(tools)

        response = await self.client.messages.create(**kwargs)

        content = None
        tool_calls = []
        for block in response.content:
            if block.type == "text":
                content = block.text
            elif block.type == "tool_use":
                tool_calls.append(ToolCall(
                    id=block.id,
                    name=block.name,
                    arguments=block.input,
                ))

        usage = TokenUsage(
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens,
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
        kwargs: dict = {
            "model": self.model,
            "max_tokens": 4096,
            "system": system_prompt,
            "messages": _messages_to_anthropic(messages),
            "temperature": temperature,
        }
        if tools:
            kwargs["tools"] = _tools_to_anthropic(tools)

        async with self.client.messages.stream(**kwargs) as stream:
            async for event in stream:
                if hasattr(event, "type"):
                    if event.type == "content_block_delta":
                        if hasattr(event.delta, "text"):
                            yield StreamChunk(content=event.delta.text)

        yield StreamChunk(finish_reason="stop")
