# Technical implementation: Proactive risk detection agent for Rappi KAMs

## Architecture overview

The system is built as a **multi-agent architecture** with a router agent that delegates to specialized agents, backed by deterministic Python computation and exposed through a web dashboard. The KAM interacts with a single conversational interface — the router handles delegation transparently.

Two core design principles govern every technical decision:

**Deterministic math for scoring, LLM reasoning for strategy and communication.** Health scores, quadrant assignments, and velocity overrides are computed by pandas — fast, reproducible, and auditable. The agents consume these structured results through function calling and generate natural-language briefings, per-restaurant recommendations, and interactive follow-up answers.

**Provider independence.** All LLM calls flow through a thin provider abstraction layer that decouples agent logic from any specific model vendor. The system ships with Google Gemini as the default provider, but can switch to OpenAI, Anthropic, or any provider that supports function calling — without touching agent logic, prompts, or tool definitions.

```
┌──────────────────────────────────────────────────────────────┐
│                      Next.js Dashboard                        │
│  KAM selector (dropdown) · Quadrant view · Alert feed · Chat │
│  Budget tracker widget · Intervention log                     │
└───────────────────────────┬──────────────────────────────────┘
                            │ REST + SSE (streaming)
┌───────────────────────────▼──────────────────────────────────┐
│                     FastAPI Backend                            │
│                                                               │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │              LLM Provider Abstraction Layer              │  │
│  │  ┌─────────┐  ┌──────────┐  ┌───────────┐              │  │
│  │  │ Gemini  │  │ OpenAI   │  │ Anthropic │  ...          │  │
│  │  │ Adapter │  │ Adapter  │  │ Adapter   │              │  │
│  │  └─────────┘  └──────────┘  └───────────┘              │  │
│  │  Unified interface: chat() · function_call() · stream() │  │
│  └──────────────────────┬──────────────────────────────────┘  │
│                         │                                     │
│  ┌──────────────────────▼──────────────────────────────────┐  │
│  │                   Router Agent                           │  │
│  │  Classifies intent → delegates to specialized agent      │  │
│  │                                                          │  │
│  │  ┌──────────────┐ ┌──────────────┐ ┌────────────────┐  │  │
│  │  │  Diagnostic   │ │ RGM Strategy │ │   Budget       │  │  │
│  │  │  Agent        │ │ Agent        │ │   Agent        │  │  │
│  │  │              │ │              │ │                │  │  │
│  │  │ Portfolio    │ │ RESCUE/TRIAGE│ │ Spend logging  │  │  │
│  │  │ overview,    │ │ recovery,    │ │ Balance check  │  │  │
│  │  │ briefings,   │ │ GROW expan., │ │ Escalation     │  │  │
│  │  │ alerts,      │ │ NURTURE      │ │ ROI tracking   │  │  │
│  │  │ drill-down   │ │ scaling      │ │                │  │  │
│  │  └──────┬───────┘ └──────┬───────┘ └───────┬────────┘  │  │
│  └─────────┼────────────────┼─────────────────┼───────────┘  │
│            │                │                 │               │
│  ┌─────────▼────────────────▼─────────────────▼───────────┐  │
│  │           Diagnostic Engine (pandas/numpy)              │  │
│  │                                                         │  │
│  │  dataset.csv → DataFrame (205 restaurants)              │  │
│  │  ├── Min-max normalization (6 signals)                  │  │
│  │  ├── Weighted composite → Health Score (0–100)          │  │
│  │  ├── Revenue = ordenes_7d × valor_ticket_prom_mxn       │  │
│  │  ├── Pareto split → High/Low Value axis                 │  │
│  │  ├── Health × Value → Quadrant assignment               │  │
│  │  ├── Velocity overrides (delta_rating, var_ordenes)     │  │
│  │  └── Budget state (balances, spend log, ROI)            │  │
│  └─────────────────────────────────────────────────────────┘  │
│                                                               │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │           LangFuse (Observability + Evals)              │  │
│  │  Traces · Token usage · Latency · Cost                  │  │
│  │  Eval datasets · Scoring runs · Regression detection    │  │
│  └─────────────────────────────────────────────────────────┘  │
└───────────────────────────────────────────────────────────────┘
```

