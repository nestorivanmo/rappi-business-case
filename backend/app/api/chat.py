import json
import os
import re

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

router = APIRouter(prefix="/api")


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    kam: str
    messages: list[ChatMessage]


class SummarizeRequest(BaseModel):
    kam: str
    messages: list[ChatMessage]


class SummarizeResponse(BaseModel):
    title: str
    summary: str


def _load_summarize_prompt() -> str:
    path = os.path.join(
        os.path.dirname(__file__), "..", "agents", "prompts", "summarize.txt"
    )
    with open(path) as f:
        return f.read()


@router.post("/chat")
async def chat(request: Request, body: ChatRequest):
    settings = request.app.state.settings
    engine = request.app.state.engine
    budget_manager = request.app.state.budget_manager

    from app.agents.router import RouterAgent
    from app.llm.types import Message

    messages = [Message(role=m.role, content=m.content) for m in body.messages]
    router_agent = RouterAgent(settings, engine, budget_manager, body.kam)

    async def event_generator():
        try:
            async for chunk in router_agent.chat_stream(messages):
                yield {"event": "message", "data": json.dumps({"content": chunk})}
        except Exception as exc:  # noqa: BLE001
            # Surface agent/LLM failures as a structured SSE payload so the
            # client stops waiting instead of hanging on a half-open stream.
            message = str(exc) or exc.__class__.__name__
            yield {"event": "message", "data": json.dumps({"error": message})}
        yield {"event": "done", "data": ""}

    return EventSourceResponse(event_generator())


@router.post("/chat/summarize", response_model=SummarizeResponse)
async def summarize_chat(request: Request, body: SummarizeRequest) -> SummarizeResponse:
    if not body.messages:
        raise HTTPException(status_code=400, detail="messages must not be empty")

    settings = request.app.state.settings

    from app.llm.factory import get_agent_provider
    from app.llm.types import Message

    transcript = "\n\n".join(f"{m.role.upper()}: {m.content}" for m in body.messages)

    provider = get_agent_provider("llm", settings)
    prompt = _load_summarize_prompt()

    response = await provider.chat(
        messages=[Message(role="user", content=f"Conversation:\n\n{transcript}")],
        system_prompt=prompt,
        tools=None,
        temperature=0.2,
    )

    raw = (response.content or "").strip()
    # Strip any ```json fences the model may emit despite instructions
    raw = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw, flags=re.MULTILINE).strip()

    try:
        parsed = json.loads(raw)
        return SummarizeResponse(
            title=str(parsed["title"])[:80],
            summary=str(parsed["summary"]),
        )
    except (json.JSONDecodeError, KeyError, TypeError):
        # Defensive fallback so the UI never crashes
        return SummarizeResponse(
            title="Conversation summary",
            summary=raw[:240] or "No summary available.",
        )
