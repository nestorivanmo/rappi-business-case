# Agent runtime guide

A code-level walkthrough of how the multi-agent system actually works at runtime. Read [`02-technical-implementation.md`](./02-technical-implementation.md) first for the architecture and design rationale — this document covers how the moving parts fit together in code, what happens on a request, and how to extend or debug the system.

**Audience:** engineers maintaining or extending the agent.

---

## Mental model in 30 seconds

A KAM types a message in the chat panel. It hits `POST /api/chat` with `{kam, messages}`. FastAPI instantiates a `RouterAgent`, which wraps a `BaseAgent` whose tools are *delegations to other agents*. The router LLM classifies intent and calls one of `call_diagnostic_agent`, `call_rgm_strategy_agent`, or `call_budget_agent`. That tool synchronously runs a sub-agent — also a `BaseAgent` — whose tools call into the deterministic `DiagnosticEngine` or `BudgetManager` (pure pandas, no LLM). The sub-agent's text output is returned as the tool result, the router sees it, and streams the final response back as Server-Sent Events.

Every LLM call, every tool execution, and every nested agent run is logged as a LangFuse observation, producing a trace tree that mirrors the call hierarchy.

---

## Code anatomy

```
backend/app/
├── main.py                      FastAPI bootstrap; loads engine + budget manager at startup
├── config.py                    Settings (env vars → typed config)
│
├── api/
│   ├── chat.py                  POST /api/chat — SSE endpoint, instantiates RouterAgent per request
│   ├── dashboard.py             GET endpoints for portfolio data (no LLM)
│   └── budget_routes.py         GET endpoints for budget state (no LLM)
│
├── agents/
│   ├── base.py                  BaseAgent: the tool-calling loop. ALL agents extend this.
│   ├── router.py                RouterAgent: owns sub-agents, creates the root LangFuse trace
│   ├── diagnostic.py            DiagnosticAgent: read-only data tools
│   ├── rgm_strategy.py          RGMStrategyAgent: strategy generation
│   ├── budget_agent.py          BudgetAgentImpl: budget operations
│   ├── tools.py                 All ToolDefinitions (JSON schemas) for all agents
│   └── prompts/                 System prompts as plain .txt files
│
├── llm/
│   ├── protocol.py              LLMProvider Protocol (the contract)
│   ├── types.py                 Message, ToolCall, ToolDefinition, LLMResponse, StreamChunk
│   ├── factory.py               create_provider() / get_agent_provider() — env-driven selection
│   ├── gemini.py                GeminiProvider adapter
│   ├── openai.py                OpenAIProvider adapter
│   └── anthropic.py             AnthropicProvider adapter
│
├── engine/                      Diagnostic engine (pandas, deterministic)
│   ├── loader.py                CSV → DataFrame, applies scoring + classification at load
│   ├── scoring.py               6-signal Health Score formula (see docs/01-business-case.md)
│   ├── classification.py        Pareto split + GROW/RESCUE/NURTURE/TRIAGE assignment
│   ├── velocity.py              Velocity override rules
│   └── queries.py               All read functions exposed as tools
│
├── budget/                      Budget manager (in-memory + CSV persistence)
│   ├── manager.py               BudgetManager: balance, log, ROI, escalation
│   ├── store.py                 CSV-backed intervention log
│   └── models.py                Pydantic models for Intervention, KAMBudget
│
└── observability/
    └── tracing.py               get_langfuse() — singleton client, no-op if not configured
```

---

## The execution loop (`BaseAgent`)

`BaseAgent` (`backend/app/agents/base.py`) is the only place where LLM-driven control flow lives. Every agent in the system is an instance of it, parameterized by:

- `name` — for tracing/logging
- `provider` — an `LLMProvider` (Gemini/OpenAI/Anthropic)
- `system_prompt` — string loaded from `prompts/*.txt`
- `tools` — a list of `ToolDefinition` (JSON schemas)
- `tool_handlers` — `{tool_name: callable}` map for execution

Two entry points:

| Method | Use case |
|---|---|
| `run(messages, parent_span=None) -> str` | Sub-agents called from a tool handler. Returns the final string. Internally non-streaming throughout. |
| `run_stream(messages, parent_span=None) -> AsyncIterator[str]` | The outermost agent. Runs the tool loop non-streaming, then streams the final response token-by-token. |