---

## Tech stack

| Layer | Technology | Rationale |
|-------|-----------|-----------|
| Frontend | **Next.js 14** (App Router) + Tailwind CSS + shadcn/ui | Modern React framework with SSR, streaming support, and a mature component library. Deployed on Vercel for zero-config hosting. |
| Backend | **Python FastAPI** | Async-native, high-performance API layer. Hosts the agents, provider abstraction, and diagnostic engine in a single process. Deployed on Railway. |
| LLM Abstraction | **Custom provider layer** (see below) | Thin adapter pattern over provider SDKs. Default: Google Gemini. Swappable to OpenAI, Anthropic, or any function-calling-capable model without changing agent code. |
| AI Agents | **Router + 3 specialized agents** via provider abstraction | Router classifies KAM intent and delegates to Diagnostic, RGM Strategy, or Budget agents. Each agent has its own focused system prompt and tool set. |
| Default LLM | **Google Gemini** (`google-genai` SDK) with `gemini-2.5-flash` | Fast inference (~1s), 1M token context window, native function calling, structured output support. |
| Diagnostic Engine | **pandas + numpy** | Deterministic computation of health scores, quadrant assignments, velocity overrides. No LLM needed — pure math, fully reproducible and auditable. |
| Data | **dataset.csv → pandas DataFrame** (in-memory) | 205 restaurants, 18 columns, 10 KAMs. Loaded once at startup, recomputed on each request. No database needed at this scale. |
| Observability | **LangFuse** | Open-source LLM observability platform. Traces every agent call, powers the evaluation framework, and tracks cost/latency across providers. |
| Deployment | **Vercel** (frontend) + **Railway** (backend) | Vercel handles Next.js with edge caching and automatic previews. Railway hosts the Python backend with persistent processes and environment variable management. |

---

## LLM provider abstraction layer

### The problem

Coupling directly to a single provider's SDK (e.g., `google-genai`) creates three risks: (1) if Google deprecates the model, changes pricing, or introduces rate limits, the entire system goes down; (2) different agents might perform better on different models — the diagnostic agent may work fine on Flash while the RGM strategy agent produces better recommendations on a more capable model; (3) A/B testing providers becomes impossible without rewriting agent code.

### The solution

A thin adapter layer that exposes a unified interface to all agents. Each adapter wraps one provider's SDK and normalizes its API to a common contract:

```python
class LLMProvider(Protocol):
    """Unified interface for all LLM providers."""

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
```

```python
class GeminiProvider(LLMProvider):
    """Google Gemini adapter — default provider."""

    def __init__(self, model: str = "gemini-2.5-flash"):
        self.client = genai.Client()
        self.model = model

    async def chat(self, messages, system_prompt, tools=None, temperature=0.7):
        # Translates ToolDefinition → Gemini function declarations
        # Translates Gemini response → LLMResponse
        ...

class OpenAIProvider(LLMProvider):
    """OpenAI adapter — drop-in alternative."""

    def __init__(self, model: str = "gpt-4o"):
        self.client = AsyncOpenAI()
        self.model = model

    async def chat(self, messages, system_prompt, tools=None, temperature=0.7):
        # Translates ToolDefinition → OpenAI function schemas
        # Translates OpenAI response → LLMResponse
        ...
```

### What the abstraction normalizes

The critical differences between providers that the adapter layer absorbs:

| Concern | Gemini | OpenAI | Anthropic |
|---------|--------|--------|-----------|
| Function calling format | `FunctionDeclaration` in `tools` param | JSON Schema in `tools` param | JSON Schema in `tools` param |
| System prompt | `system_instruction` parameter | `system` role message | `system` parameter |
| Streaming protocol | `generate_content_stream()` | `stream=True` on `chat.completions` | `stream=True` on `messages` |
| Tool call response | `function_call` in `parts` | `tool_calls` in message | `tool_use` content block |
| Token counting | `usage_metadata` | `usage` object | `usage` object |

