"""
Evaluation pipeline runner for Rappi KAM Intelligence agents.

Usage:
    python evals/run_evals.py --dimension diagnostic --provider gemini
    python evals/run_evals.py --all
"""

import argparse
import asyncio
import json
import os
import sys

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.config import Settings
from app.engine import DiagnosticEngine
from app.budget.manager import BudgetManager
from app.agents.router import RouterAgent
from app.llm.types import Message


def load_golden_dataset(name: str) -> list[dict]:
    path = os.path.join(os.path.dirname(__file__), "datasets", f"{name}_golden.json")
    with open(path) as f:
        return json.load(f)


async def run_diagnostic_eval(settings: Settings, engine: DiagnosticEngine, budget_manager: BudgetManager):
    """Run diagnostic evaluation scenarios."""
    dataset = load_golden_dataset("diagnostic")
    results = []

    for scenario in dataset:
        kam = scenario.get("kam_name") or "Ana Torres"
        print(f"  Running {scenario['id']}: {scenario['description']}...")

        try:
            router = RouterAgent(settings, engine, budget_manager, kam)
            response = await router.chat([
                Message(role="user", content=scenario["input_message"])
            ])

            results.append({
                "id": scenario["id"],
                "status": "completed",
                "response_length": len(response),
                "response_preview": response[:200],
            })
        except Exception as e:
            results.append({
                "id": scenario["id"],
                "status": "error",
                "error": str(e),
            })

    return results


async def run_recommendation_eval(settings: Settings, engine: DiagnosticEngine, budget_manager: BudgetManager):
    """Run recommendation evaluation scenarios."""
    dataset = load_golden_dataset("recommendation")
    results = []

    for scenario in dataset:
        print(f"  Running {scenario['id']}: {scenario['description']}...")

        try:
            router = RouterAgent(settings, engine, budget_manager, "Ana Torres")
            response = await router.chat([
                Message(role="user", content=scenario["input_message"])
            ])

            results.append({
                "id": scenario["id"],
                "status": "completed",
                "response_length": len(response),
                "response_preview": response[:200],
            })
        except Exception as e:
            results.append({
                "id": scenario["id"],
                "status": "error",
                "error": str(e),
            })

    return results


async def run_budget_eval(settings: Settings, engine: DiagnosticEngine):
    """Run budget evaluation scenarios."""
    dataset = load_golden_dataset("budget")
    results = []

    for scenario in dataset:
        print(f"  Running {scenario['id']}: {scenario['description']}...")
        kam = scenario["kam_name"]

        # Fresh budget manager for each scenario
        budget_manager = BudgetManager(10000.0, "/tmp/eval_interventions.csv", engine)

        try:
            for step in scenario["steps"]:
                router = RouterAgent(settings, engine, budget_manager, kam)
                response = await router.chat([
                    Message(role="user", content=step["input"])
                ])

            results.append({
                "id": scenario["id"],
                "status": "completed",
                "steps_completed": len(scenario["steps"]),
            })
        except Exception as e:
            results.append({
                "id": scenario["id"],
                "status": "error",
                "error": str(e),
            })

        # Clean up temp file
        if os.path.exists("/tmp/eval_interventions.csv"):
            os.remove("/tmp/eval_interventions.csv")

    return results


async def main():
    parser = argparse.ArgumentParser(description="Run eval pipeline")
    parser.add_argument("--dimension", choices=["diagnostic", "recommendation", "budget"])
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--provider", default="gemini")
    args = parser.parse_args()

    if not args.dimension and not args.all:
        parser.print_help()
        return

    settings = Settings()
    engine = DiagnosticEngine(
        data_path=os.path.join("backend", "data", "dataset.csv"),
        health_threshold=60.0,
    )
    budget_manager = BudgetManager(10000.0, "/tmp/eval_interventions.csv", engine)

    dimensions = []
    if args.all:
        dimensions = ["diagnostic", "recommendation", "budget"]
    else:
        dimensions = [args.dimension]

    all_results = {}

    for dim in dimensions:
        print(f"\n{'='*60}")
        print(f"Running {dim} evaluation...")
        print(f"{'='*60}")

        if dim == "diagnostic":
            results = await run_diagnostic_eval(settings, engine, budget_manager)
        elif dim == "recommendation":
            results = await run_recommendation_eval(settings, engine, budget_manager)
        elif dim == "budget":
            results = await run_budget_eval(settings, engine)

        all_results[dim] = results

        completed = sum(1 for r in results if r["status"] == "completed")
        errors = sum(1 for r in results if r["status"] == "error")
        print(f"\nResults: {completed} completed, {errors} errors out of {len(results)} scenarios")

    # Write results
    output_path = "/tmp/eval_results.json"
    with open(output_path, "w") as f:
        json.dump(all_results, f, indent=2)
    print(f"\nResults written to {output_path}")


if __name__ == "__main__":
    asyncio.run(main())