### Tool loop, step by step

```python
for _ in range(max_iterations):  # 10
    response = await provider.chat(messages, system_prompt, tools)
    log_generation(response)                    # → LangFuse

    if response.tool_calls:
        append assistant message with tool_calls to conversation
        for tc in response.tool_calls:
            result = await execute_tool(tc)     # → LangFuse tool span
            append tool result message to conversation
        # loop again — feed tool results back to the model
    else:
        # No tool call → final answer
        return response.content                 # (or stream it, in run_stream)
```

Three properties matter:

1. **The loop is bounded** at 10 iterations. If the model keeps calling tools without producing a final answer, the agent returns a fallback string and the trace is marked `WARNING`. This is the only safety net against infinite loops.
2. **Tool results are JSON-serialized** before being fed back as `role="tool"` messages. Errors get serialized as `{"error": "..."}` rather than raised, so a single broken tool doesn't kill the loop — the model usually recovers by trying a different tool or apologizing.
3. **Streaming is final-only.** Tool-calling iterations are non-streaming because we need the full structured response to dispatch tools. Once the model produces a tool-call-free response, `run_stream` re-issues that same prompt with `chat_stream` to get token-by-token output. This means there's a brief delay before the first SSE chunk arrives — the user sees "Thinking..." while iterations 1..N-1 happen.

---

## Request lifecycle: `POST /api/chat`

```
1. chat.py:chat()
   ├── Parse {kam, messages} from body
   ├── Build [Message(role, content)] list
   ├── Construct RouterAgent(settings, engine, budget_manager, kam)
   │   └── RouterAgent.__init__:
   │       ├── Resolve providers via get_agent_provider() for each agent
   │       ├── Instantiate DiagnosticAgent, RGMStrategyAgent, BudgetAgentImpl
   │       ├── Load router prompt, format with kam_name
   │       └── Wrap self in a BaseAgent("router", router_provider, prompt, ROUTER_TOOLS, handlers)
   └── Return EventSourceResponse(event_generator())
        └── async for chunk in router_agent.chat_stream(messages):
                yield {"event": "message", "data": json.dumps({"content": chunk})}

2. RouterAgent.chat_stream()
   ├── lf.start_observation(name="chat", as_type="span", input=last_user_message, metadata={kam_name})
   ├── self._active_span = trace
   ├── async for chunk in self.agent.run_stream(messages, parent_span=trace):
   │       collected.append(chunk); yield chunk
   ├── trace.update(output=collected); trace.end()
   └── lf.flush()

3. BaseAgent("router").run_stream()
   └── Tool loop (see above). On tool call:
       └── _execute_tool(call_diagnostic_agent, parent_span=router_agent_span)
           └── self.tool_handlers["call_diagnostic_agent"](message="...")
               └── RouterAgent._call_diagnostic(message)
                   ├── prepend [KAM: Ana Torres] to message  ← KAM context injection
                   └── await self.diagnostic.run([Message(role="user", content=msg)],
                                                  parent_span=self._active_span)
                       └── BaseAgent("diagnostic").run()
                           └── Tool loop again, calling engine.* functions
                           └── Returns final string

4. Sub-agent's string is JSON-encoded and appended as role="tool" message
5. Router loop iterates: model sees the tool result, decides next step
6. Router eventually produces a tool-call-free response → streamed via chat_stream
7. Each yielded chunk is wrapped in an SSE event and pushed to the frontend
```

The whole call tree is captured in LangFuse as nested observations under the root `chat` span. See the **Tracing** section below.

---

## Provider abstraction

The three concrete providers (`gemini.py`, `openai.py`, `anthropic.py`) all implement the same shape, defined informally by `LLMProvider` in `protocol.py`:

```python
async def chat(messages, system_prompt, tools=None, temperature=0.7) -> LLMResponse
async def chat_stream(messages, system_prompt, tools=None, temperature=0.7) -> AsyncIterator[StreamChunk]
```

Each adapter is responsible for:

