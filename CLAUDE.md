# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

Proactive Risk Detection Agent for Rappi KAMs (Rappi AI Builder Challenge — Case 02). Multi-agent system that monitors restaurant health across a KAM's portfolio, classifies each into GROW/RESCUE/NURTURE/TRIAGE quadrants (Health x Value), and delivers prioritized weekly briefings with actionable recommendations.

## Repo structure

- `1-data-exploration/` — Dataset (205 restaurants), Jupyter notebook, plot assets
- `2-business-case.md` — Ecosystem analysis, scoring logic, quadrant classification
- `3-technical-implementation.md` — Architecture spec: multi-agent design, provider abstraction, eval framework
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

- **Deterministic scoring, LLM for strategy only.** Health scores, quadrants, and velocity overrides computed by pandas. Agents consume structured results.
- **Provider-agnostic LLM layer.** `LLMProvider` protocol with Gemini/OpenAI/Anthropic adapters. Configurable per agent via env vars.
- **Three specialized agents behind a router:** Diagnostic, RGM Strategy, Budget. Router classifies intent and delegates.
- **Two-axis classification (Health x Value)** via Pareto threshold on revenue. Health threshold = 60, budget = $10,000 MXN/week per KAM.

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
pytest tests/ -v
```

## Running evals (requires LLM API key)

```bash
python evals/run_evals.py --dimension diagnostic
python evals/run_evals.py --all
```

## Environment

- Python 3.14 venv in `.venv/` (Docker uses 3.12)
- API keys via `.env` file (see `.env.example`)
- Backend dependencies in `backend/requirements.txt`
