import json
from typing import AsyncIterator, Callable, Any

from app.llm.types import Message, ToolDefinition, LLMResponse, ToolCall


class BaseAgent:
    def __init__(
        self,
        name: str,
        provider,
        system_prompt: str,
        tools: list[ToolDefinition],
        tool_handlers: dict[str, Callable[..., Any]],
    ):
        self.name = name
        self.provider = provider
        self.system_prompt = system_prompt
        self.tools = tools
        self.tool_handlers = tool_handlers

    async def _execute_tool(self, tool_call: ToolCall, parent_span=None) -> str:
        """Execute a tool call, optionally logging to LangFuse."""
        tool_span = None
        if parent_span:
            tool_span = parent_span.start_observation(
                name=tool_call.name,
                as_type="tool",
                input=tool_call.arguments,
            )

        handler = self.tool_handlers.get(tool_call.name)
        if not handler:
            error_result = json.dumps({"error": f"Unknown tool: {tool_call.name}"})
            if tool_span:
                tool_span.update(output=error_result, level="ERROR")
                tool_span.end()
            return error_result
        try:
            result = handler(**tool_call.arguments)
            if hasattr(result, "__await__"):
                result = await result
            serialized = json.dumps(result, default=str)
            if tool_span:
                tool_span.update(output=result)
                tool_span.end()
            return serialized
        except Exception as e:
            error_result = json.dumps({"error": str(e)})
            if tool_span:
                tool_span.update(output=error_result, level="ERROR", status_message=str(e))
                tool_span.end()
            return error_result

    def _log_generation(self, parent_span, messages, response: LLMResponse, iteration: int):
        """Log an LLM call as a generation observation."""
        if not parent_span:
            return
        input_msgs = [{"role": m.role, "content": m.content[:200] if m.content else None} for m in messages[-5:]]
        gen = parent_span.start_observation(
            name=f"llm_call_{iteration}",
            as_type="generation",
            model=getattr(self.provider, "model", None),
            input=input_msgs,
            output=response.content[:500] if response.content else None,
            metadata={
                "tool_calls": [{"name": tc.name, "args": tc.arguments} for tc in response.tool_calls] if response.tool_calls else None,
            },
        )
        if response.usage:
            gen.update(usage_details={
                "input": response.usage.input_tokens,
                "output": response.usage.output_tokens,
            })
        gen.end()

    async def run(self, messages: list[Message], parent_span=None) -> str:
        """Execute agent loop: send messages, handle tool calls, return final text."""
        agent_span = None
        if parent_span:
            agent_span = parent_span.start_observation(
                name=self.name,
                as_type="agent",
                input=messages[-1].content if messages else None,
            )

        active_span = agent_span  # span to attach children to
        conversation = list(messages)
        max_iterations = 10
        iteration = 0

        try:
            for _ in range(max_iterations):
                iteration += 1
                response: LLMResponse = await self.provider.chat(
                    messages=conversation,
                    system_prompt=self.system_prompt,
                    tools=self.tools if self.tools else None,
                    temperature=0.7,
                )
                self._log_generation(active_span, conversation, response, iteration)

                if response.tool_calls:
                    conversation.append(Message(
                        role="assistant",
                        content=response.content,
                        tool_calls=response.tool_calls,
                    ))
                    for tc in response.tool_calls:
                        result = await self._execute_tool(tc, parent_span=active_span)
                        conversation.append(Message(
                            role="tool",
                            content=result,
                            tool_call_id=tc.id,
                        ))
                else:
                    output = response.content or ""
                    if agent_span:
                        agent_span.update(output=output[:500])
                        agent_span.end()
                    return output

            fallback = "Agent reached maximum iterations without producing a final response."
            if agent_span:
                agent_span.update(output=fallback, level="WARNING")
                agent_span.end()
            return fallback
        except Exception as e:
            if agent_span:
                agent_span.update(level="ERROR", status_message=str(e))
                agent_span.end()
            raise

    async def run_stream(self, messages: list[Message], parent_span=None) -> AsyncIterator[str]:
        """Run tool loop non-streaming, then stream the final response."""
        agent_span = None
        if parent_span:
            agent_span = parent_span.start_observation(
                name=self.name,
                as_type="agent",
                input=messages[-1].content if messages else None,
            )

        active_span = agent_span
        conversation = list(messages)
        max_iterations = 10
        iteration = 0

        try:
            for _ in range(max_iterations):
                iteration += 1
                response: LLMResponse = await self.provider.chat(
                    messages=conversation,
                    system_prompt=self.system_prompt,
                    tools=self.tools if self.tools else None,
                    temperature=0.7,
                )
                self._log_generation(active_span, conversation, response, iteration)

                if response.tool_calls:
                    conversation.append(Message(
                        role="assistant",
                        content=response.content,
                        tool_calls=response.tool_calls,
                    ))
                    for tc in response.tool_calls:
                        result = await self._execute_tool(tc, parent_span=active_span)
                        conversation.append(Message(
                            role="tool",
                            content=result,
                            tool_call_id=tc.id,
                        ))
                else:
                    # Final response — stream it
                    collected = []
                    async for chunk in self.provider.chat_stream(
                        messages=conversation,
                        system_prompt=self.system_prompt,
                        tools=None,
                        temperature=0.7,
                    ):
                        if chunk.content:
                            collected.append(chunk.content)
                            yield chunk.content

                    if agent_span:
                        agent_span.update(output="".join(collected)[:500])
                        agent_span.end()
                    return

            if agent_span:
                agent_span.update(level="WARNING", status_message="Max iterations reached")
                agent_span.end()
            yield "Agent reached maximum iterations."
        except Exception as e:
            if agent_span:
                agent_span.update(level="ERROR", status_message=str(e))
                agent_span.end()
            raise