1. **Translating** the unified `Message`/`ToolDefinition` types into the provider's native format (Gemini `Content`/`FunctionDeclaration`, OpenAI `messages`/`tools`, Anthropic `messages`/`tools`).
2. **Translating back** the provider's response into `LLMResponse` (`content`, `tool_calls`, `usage`, `finish_reason`).
3. **Handling provider quirks** — e.g., Gemini uses `function_call.name` as the call ID, OpenAI generates a `tool_call_id`, Anthropic uses `tool_use_id`. These are normalized inside the adapter.
4. **Error handling and retries** — `gemini.py` has `_retry_on_rate_limit()` for 429s with exponential backoff. Add equivalents to other adapters as needed.

### Provider selection

`factory.get_agent_provider(agent_name, settings)` resolves the provider for one agent by checking, in order:

1. `{agent_name}_provider` env var (e.g., `RGM_AGENT_PROVIDER=openai`)
2. `LLM_PROVIDER` (default fallback)

Same for `_model`. This means you can run the diagnostic agent on Gemini Flash and the RGM agent on GPT-4o without changing any code — just `.env`.

```bash
LLM_PROVIDER=gemini
LLM_MODEL=gemini-2.5-flash
RGM_AGENT_PROVIDER=openai
RGM_AGENT_MODEL=gpt-4o
```

**Gotcha:** the `factory.get_agent_provider("llm", settings)` call inside `RouterAgent.__init__` is a hack — it's looking up `llm_provider`/`llm_model`, not a per-agent override. The router always uses the default provider. If you want per-router overrides, add `router_provider`/`router_model` to `Settings` and adjust the call.

---

## Tool definitions and handlers

Tools are split across two places:

**`agents/tools.py`** — declarative tool schemas (`ToolDefinition` objects with name, description, JSON-Schema parameters). Grouped into `DIAGNOSTIC_TOOLS`, `RGM_TOOLS`, `BUDGET_TOOLS`, `ROUTER_TOOLS`.

**Each agent's `__init__`** — the `tool_handlers` dict that maps each tool name to a callable. Handlers are usually thin lambdas wrapping engine or budget manager methods:

```python
# diagnostic.py
tool_handlers = {
    "get_portfolio_overview": lambda **kw: engine.get_portfolio_overview(**kw),
    "get_kam_briefing":       lambda **kw: engine.get_kam_briefing(**kw),
    ...
}
```

The router is the exception — its handlers are bound methods on `RouterAgent` itself (`_call_diagnostic`, `_call_rgm`, `_call_budget`) because they need to (a) prepend the KAM context and (b) pass the active LangFuse span to the sub-agent.

Why split schemas from handlers? The schemas are pure data — easy to unit-test, easy to round-trip through provider adapters. The handlers are tied to runtime objects (engine, budget manager). Keeping them separate means tools can be defined once and reused across agents (e.g., `get_restaurant_detail` is in both `DIAGNOSTIC_TOOLS` and `RGM_TOOLS`).

---

## KAM context propagation

The chat endpoint receives `kam` as a top-level field in the request body. This flows through three places:

1. **`RouterAgent.__init__`** stores `self.kam_name = kam`.
2. **The router system prompt** is `.format(kam_name=kam)` so the model knows whose portfolio it's looking at.
3. **`_call_diagnostic` / `_call_rgm` / `_call_budget`** prepend `[KAM: {self.kam_name}]` to the message before delegating.

That third step is load-bearing. Without it, the sub-agents would see only the abstract message ("Give me my weekly briefing") and would have no way to know which KAM's data to fetch — they'd ask the user for it. The sub-agent system prompts are written to look for that `[KAM: ...]` tag and pass the name into their tool calls.

If you add a new sub-agent, do the same: prepend the tag in its router handler.

---

## Tracing & observability

All instrumentation lives in `BaseAgent` and `RouterAgent` — there is no decorator. The `tracing.py` module exports just `get_langfuse()`, a lazy singleton that returns `None` if `LANGFUSE_PUBLIC_KEY` is not set, making the entire tracing pipeline a no-op outside of dev/prod.

### Trace hierarchy

A single chat request produces this tree:

