import json
import os
from typing import AsyncIterator

from app.agents.base import BaseAgent
from app.agents.diagnostic import DiagnosticAgent
from app.agents.rgm_strategy import RGMStrategyAgent
from app.agents.budget_agent import BudgetAgentImpl
from app.agents.tools import ROUTER_TOOLS
from app.llm.types import Message, LLMResponse
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
        """Custom streaming loop that bypasses the router's wrap-up LLM call.

        The router prompt instructs the model to relay each specialist agent's
        response verbatim ("When presenting the specialist agent's response,
        relay it faithfully without adding your own analysis."), so the
        router's final streaming LLM call is effectively a no-op paraphrase.
        We skip it entirely and stream the sub-agent's final synthesis
        directly to the client instead — saving one full LLM round-trip
        (~3-5s on Gemini 2.5 Flash) per request.

        Flow:
          1. Router LLM call (non-streaming) → picks a sub-agent to delegate to.
          2. Invoke that sub-agent via `run_stream()`, yielding chunks as they
             arrive. The sub-agent's own tool loop + final streaming synthesis
             is what the user sees.
          3. Append the collected sub-agent text to the conversation so the
             router can decide whether to call another specialist (e.g. RGM
             after diagnostic). Loop.
          4. When the router returns no tool calls, stop — no wrap-up call.

        Multi-step flows (e.g. diagnostic → rgm) stream both specialists'
        outputs to the client in sequence.
        """
        lf = get_langfuse()
        trace = None
        if lf:
            trace = lf.start_observation(
                name="chat",
                as_type="span",
                input=messages[-1].content if messages else None,
                metadata={"kam_name": self.kam_name},
            )

        router_span = None
        if trace:
            router_span = trace.start_observation(
                name="router",
                as_type="agent",
                input=messages[-1].content if messages else None,
            )

        self._active_span = trace

        # Map router tool names → (sub-agent instance, message builder).
        # Each builder takes tool_call.arguments and returns a list[Message]
        # to feed into sub_agent.run_stream().
        def _build_diag_msgs(args: dict) -> list[Message]:
            content = f"[KAM: {self.kam_name}] {args.get('message', '')}"
            return [Message(role="user", content=content)]

        def _build_rgm_msgs(args: dict) -> list[Message]:
            base = args.get("message", "")
            diag_ctx = args.get("diagnostic_context", "")
            if diag_ctx:
                content = (
                    f"Diagnostic context:\n{diag_ctx}\n\n"
                    f"[KAM: {self.kam_name}] {base}"
                )
            else:
                content = f"[KAM: {self.kam_name}] {base}"
            return [Message(role="user", content=content)]

        def _build_budget_msgs(args: dict) -> list[Message]:
            content = f"[KAM: {self.kam_name}] {args.get('message', '')}"
            return [Message(role="user", content=content)]

        sub_agent_dispatch = {
            "call_diagnostic_agent": (self.diagnostic, _build_diag_msgs),
            "call_rgm_strategy_agent": (self.rgm_strategy, _build_rgm_msgs),
            "call_budget_agent": (self.budget, _build_budget_msgs),
        }

        try:
            conversation = list(messages)
            collected_output: list[str] = []
            max_iterations = 5  # diagnostic → rgm/budget → stop; 5 is generous
            streamed_anything = False

            for iteration in range(1, max_iterations + 1):
                response: LLMResponse = await self.agent.provider.chat(
                    messages=conversation,
                    system_prompt=self.agent.system_prompt,
                    tools=self.agent.tools,
                    temperature=0.7,
                )
                self.agent._log_generation(
                    router_span, conversation, response, iteration
                )

                if not response.tool_calls:
                    # Router has nothing more to delegate. If we never streamed
                    # any sub-agent output, yield whatever the router said as a
                    # fallback (rare — typically happens only for trivial
                    # prompts like "hola" where the router answers directly).
                    if not streamed_anything and response.content:
                        collected_output.append(response.content)
                        yield response.content
                    break

                # Record the router's tool-call request in the conversation
                # so the follow-up iteration has the right history.
                conversation.append(
                    Message(
                        role="assistant",
                        content=response.content,
                        tool_calls=response.tool_calls,
                    )
                )

                for tc in response.tool_calls:
                    dispatch = sub_agent_dispatch.get(tc.name)
                    if dispatch is None:
                        # Unknown tool — fall back to the standard handler so
                        # nothing silently breaks.
                        result = await self.agent._execute_tool(
                            tc, parent_span=router_span
                        )
                        conversation.append(
                            Message(
                                role="tool",
                                content=result,
                                tool_call_id=tc.id,
                            )
                        )
                        continue

                    sub_agent, build_msgs = dispatch
                    sub_messages = build_msgs(tc.arguments)

                    # Stream the sub-agent's output directly to the client.
                    # We still collect the full text so the next router
                    # iteration sees it as a tool result.
                    sub_collected: list[str] = []
                    async for chunk in sub_agent.run_stream(
                        sub_messages, parent_span=router_span
                    ):
                        sub_collected.append(chunk)
                        collected_output.append(chunk)
                        yield chunk

                    streamed_anything = True
                    # Tool results must be JSON-encoded strings — the Gemini
                    # adapter re-parses them in _messages_to_contents to
                    # reconstruct the function-response part.
                    conversation.append(
                        Message(
                            role="tool",
                            content=json.dumps({"response": "".join(sub_collected)}),
                            tool_call_id=tc.id,
                        )
                    )

            if router_span:
                router_span.update(output="".join(collected_output)[:500])
                router_span.end()
            if trace:
                trace.update(output="".join(collected_output)[:500])
                trace.end()
        except Exception as e:
            if router_span:
                router_span.update(level="ERROR", status_message=str(e))
                router_span.end()
            if trace:
                trace.update(level="ERROR", status_message=str(e))
                trace.end()
            raise
        finally:
            self._active_span = None
            if lf:
                lf.flush()