Each adapter translates these provider-specific formats to and from the unified `Message`, `ToolDefinition`, `LLMResponse`, and `StreamChunk` types. Agent code never imports a provider SDK directly.

### Provider configuration

Provider selection is controlled by environment variables, configurable per agent:

```
LLM_PROVIDER=gemini                    # Default provider
LLM_MODEL=gemini-2.5-flash             # Default model

DIAGNOSTIC_AGENT_PROVIDER=gemini       # Can override per agent
DIAGNOSTIC_AGENT_MODEL=gemini-2.5-flash

RGM_AGENT_PROVIDER=openai              # Example: RGM on a different model
RGM_AGENT_MODEL=gpt-4o

BUDGET_AGENT_PROVIDER=gemini           # Budget agent on default
```

This enables three things immediately: (1) swapping the entire system to a new provider by changing one env var, (2) running individual agents on the provider/model where they perform best, and (3) A/B testing providers in production by routing a percentage of traffic to each.

---

## Multi-agent architecture

### Why multiple agents instead of one

The original design considered a single agent carrying both diagnostic context and RGM playbooks in one system prompt. This works for an MVP, but has three structural limitations that compound as the system grows:

**Prompt bloat.** The diagnostic agent needs scoring methodology, quadrant definitions, and velocity rules. The RGM agent needs four playbooks (RESCUE recovery, GROW expansion, NURTURE scaling, TRIAGE evaluation) that will grow as proven strategies are catalogued per vertical, city, and restaurant archetype. The budget agent needs spending rules, balance tracking, and escalation logic. Putting all of this in one prompt creates context window pressure and attention dilution — the model performs worse on each task because it's carrying context for all tasks simultaneously.

**Independent iteration.** When the team wants to improve RGM recommendations, they shouldn't have to regression-test diagnostic briefings. When budget escalation logic changes, it shouldn't risk breaking restaurant drill-downs. Separate agents with separate prompts and separate eval suites enable independent iteration cycles.

**Targeted evaluation.** A single agent's output quality is an average across very different tasks (data summarization, strategic recommendation, budget arithmetic). Separate agents enable targeted evals: the diagnostic agent is evaluated on accuracy and completeness, the RGM agent on recommendation quality and actionability, the budget agent on arithmetic correctness and rule compliance.

### The router agent

The router is a lightweight agent with a focused job: classify the KAM's intent and delegate to the right specialist. It maintains the conversation history and handles multi-turn context, so the KAM experiences a seamless interaction.

**Router system prompt** (abbreviated):

```
You are a request router for Rappi's KAM intelligence system. Your job is to
classify each KAM message and delegate to the appropriate specialist agent.

Classification rules:
- Portfolio overview, briefings, alerts, restaurant details, comparisons,
  city/vertical breakdowns → DIAGNOSTIC
- Growth strategies, recovery plans, menu optimization, ads recommendations,
  any "what should I do?" question → RGM_STRATEGY
- Budget spending, "log an investment", balance checks, ROI questions,
  escalation requests → BUDGET

If a message spans multiple intents (e.g., "show me Burger Clásico's details
and give me a recovery plan"), call the diagnostic agent first, then pass its
output as context to the RGM agent.

Never generate restaurant data or recommendations yourself. Always delegate.
```

**Routing flow:**

```
KAM: "Give me my weekly briefing"
  → Router classifies: DIAGNOSTIC
  → Delegates to Diagnostic Agent
  → Diagnostic Agent calls tools, generates briefing
  → Router returns response to KAM

KAM: "What growth strategy for Sushi Fusión 8?"
  → Router classifies: RGM_STRATEGY
  → Router calls Diagnostic Agent first (get_restaurant_detail)
  → Passes diagnostic context to RGM Strategy Agent
  → RGM Agent generates tailored strategy
  → Router returns combined response

KAM: "Log $150 on co-funded promo for Sushi Fusión 8"
  → Router classifies: BUDGET
  → Delegates to Budget Agent
  → Budget Agent validates balance, logs spend, confirms
  → Router returns confirmation with updated balance
```

### Agent 1 — Diagnostic Agent

**Purpose:** Read signals, classify, prioritize. This agent answers "where should I look?" and "what's happening here?"

