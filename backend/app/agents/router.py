import os
from typing import AsyncIterator

from app.agents.base import BaseAgent
from app.agents.diagnostic import DiagnosticAgent
from app.agents.rgm_strategy import RGMStrategyAgent
from app.agents.budget_agent import BudgetAgentImpl
from app.agents.tools import ROUTER_TOOLS
from app.llm.types import Message
from app.llm.factory import get_agent_provider
from app.config import Settings
from app.observability.tracing import get_langfuse


def _load_prompt() -> str:
    path = os.path.join(os.path.dirname(__file__), "prompts", "router.txt")
    with open(path) as f:
        return f.read()


class RouterAgent:
    def __init__(self, settings: Settings, engine, budget_manager, kam_name: str):
        self.kam_name = kam_name

        # Create sub-agents with per-agent provider overrides
        diag_provider = get_agent_provider("diagnostic_agent", settings)
        rgm_provider = get_agent_provider("rgm_agent", settings)
        budget_provider = get_agent_provider("budget_agent", settings)

        self.diagnostic = DiagnosticAgent(diag_provider, engine, kam_name)
        self.rgm_strategy = RGMStrategyAgent(rgm_provider, engine, budget_manager, kam_name)
        self.budget = BudgetAgentImpl(budget_provider, budget_manager, kam_name)

        # Router's own provider
        router_provider = get_agent_provider("llm", settings)
        system_prompt = _load_prompt().format(kam_name=kam_name)

        # _active_span is set per-request to pass tracing context to sub-agent tools
        self._active_span = None

        tool_handlers = {
            "call_diagnostic_agent": self._call_diagnostic,
            "call_rgm_strategy_agent": self._call_rgm,
            "call_budget_agent": self._call_budget,
        }
        self.agent = BaseAgent(
            "router", router_provider, system_prompt, ROUTER_TOOLS, tool_handlers
        )

    async def _call_diagnostic(self, message: str) -> str:
        msg = f"[KAM: {self.kam_name}] {message}"
        return await self.diagnostic.run(
            [Message(role="user", content=msg)],
            parent_span=self._active_span,
        )

    async def _call_rgm(self, message: str, diagnostic_context: str = "") -> str:
        full_msg = f"[KAM: {self.kam_name}] {message}"
        if diagnostic_context:
            full_msg = f"Diagnostic context:\n{diagnostic_context}\n\n[KAM: {self.kam_name}] {message}"
        return await self.rgm_strategy.run(
            [Message(role="user", content=full_msg)],
            parent_span=self._active_span,
        )

    async def _call_budget(self, message: str) -> str:
        msg = f"[KAM: {self.kam_name}] {message}"
        return await self.budget.run(
            [Message(role="user", content=msg)],
            parent_span=self._active_span,
        )

    async def chat(self, messages: list[Message]) -> str:
        lf = get_langfuse()
        trace = None
        if lf:
            trace = lf.start_observation(
                name="chat",
                as_type="span",
                input=messages[-1].content if messages else None,
                metadata={"kam_name": self.kam_name},
            )

        self._active_span = trace
        try:
            result = await self.agent.run(messages, parent_span=trace)
            if trace:
                trace.update(output=result[:500])
                trace.end()
            return result
        except Exception as e:
            if trace:
                trace.update(level="ERROR", status_message=str(e))
                trace.end()
            raise
        finally:
            self._active_span = None
            if lf:
                lf.flush()

    async def chat_stream(self, messages: list[Message]) -> AsyncIterator[str]:
        lf = get_langfuse()
        trace = None
        if lf:
            trace = lf.start_observation(
                name="chat",
                as_type="span",
                input=messages[-1].content if messages else None,
                metadata={"kam_name": self.kam_name},
            )

        self._active_span = trace
        try:
            collected = []
            async for chunk in self.agent.run_stream(messages, parent_span=trace):
                collected.append(chunk)
                yield chunk

            if trace:
                trace.update(output="".join(collected)[:500])
                trace.end()
        except Exception as e:
            if trace:
                trace.update(level="ERROR", status_message=str(e))
                trace.end()
            raise
        finally:
            self._active_span = None
            if lf:
                lf.flush()
