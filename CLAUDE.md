# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

Proactive Risk Detection Agent for Rappi KAMs (Rappi AI Builder Challenge — Case 02). Multi-agent system that monitors restaurant health across a KAM's portfolio, classifies each into GROW/RESCUE/NURTURE/TRIAGE quadrants (Health x Value), and delivers prioritized weekly briefings with actionable recommendations.

## Repo structure

- `data-exploration/` — Dataset (205 restaurants), Jupyter notebook, plot assets
- `docs/01-business-case.md` — Ecosystem analysis, scoring logic, quadrant classification
- `docs/02-technical-implementation.md` — Architecture spec: multi-agent design, provider abstraction, eval framework
- `docs/03-agent-runtime.md` — Code-level runtime walkthrough of the multi-agent system
- `docs/challenge.pdf` — Original Rappi AI Builder Challenge brief
- `backend/` — Python FastAPI backend (diagnostic engine, agents, LLM abstraction, budget management)
- `frontend/` — Next.js 14 dashboard with chat panel
- `evals/` — Evaluation framework (golden datasets, scorers)
- `docker-compose.yml` — Local development with both services

## Tech stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 14 (App Router) + Tailwind + shadcn/ui |
| Backend | Python FastAPI |
| LLM | Gemini 2.5 Flash via `google-genai` SDK (swappable) |
| Scoring | pandas/numpy — deterministic, no LLM |
| Observability | LangFuse (opt-in) |
| Deployment | Docker + Vercel (frontend) + Railway (backend) |

## Key architecture decisions

- **Deterministic scoring, LLM for strategy only.** Health scores, quadrants, and velocity overrides computed by pandas in `backend/app/engine/`. Agents consume structured results via tool calls, never recompute metrics.
- **Provider-agnostic LLM layer.** `LLMProvider` protocol (`backend/app/llm/protocol.py`) with Gemini/OpenAI/Anthropic adapters. `get_agent_provider()` in `llm/factory.py` resolves per-agent overrides, falling back to `llm_provider`/`llm_model` defaults.
- **Router → 3 specialized sub-agents.** `RouterAgent` (`backend/app/agents/router.py`) owns its own LLM + tool handlers that delegate to `DiagnosticAgent`, `RGMStrategyAgent`, `BudgetAgentImpl`. Each agent's system prompt lives in `backend/app/agents/prompts/`.
- **Two-axis classification (Health x Value)** via Pareto threshold on revenue. Health threshold = 60, budget = $10,000 MXN/week per KAM.
- **FastAPI lifespan bootstrap.** `DiagnosticEngine` and `BudgetManager` are constructed once in `main.py` lifespan and attached to `app.state`; route handlers read them via `request.app.state`.

## Scoring model

6 signals: `delta_rating` (0.25), `tasa_cancelacion_pct` (0.20), `quejas_7d` (0.20), `rating_actual` (0.15), `tiempo_entrega_avg_min` (0.10), `var_ordenes_pct` (0.10). Health Score = 100 - weighted risk score.

## Running locally

```bash
# With Docker (recommended)
cp .env.example .env  # Add your API keys
docker compose up --build

# Without Docker
source .venv/bin/activate
cd backend && pip install -r requirements.txt
uvicorn app.main:app --reload  # Backend on :8000

cd frontend && npm install && npm run dev  # Frontend on :3000
```

## Running tests

```bash
cd backend && source ../.venv/bin/activate
pytest tests/ -v                                   # full suite
pytest tests/test_scoring.py -v                    # one file
pytest tests/test_scoring.py::test_name -v         # one test
```

Frontend lint: `cd frontend && npm run lint` (ESLint 9 flat config via `eslint.config.mjs`).

## Running evals (requires LLM API key)

```bash
python evals/run_evals.py --dimension diagnostic
python evals/run_evals.py --all
```

## Environment

- Python 3.14 venv in `.venv/` (Docker uses 3.12)
- API keys via `.env` file (see `.env.example`); `Settings` reads both `.env` and `../.env`
- Backend dependencies in `backend/requirements.txt`
- **Per-agent LLM overrides** via `{diagnostic,rgm,budget}_agent_{provider,model}` env vars; otherwise all agents share `llm_provider` / `llm_model`
- **Data loading quirk:** the canonical dataset lives at `data-exploration/dataset.csv`. Docker mounts it read-only into `backend/data/dataset.csv` (see `docker-compose.yml`). When running the backend outside Docker, ensure `backend/data/dataset.csv` exists or set `data_path` accordingly.

## Frontend caveat

`frontend/AGENTS.md` warns: **this is not the Next.js in your training data.** The frontend runs Next.js 16.2.2 + React 19.2 with breaking API/convention changes. Before writing frontend code, consult `frontend/node_modules/next/dist/docs/` for the current guide rather than relying on memory, and heed deprecation notices.