**System prompt contains:** Role definition, scoring methodology (6-signal composite, weights, normalization ranges), quadrant definitions (GROW/RESCUE/NURTURE/TRIAGE), velocity override rules, communication guidelines.

**Tools available:**

**Portfolio-level tools (the "where should I look?" layer)**

| Tool | Purpose | Returns |
|------|---------|---------|
| `get_portfolio_overview(kam_name?)` | Aggregate portfolio health snapshot | Total restaurants, quadrant distribution, total revenue, revenue at risk, velocity alert count |
| `get_kam_briefing(kam_name)` | Prioritized action list for one KAM | Ordered list: RESCUE first → velocity-escalated → TRIAGE → GROW opportunities. Each entry has health score, quadrant, revenue, dominant risk signals, time horizon |
| `get_velocity_alerts(kam_name?)` | Early warning escalation feed | Restaurants with `delta_rating < -0.4` and/or `var_ordenes_pct < -20%`, with escalation level (5-day or immediate) |
| `get_revenue_at_risk(kam_name?)` | Financial exposure summary | Total weekly revenue in RESCUE + TRIAGE, plus velocity-threatened GROW/NURTURE revenue |

**Restaurant-level tools (the "what's happening here?" layer)**

| Tool | Purpose | Returns |
|------|---------|---------|
| `get_restaurant_detail(restaurant_id)` | Complete signal profile for one restaurant | All 6 risk signals (raw + normalized), health score, quadrant, revenue, velocity status, KAM assigned, city, vertical, active since |
| `get_restaurants_by_quadrant(quadrant, kam_name?)` | Filtered segment view | All restaurants in a given quadrant, sorted by health score (ascending for RESCUE/TRIAGE, descending for GROW/NURTURE) |
| `compare_restaurants(restaurant_ids[])` | Side-by-side comparison | Signal profiles for 2–5 restaurants, highlighting where they diverge |

**Analytical tools (the "help me understand" layer)**

| Tool | Purpose | Returns |
|------|---------|---------|
| `get_city_breakdown(kam_name?)` | Geographic performance analysis | Aggregated health, revenue, and quadrant distribution by city |
| `get_vertical_breakdown(kam_name?)` | Vertical performance analysis | Same breakdown by vertical (Comida, Farmacia, Mercado, etc.) |
| `search_restaurants(query)` | Natural language search | Finds restaurants by name, city, vertical, or KAM |

### Agent 2 — RGM Strategy Agent

**Purpose:** Generate tailored Revenue Growth Management recommendations. This agent answers "what should I do?"

**System prompt contains:** Role definition, four RGM playbook frameworks, communication guidelines. The RGM agent does *not* carry scoring methodology or quadrant logic — it receives the restaurant's diagnostic profile as input context from the router.

**RGM playbooks:**

- **RESCUE/TRIAGE:** operational recovery — cancellation root-cause analysis, delivery optimization, menu simplification, emergency promos, disengagement criteria
- **GROW:** expansion strategies — ads & sponsored placement, menu & pricing optimization, exclusive promos & loyalty, dark kitchens / new zones / extended hours
- **NURTURE:** scaling strategies — volume-building promos, visibility campaigns, menu optimization for discoverability
- **WATCH (velocity override):** monitoring guidance — which specific signals to track, what thresholds trigger re-evaluation, suggested check-in cadence

**Tools available:**

| Tool | Purpose | Returns |
|------|---------|---------|
| `get_restaurant_detail(restaurant_id)` | Full signal profile (shared with Diagnostic) | Complete diagnostic context for strategy generation |
| `get_restaurants_by_quadrant(quadrant, kam_name?)` | Peer comparison for benchmarking | How similar restaurants in the same quadrant are performing |
| `get_intervention_history(restaurant_id)` | Past interventions and outcomes for a specific restaurant | Previous strategies applied, budget spent, health score trajectory post-intervention |

The `get_intervention_history` tool is critical: it allows the RGM agent to learn from what's been tried before. If a RESCUE restaurant already received a delivery optimization recommendation last month with no improvement, the agent avoids repeating the same advice and escalates to a different lever.

