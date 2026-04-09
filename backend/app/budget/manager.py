import uuid
from datetime import datetime, date

from app.budget.models import Intervention
from app.budget import store


class BudgetManager:
    def __init__(self, weekly_allocation: float, interventions_path: str, engine):
        self.weekly_allocation = weekly_allocation
        self.interventions_path = interventions_path
        self.engine = engine
        self.interventions = store.load_interventions(interventions_path)

    def _current_week_interventions(self, kam_name: str) -> list[Intervention]:
        today = date.today()
        # ISO week: Monday = 1
        week_start = today - __import__("datetime").timedelta(days=today.weekday())
        return [
            i for i in self.interventions
            if i.kam_name == kam_name and i.timestamp.date() >= week_start
        ]

    def get_budget_balance(self, kam_name: str) -> dict:
        week_interventions = self._current_week_interventions(kam_name)
        total_spent = sum(i.amount_mxn for i in week_interventions)
        spend_by_category: dict[str, float] = {}
        for i in week_interventions:
            spend_by_category[i.category] = spend_by_category.get(i.category, 0) + i.amount_mxn

        return {
            "kam_name": kam_name,
            "remaining": round(self.weekly_allocation - total_spent, 2),
            "total_allocated": self.weekly_allocation,
            "total_spent": round(total_spent, 2),
            "spend_by_category": spend_by_category,
        }

    def log_intervention(
        self,
        kam_name: str,
        restaurant_id: str,
        amount: float,
        category: str,
        description: str,
    ) -> dict:
        balance = self.get_budget_balance(kam_name)
        if amount > balance["remaining"]:
            return {
                "error": "Insufficient budget",
                "remaining": balance["remaining"],
                "requested": amount,
                "suggestion": "Use request_escalation for amounts exceeding your weekly budget.",
            }

        # Look up restaurant context
        detail = self.engine.get_restaurant_detail(restaurant_id)
        if "error" in detail:
            return detail

        intervention = Intervention(
            id=str(uuid.uuid4()),
            kam_name=kam_name,
            restaurant_id=restaurant_id,
            timestamp=datetime.now(),
            amount_mxn=amount,
            category=category,
            quadrant_at_time=detail["quadrant"],
            health_score_at_time=detail["health_score"],
            description=description,
            revenue_7d_before=detail["weekly_revenue"],
        )

        self.interventions.append(intervention)
        store.save_intervention(intervention, self.interventions_path)

        updated_balance = self.get_budget_balance(kam_name)
        return {
            "status": "logged",
            "intervention_id": intervention.id,
            "restaurant": detail["nombre"],
            "amount": amount,
            "category": category,
            "balance": updated_balance,
        }

    def get_intervention_history(
        self, restaurant_id: str | None = None, kam_name: str | None = None
    ) -> list[dict]:
        filtered = self.interventions
        if restaurant_id:
            filtered = [i for i in filtered if i.restaurant_id == restaurant_id]
        if kam_name:
            filtered = [i for i in filtered if i.kam_name == kam_name]
        return [i.model_dump() for i in filtered]

    def get_budget_roi(self, kam_name: str | None = None, period: str | None = None) -> dict:
        filtered = self.interventions
        if kam_name:
            filtered = [i for i in filtered if i.kam_name == kam_name]

        total_invested = sum(i.amount_mxn for i in filtered)
        with_roi = [i for i in filtered if i.revenue_7d_after is not None]
        total_revenue_delta = sum(
            (i.revenue_7d_after or 0) - i.revenue_7d_before for i in with_roi
        )

        return {
            "total_invested": round(total_invested, 2),
            "interventions_count": len(filtered),
            "interventions_with_roi_data": len(with_roi),
            "total_revenue_delta": round(total_revenue_delta, 2),
            "roi_ratio": round(total_revenue_delta / total_invested, 2) if total_invested > 0 else 0,
        }

    def request_escalation(
        self, kam_name: str, restaurant_id: str, amount: float, justification: str
    ) -> dict:
        detail = self.engine.get_restaurant_detail(restaurant_id)
        balance = self.get_budget_balance(kam_name)

        return {
            "status": "escalation_requested",
            "kam_name": kam_name,
            "restaurant": detail.get("nombre", restaurant_id),
            "amount_requested": amount,
            "current_balance": balance["remaining"],
            "overage": round(amount - balance["remaining"], 2),
            "justification": justification,
            "diagnostic_context": {
                "health_score": detail.get("health_score"),
                "quadrant": detail.get("quadrant"),
                "dominant_risk_signals": detail.get("dominant_risk_signals"),
                "weekly_revenue": detail.get("weekly_revenue"),
            },
        }
