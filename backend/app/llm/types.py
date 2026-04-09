from typing import Any

from pydantic import BaseModel


class ToolCall(BaseModel):
    id: str
    name: str
    arguments: dict[str, Any]


class Message(BaseModel):
    role: str  # "user" | "assistant" | "tool"
    content: str | None = None
    tool_calls: list[ToolCall] | None = None
    tool_call_id: str | None = None


class ToolDefinition(BaseModel):
    name: str
    description: str
    parameters: dict[str, Any]  # JSON Schema


class TokenUsage(BaseModel):
    input_tokens: int
    output_tokens: int


class LLMResponse(BaseModel):
    content: str | None = None
    tool_calls: list[ToolCall] | None = None
    usage: TokenUsage | None = None
    finish_reason: str | None = None


class StreamChunk(BaseModel):
    content: str | None = None
    tool_calls: list[ToolCall] | None = None
    finish_reason: str | None = None