### Agent 3 — Budget Agent

**Purpose:** Manage KAM discretionary budgets. This agent answers "how much can I spend?" and "was my investment worth it?"

**System prompt contains:** Budget rules (weekly allocation, reset cadence, escalation thresholds), spending categories, ROI tracking logic, escalation workflow.

**Tools available:**

| Tool | Purpose | Returns |
|------|---------|---------|
| `get_budget_balance(kam_name)` | Current weekly balance | Remaining budget, total allocated, total spent this week, spend by category |
| `log_intervention(kam_name, restaurant_id, amount, category, description)` | Record a spend | Updated balance, confirmation, auto-tags with restaurant quadrant |
| `get_intervention_history(restaurant_id?, kam_name?)` | Past spend + outcomes (broader scope than RGM version) | When `restaurant_id` is given: that restaurant's history. When `kam_name` is given: all interventions by that KAM. Includes health score before/after for ROI. |
| `get_budget_roi(kam_name?, period?)` | ROI analysis | Revenue impact per $ invested, broken down by quadrant and intervention type |
| `request_escalation(kam_name, restaurant_id, amount, justification)` | Over-budget request | Packages the request with diagnostic context for supervisor approval |

**Budget data model:**

```python
class Intervention:
    id: str
    kam_name: str
    restaurant_id: str
    timestamp: datetime
    amount_mxn: float
    category: str           # "promo", "credit", "ops_support", "growth_investment"
    quadrant_at_time: str   # GROW / RESCUE / NURTURE / TRIAGE
    health_score_at_time: float
    description: str
    revenue_7d_before: float
    revenue_7d_after: float | None   # Populated after 7 days for ROI calculation

class KAMBudget:
    kam_name: str
    weekly_allocation_mxn: float
    current_week_spent: float
    reset_day: str          # "monday"
    interventions: list[Intervention]
```

At demo scale (205 restaurants, 10 KAMs), the budget state lives in-memory alongside the restaurant DataFrame. The `Intervention` log is persisted as a CSV file that appends on each `log_intervention` call and reloads at startup — simple, auditable, and sufficient for the demo. For production, this migrates to a Postgres table with proper time-series indexing.

### How agents compose: examples

**Weekly briefing:**

1. KAM asks: "Give me my weekly briefing"
2. Router classifies → DIAGNOSTIC
3. Diagnostic Agent calls `get_kam_briefing("Ana Torres")` → prioritized list of 20 restaurants
4. Diagnostic Agent calls `get_velocity_alerts("Ana Torres")` → 3 restaurants with velocity deterioration
5. Diagnostic Agent calls `get_revenue_at_risk("Ana Torres")` → $12K/week exposure
6. Diagnostic Agent synthesizes into natural-language briefing
7. Router returns to KAM

**Deep dive with strategy:**

1. KAM asks: "Tell me more about Burger Clásico — what should I do?"
2. Router classifies → spans DIAGNOSTIC + RGM_STRATEGY
3. Router calls Diagnostic Agent → `get_restaurant_detail("R0104")` → Health: 14, TRIAGE, multi-signal collapse
4. Router passes diagnostic output to RGM Strategy Agent
5. RGM Agent calls `get_intervention_history("R0104")` → no previous interventions
6. RGM Agent generates recovery strategy (or disengagement recommendation based on ROI)
7. Router returns combined diagnostic + strategy to KAM

**Budget spend:**

1. KAM asks: "I want to spend $200 on a co-funded promo for Sushi Fusión 8"
2. Router classifies → BUDGET
3. Budget Agent calls `get_budget_balance("Ana Torres")` → $340 remaining
4. Budget Agent calls `log_intervention("Ana Torres", "R0087", 200, "promo", "Co-funded weekend dinner promo")` → logs spend, updates balance
5. Budget Agent confirms: "Logged $200 promo for Sushi Fusión 8. Balance: $140 remaining this week."

---

## KAM selector (demo authentication)

For the demo, authentication is replaced by a KAM selector dropdown in the dashboard header. This is not a security mechanism — it's a demo convenience that simulates the per-KAM experience.

**How it works:**

