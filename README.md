# Proactive Risk Detection Agent for Rappi KAMs

**Rappi AI Builder Challenge — Case 02: Operational Intelligence Agent**

## What it does

Multi-agent system that monitors restaurant health across a KAM's portfolio, classifies each into **GROW / RESCUE / NURTURE / TRIAGE** quadrants (Health x Revenue), and delivers prioritized weekly briefings with actionable recommendations and velocity alerts.

## Architecture

**Frontend:** Next.js 14 + Tailwind (Vercel) | **Backend:** FastAPI (Railway) | **LLM:** Gemini 2.5 Flash (swappable) | **Scoring:** pandas (deterministic) | **Observability:** LangFuse

Three specialized agents behind a router: **Diagnostic** (scoring, alerts), **RGM Strategy** (recommendations per quadrant), **Budget** (KAM discretionary spend + ROI).

## Key decisions

- **Deterministic scoring, LLM for strategy only** — health scores are pure math, auditable and reproducible
- **Provider-agnostic** — thin adapter layer, swap LLM vendors via env var
- **Two-axis classification** over simple traffic light — captures both risk and growth opportunity

## Repo structure

```
1-data-exploration/           # Dataset (205 restaurants), notebook, plots
2-business-case.md            # Ecosystem analysis, scoring logic, strategic impact
3-technical-implementation.md # Architecture, agents, eval framework
```