```
chat                              span     ← root, created by RouterAgent
└── router                        agent    ← BaseAgent("router")
    ├── router.llm_call_1         generation
    ├── call_diagnostic_agent     tool
    │   └── diagnostic            agent    ← BaseAgent("diagnostic")
    │       ├── diagnostic.llm_call_1   generation
    │       ├── get_kam_briefing  tool
    │       ├── get_velocity_alerts tool
    │       └── diagnostic.llm_call_2   generation
    ├── router.llm_call_2         generation
    └── (final streamed response)
```

### What gets logged

| Observation | When | Captured fields |
|---|---|---|
| `span` ("chat") | `RouterAgent.chat_stream` start | `input` (last user message), `metadata.kam_name`, `output` (collected stream) |
| `agent` (per agent) | `BaseAgent.run` / `run_stream` start | `input` (last message), `output` (final text, truncated 500 chars) |
| `generation` (per LLM call) | After `provider.chat()` returns | `model`, `input` (last 5 messages, truncated 200 chars each), `output` (response content), `metadata.tool_calls`, `usage_details` (input/output tokens) |
| `tool` (per tool execution) | Around `_execute_tool` | `input` (tool args), `output` (tool result or error), `level=ERROR` on failure |

### Reading the LangFuse graph view

LangFuse shows the trace as both a **timeline** (sequential, with durations) and a **graph** (call hierarchy as a flow diagram). The graph collapses observations with the same name into one node — that's why we prefix generation names with the agent name (`router.llm_call_1`, `diagnostic.llm_call_1`) so iterations from different agents don't merge.

A self-loop on a generation node (e.g., `router.llm_call_1 (2/2)`) means the same agent invoked the same iteration label twice in this trace. That happens because the loop's iteration counter is local to one `run_stream` call, and after a tool returns, the next LLM call also gets `_1` if the iteration counter didn't advance correctly. *(Known minor issue — see the iteration counter in `base.py:run_stream`.)*

---

## Streaming protocol

The chat endpoint uses Server-Sent Events via `sse-starlette`. Three event types:

```
event: message
data: {"content": "Here's your"}

event: message
data: {"content": " weekly briefing..."}

event: done
data:
```

The frontend's `streamChat` (`frontend/src/lib/api.ts`) reads the SSE stream, parses each `data:` line as JSON, and yields the `content` field. The hook `useChat` accumulates the chunks into a single assistant message.

**Critical detail:** the SSE response only starts emitting events after the tool loop is done. If the diagnostic agent calls 4 tools before producing a final answer, the user sees no output for several seconds. The first chunk arrives only when `provider.chat_stream` starts emitting tokens. There is no streaming for tool-call iterations — the LangFuse spans are written, but nothing flows over the wire.