- The dashboard header contains a dropdown populated with all KAM names from the dataset (10 KAMs in current data)
- Selecting a KAM filters the entire dashboard: quadrant scatter, alert feed, portfolio summary, and chat context
- The selected KAM name is passed as a parameter to all API calls (`?kam=Ana Torres`)
- The chat agent receives the selected KAM as context and scopes all tool calls accordingly
- KAM selection persists in the browser's URL (`/dashboard?kam=ana-torres`) so demo links can be shared pre-scoped to a specific KAM

**API scoping:** Every backend endpoint accepts an optional `kam` parameter. When present, all tool calls filter to that KAM's portfolio. When absent (admin view), tools return data across all KAMs.

```
GET  /api/dashboard?kam=Ana Torres       → Portfolio overview for Ana Torres
POST /api/chat     { kam: "Ana Torres", message: "..." }  → Agent scoped to Ana's portfolio
GET  /api/dashboard                      → Admin view: all KAMs, all restaurants
```

**Frontend component:**

```
┌─────────────────────────────────────────────────────┐
│  🏢 Rappi KAM Intelligence    [Ana Torres ▼]  [⚙]  │
│                                                      │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────┐ │
│  │ 18 restaurants│  │ $168K revenue│  │ 2 alerts   │ │
│  └──────────────┘  └──────────────┘  └────────────┘ │
│                                                      │
│  Budget: $340 / $500 remaining ████████░░░░          │
│  ...                                                 │
└─────────────────────────────────────────────────────┘
```

---

## Evaluation framework

### Why evaluation is non-negotiable

The system generates RGM strategies, recovery plans, and budget recommendations that KAMs act on. A hallucinated recommendation — "reduce your menu to 5 items" when the restaurant has 80 SKUs driving variety-seeking behavior — doesn't just waste the KAM's time, it damages restaurant trust. Without an eval framework, every system prompt tweak is a blind deployment.

### Evaluation architecture

The eval framework runs on LangFuse and is structured around four dimensions, each with its own scoring rubric, golden dataset, and automation pipeline.

```
┌─────────────────────────────────────────────────────┐
│                  Eval Pipeline                        │
│                                                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐ │
│  │  Golden      │  │  Automated  │  │  Regression │ │
│  │  Dataset     │→ │  Eval Runs  │→ │  Detection  │ │
│  │  (30 cases)  │  │  (per PR)   │  │  (alerts)   │ │
│  └─────────────┘  └─────────────┘  └─────────────┘ │
│                                                      │
│  Dimensions:                                         │
│  1. Diagnostic accuracy                              │
│  2. Recommendation quality                           │
│  3. Budget correctness                               │
│  4. Communication quality                            │
└─────────────────────────────────────────────────────┘
```

### Dimension 1 — Diagnostic accuracy

Evaluates: Does the Diagnostic Agent correctly interpret the structured data it receives from tools?

| Metric | Scoring | Target |
|--------|---------|--------|
| Quadrant mention accuracy | Does the briefing correctly state each restaurant's quadrant? Binary per restaurant. | 100% (no tolerance — this is deterministic data) |
| Health score citation | When the agent mentions a health score, does it match the computed value (±1 point)? | 100% |
| Velocity alert completeness | Does the briefing mention all restaurants with active velocity alerts? | 100% |
| Signal attribution | When explaining why a restaurant is struggling, does the agent cite the correct dominant signal(s)? | ≥90% |
| Prioritization ordering | Are RESCUE restaurants presented before GROW in briefings? Are velocity-escalated restaurants flagged with correct time horizon? | 100% |

**Golden dataset:** 15 KAM briefing scenarios with known-correct outputs. Each scenario includes a specific restaurant portfolio, expected quadrant distribution, expected velocity alerts, and expected prioritization order. These are deterministic — the "correct" answer is computable from the data.

**Automation:** On every system prompt change, the eval pipeline runs all 15 scenarios through the Diagnostic Agent and scores each metric. Results are logged to LangFuse as a scored eval run. Any metric below target triggers a CI alert.

### Dimension 2 — Recommendation quality

