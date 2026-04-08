# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

Proactive Risk Detection Agent for Rappi KAMs (Rappi AI Builder Challenge — Case 02). Multi-agent system that monitors restaurant health across a KAM's portfolio, classifies each into GROW/RESCUE/NURTURE/TRIAGE quadrants (Health x Value), and delivers prioritized weekly briefings with actionable recommendations.

**Current state:** Documentation and data exploration phase. No application code yet — the repo contains the business case, technical architecture spec, dataset, and exploratory notebook.

## Repo structure

- `1-data-exploration/` — Dataset (205 restaurants, `dataset.csv`), Jupyter notebook (`exploration.ipynb`), plot assets
- `2-business-case.md` — Ecosystem analysis, scoring logic, quadrant classification, strategic impact
- `3-technical-implementation.md` — Architecture spec: multi-agent design, provider abstraction, eval framework
- `Rappi AI Builder Challenge.pdf` — Original challenge brief

## Planned tech stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 14 (App Router) + Tailwind + shadcn/ui, deployed on Vercel |
| Backend | Python FastAPI, deployed on Railway |
| LLM | Gemini 2.5 Flash via `google-genai` SDK (swappable via provider abstraction) |
| Scoring | pandas/numpy — deterministic, no LLM |
| Observability | LangFuse |

## Key architecture decisions

- **Deterministic scoring, LLM for strategy only.** Health scores, quadrant assignments, and velocity overrides are computed by pandas. Agents consume structured results and generate natural-language output.
- **Provider-agnostic LLM layer.** Thin adapter (`LLMProvider` protocol) wraps provider SDKs. Agent code never imports a provider SDK directly. Provider selection via env vars, configurable per agent.
- **Three specialized agents behind a router:** Diagnostic (scoring/alerts), RGM Strategy (recommendations per quadrant), Budget (KAM discretionary spend + ROI). Router classifies intent and delegates.
- **Two-axis classification (Health x Value)** over simple traffic light — captures both risk and growth opportunity via Pareto threshold on revenue.

## Scoring model

6 risk signals with weights: `delta_rating` (0.25), `tasa_cancelacion_pct` (0.20), `quejas_7d` (0.20), `rating_actual` (0.15), `tiempo_entrega_avg_min` (0.10), `var_ordenes_pct` (0.10). Health Score = 100 - weighted risk score. Revenue = `ordenes_7d * valor_ticket_prom_mxn`.

## Running the notebook

```bash
source .venv/bin/activate
jupyter notebook 1-data-exploration/exploration.ipynb
```

## Environment

- Python 3.14 virtual environment in `.venv/`
- No `requirements.txt` yet — dependencies are notebook-only (pandas, matplotlib, scipy, seaborn)