This is by design (you can't stream a JSON tool call meaningfully), but it means latency optimization should focus on tool count and tool execution time, not on token streaming speed.

---

## Adding a new tool

Steps to expose a new diagnostic engine method as a tool:

1. **Implement the engine method** in `engine/queries.py` and expose it on `DiagnosticEngine` (`engine/__init__.py`). Return a JSON-serializable dict or list.
2. **Add the schema** to `agents/tools.py` in the appropriate `*_TOOLS` list:
   ```python
   ToolDefinition(
       name="get_my_thing",
       description="What this tool returns and when to use it. The model reads this — be specific.",
       parameters={
           "type": "object",
           "properties": {
               "kam_name": {"type": "string", "description": "..."},
           },
           "required": ["kam_name"],
       },
   )
   ```
3. **Wire the handler** in the agent's `__init__`:
   ```python
   tool_handlers["get_my_thing"] = lambda **kw: engine.get_my_thing(**kw)
   ```
4. **Update the agent's system prompt** (`prompts/diagnostic.txt`) so the model knows when to call it. Often the tool description is enough, but for non-obvious cases add a "use `get_my_thing` when..." rule.
5. **Add an eval case** in `evals/` to lock in expected behavior.

The tool will appear in LangFuse traces immediately — no instrumentation needed.

---

## Adding a new agent

Less common, but here's the recipe:

1. **Create `agents/my_agent.py`** subclassing `BaseAgent`. Build `tool_handlers` and pass them to `super().__init__("my_agent", provider, system_prompt, MY_TOOLS, tool_handlers)`.
2. **Add `MY_TOOLS`** in `agents/tools.py`.
3. **Write `prompts/my_agent.txt`**. Make sure it tells the model to look for `[KAM: ...]` if it needs the KAM name.
4. **Add `call_my_agent`** to `ROUTER_TOOLS` in `agents/tools.py`.
5. **Wire the router**:
   - Instantiate the agent in `RouterAgent.__init__`
   - Add `_call_my_agent` method that prepends the KAM tag and calls `self.my_agent.run(..., parent_span=self._active_span)`
   - Register `"call_my_agent": self._call_my_agent` in the router's `tool_handlers`
6. **Update the router prompt** (`prompts/router.txt`) with the classification rule.
7. **Add eval scenarios.**

---

## Debugging recipes

### "The agent hangs / never responds"

The frontend shows "Thinking..." forever. Possible causes:

1. **Quota / API error.** Check uvicorn logs for 429 or 401. The Gemini adapter retries 429s up to 3 times then raises — if you don't see logs, the failure is silent in a tool handler. Look at LangFuse traces for `level=ERROR`.
2. **Tool loop maxed out.** If you see 10 iterations in LangFuse with no final answer, the model is stuck calling tools. Usually the system prompt isn't telling it to summarize, or a tool is returning malformed data. Read the tool outputs in the trace.
3. **Sub-agent missing KAM context.** Symptom: the sub-agent responds with "I need your KAM name". Check that `_call_*` in `router.py` prepends `[KAM: ...]` and that the sub-agent's prompt knows to use it.
4. **SSE connection closed early.** Frontend sees the stream end before any content. Check the network tab — a 200 with zero events usually means an exception inside `event_generator` after the response started. Look for tracebacks in the uvicorn log.

### "Tool returns wrong data"

The engine and budget queries are deterministic — call them directly in a Python REPL with the same arguments the trace shows. If they're correct in isolation, the agent is passing wrong arguments — check the tool call `input` field in LangFuse. Usually a system prompt fix.

### "LangFuse shows nothing"

1. Confirm `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`, `LANGFUSE_HOST` are set. The SDK reads `LANGFUSE_HOST`, *not* `LANGFUSE_BASE_URL`.
2. Make sure the host points to the right region (`us.cloud.langfuse.com` vs `cloud.langfuse.com`). Wrong host = silent success on a project that doesn't exist.
3. The `tracing.py` singleton swallows import errors. If you suspect the SDK is broken, run `python -c "from langfuse import Langfuse; Langfuse()"` directly.
4. `lf.flush()` is called in `RouterAgent.chat_stream`'s `finally` block. If a request crashes before `finally`, traces may be lost. Increase verbosity by adding `print` statements in `tracing.py`.

### "I want to see the actual LLM input/output"

LangFuse generation observations capture both. If you need more (e.g., the full prompt rather than the truncated last 5 messages), edit `BaseAgent._log_generation` — the truncation is there to keep traces small.

---

## Common gotchas

- **The router and sub-agents share `BaseAgent` but the router is special** in that its tool handlers call other `BaseAgent`s. Don't try to make every agent symmetric — the router needs to own the trace context (`_active_span`) so children can attach to it.
- **Tool handler exceptions are swallowed** and returned as `{"error": "..."}` strings. This is intentional (so the model can recover), but it means a broken handler is invisible unless you watch the trace. Always check LangFuse before assuming the model is being stupid.
- **`run_stream` re-issues the final prompt** to `chat_stream`. That's a second LLM call. It will appear as an extra generation in the trace and counts against your token budget.
- **Pydantic V1 warnings** from the LangFuse SDK on Python 3.14 are harmless but noisy. They're emitted at import time and don't indicate a runtime problem.
- **Uvicorn `--reload` watches Python files only.** Editing a `prompts/*.txt` file doesn't trigger a reload — restart manually.
- **The frontend always sends the full message history** with each request. The agent has no server-side memory between requests — every chat is stateless from the backend's perspective.

---

## See also

- [`01-business-case.md`](./01-business-case.md) — the scoring model and quadrant definitions the engine implements
- [`02-technical-implementation.md`](./02-technical-implementation.md) — architecture, design rationale, and the eval framework
- `backend/app/agents/base.py` — the only file you really need to read to understand the runtime