Evaluates: Are the RGM Strategy Agent's recommendations actionable, contextually appropriate, and non-hallucinated?

| Metric | Scoring | Target |
|--------|---------|--------|
| Quadrant-strategy alignment | Does the recommendation match the restaurant's quadrant? (RESCUE gets recovery, not growth. GROW gets expansion, not recovery.) | 100% |
| Actionability | Does the recommendation specify a concrete action the KAM can take this week? (Not "improve operations" but "investigate cancellation causes — check tablet uptime and stock-out frequency") | ≥85% (LLM-as-judge) |
| Signal grounding | Does the recommendation reference specific signals from the restaurant's profile? | ≥90% |
| Hallucination detection | Does the recommendation invent data not present in the tool output? (e.g., citing a "34% cancellation rate" when the actual rate is 23%) | 0% hallucination rate |
| Playbook compliance | Does the recommendation draw from the correct playbook for the restaurant's quadrant? | ≥95% |
| Non-repetition | If the restaurant has intervention history, does the agent avoid repeating previously ineffective strategies? | ≥80% |

**Golden dataset:** 15 restaurant scenarios spanning all four quadrants plus velocity override cases:

- 3 RESCUE cases (varying severity: early deterioration, mid-collapse, terminal)
- 3 GROW cases (varying opportunity: ads-ready, menu-optimization-ready, expansion-ready)
- 3 TRIAGE cases (varying recovery viability: recoverable, borderline, disengage)
- 3 NURTURE cases (varying scale potential: high-potential, moderate, limited)
- 3 velocity override cases (GROW-to-RESCUE transition, both signals firing, single signal)

Each scenario includes the restaurant's full signal profile, quadrant, velocity status, and an expert-validated reference recommendation. The reference isn't a single "correct" answer — it's an annotated set of acceptable strategies with the reasoning behind each.

**Scoring method:** Hybrid. Quadrant-strategy alignment and hallucination detection are rule-based (automated). Actionability, signal grounding, and playbook compliance use LLM-as-judge scoring: a separate evaluation prompt that receives the restaurant profile, the agent's recommendation, and a rubric, then scores each dimension 1–5 with justification. The judge model should be a different provider than the agent model to avoid self-evaluation bias (e.g., if the agent runs on Gemini, the judge runs on Claude or GPT-4o).

### Dimension 3 — Budget correctness

Evaluates: Does the Budget Agent handle arithmetic, balance tracking, and escalation rules correctly?

| Metric | Scoring | Target |
|--------|---------|--------|
| Balance arithmetic | After a spend is logged, is the reported remaining balance correct? | 100% (zero tolerance) |
| Overspend prevention | Does the agent correctly reject or escalate when a spend exceeds remaining balance? | 100% |
| Category tagging | Is the intervention logged with the correct category and quadrant? | ≥95% |
| Escalation trigger | When spend exceeds weekly budget, does the agent generate an escalation with proper context? | 100% |
| ROI calculation | When reporting intervention ROI, does the math check out? | 100% |

**Golden dataset:** 10 budget interaction sequences, each a multi-turn conversation:

- Simple spend within budget
- Spend that exactly exhausts remaining budget
- Spend that exceeds budget (should trigger escalation)
- Multiple spends in sequence (running balance check)
- ROI query after interventions
- Week reset boundary case

**Automation:** Fully automated — all metrics are arithmetically verifiable. The pipeline runs the interaction sequence, captures the agent's reported numbers, and validates against computed expected values.

### Dimension 4 — Communication quality

Evaluates: Is the agent's output well-structured, concise, and appropriately toned?

| Metric | Scoring | Target |
|--------|---------|--------|
| Conciseness | Briefing length per restaurant ≤ 4 sentences. No filler, no dashboardese. | ≥90% |
| Structure compliance | Does the output follow the expected format (header → signal summary → recommendation → time horizon)? | ≥85% |
| Tone | Does the agent write like a sharp colleague, not a BI report? No passive voice, no "it is recommended that..." | ≥80% (LLM-as-judge) |
| Emoji/formatting consistency | Are quadrant indicators, severity markers, and budget displays formatted consistently? | ≥90% |

