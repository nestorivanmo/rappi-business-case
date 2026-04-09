from typing import Protocol, AsyncIterator

from app.llm.types import Message, ToolDefinition, LLMResponse, StreamChunk


class LLMProvider(Protocol):
    async def chat(
        self,
        messages: list[Message],
        system_prompt: str,
        tools: list[ToolDefinition] | None = None,
        temperature: float = 0.7,
    ) -> LLMResponse: ...

    async def chat_stream(
        self,
        messages: list[Message],
        system_prompt: str,
        tools: list[ToolDefinition] | None = None,
        temperature: float = 0.7,
    ) -> AsyncIterator[StreamChunk]: ...
