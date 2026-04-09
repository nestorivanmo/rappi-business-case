import json

from fastapi import APIRouter, Request
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

router = APIRouter(prefix="/api")


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    kam: str
    messages: list[ChatMessage]


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
        async for chunk in router_agent.chat_stream(messages):
            yield {"event": "message", "data": json.dumps({"content": chunk})}
        yield {"event": "done", "data": ""}

    return EventSourceResponse(event_generator())