**Golden dataset:** Shares scenarios with Dimensions 1–2. Communication quality is scored as an overlay on every eval run.

### Eval pipeline execution

**Trigger:** Every change to a system prompt file, tool definition, or agent routing logic triggers a full eval run. The pipeline is also scheduled to run weekly against production traffic samples.

**Execution flow:**

1. Load golden datasets from `evals/` directory (version-controlled alongside system prompts)
2. For each scenario, instantiate the relevant agent with the updated prompt
3. Run the agent through the scenario's input sequence
4. Score each dimension using the appropriate method (rule-based, arithmetic, or LLM-as-judge)
5. Log all scores to LangFuse as a scored eval run, tagged with the commit hash
6. Compare against the previous run's scores
7. If any dimension drops below target or regresses by >5 points, flag for review

**Regression detection:** LangFuse stores eval scores as time series. The pipeline compares each run to the trailing 5-run average. A regression alert fires when:

- Any 100%-target metric drops below 100%
- Any other metric drops more than 5 percentage points from its trailing average
- The LLM-as-judge confidence interval widens (indicating the prompt change introduced inconsistency)

---

## Observability with LangFuse

Every interaction across all three agents is traced through LangFuse, providing:

- **Request tracing**: Full conversation history, router classification, agent delegation, tool calls, and agent reasoning for each interaction. Each trace captures which agent handled the request, which tools were invoked, the structured data returned, and the final response generated.
- **Token and cost monitoring**: Input/output token counts per request, broken down by agent and provider. This is critical with the multi-agent architecture: a briefing request that touches both Diagnostic and RGM agents will show token usage for each separately, enabling targeted optimization.
- **Latency tracking**: End-to-end response time broken down by: router classification, diagnostic engine computation, LLM API call (per agent), and streaming delivery. With multiple agents, the pipeline latency is the sum of sequential agent calls — monitoring identifies when to parallelize.
- **Tool usage analytics**: Which tools are called most frequently, which combinations appear together, and which queries trigger the most tool calls. Reveals patterns in KAM behavior and agent efficiency.
- **Cross-provider comparison**: When running agents on different providers (e.g., Diagnostic on Gemini, RGM on OpenAI), LangFuse tracks cost, latency, and eval scores per provider, enabling data-driven provider selection.
- **Evaluation integration**: Eval pipeline scores are stored as LangFuse scores linked to traces, creating a single dashboard where cost, latency, and quality metrics live side by side.

---

## Data flow: from CSV to KAM briefing

1. **Startup**: FastAPI loads `dataset.csv` into a pandas DataFrame. The diagnostic engine computes health scores, revenue, quadrants, and velocity flags for all 205 restaurants. Budget state is loaded from `interventions.csv` (or initialized empty). This takes <100ms.

2. **Dashboard load**: Next.js calls `GET /api/dashboard?kam={name}`. FastAPI invokes `get_portfolio_overview()` and returns structured JSON. The dashboard renders the quadrant scatter, alert feed, portfolio summary, and budget balance — no LLM call needed for the initial view.

3. **Briefing request**: KAM clicks "Generate Briefing" or types a question in the chat panel. Next.js sends to `POST /api/chat`. FastAPI passes the message to the Router Agent, which classifies intent and delegates to the appropriate specialist agent. The specialist decides which tools to call, receives structured diagnostic data, and generates a response. Response is streamed via SSE.

4. **Follow-up**: The KAM asks "tell me more about Burger Clásico" or "what growth strategy would you recommend for Sushi Fusión 8?". The Router detects multi-intent, calls the Diagnostic Agent for data, then passes context to the RGM Strategy Agent for the recommendation.

5. **Budget interaction**: The KAM says "log $150 on Sushi Fusión 8 promo". The Router delegates to the Budget Agent, which validates the balance, logs the intervention, and confirms with the updated balance.

6. **Observability**: Every step (2–5) is traced in LangFuse. The dashboard view (step 2) logs only the diagnostic engine call. Steps 3–5 log the full agent trace: router classification, agent delegation, tool calls, structured results, generated response, token usage, and latency. Budget operations additionally log the intervention to `interventions.csv`.
