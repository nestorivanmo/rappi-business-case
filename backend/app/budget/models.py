from datetime import datetime

from pydantic import BaseModel


class Intervention(BaseModel):
    id: str
    kam_name: str
    restaurant_id: str
    timestamp: datetime
    amount_mxn: float
    category: str  # "promo" | "credit" | "ops_support" | "growth_investment"
    quadrant_at_time: str
    health_score_at_time: float
    description: str
    revenue_7d_before: float
    revenue_7d_after: float | None = None


class KAMBudget(BaseModel):
    kam_name: str
    weekly_allocation_mxn: float
    current_week_spent: float
    reset_day: str = "monday"
    interventions: list[Intervention] = []


class EscalationRequest(BaseModel):
    kam_name: str
    restaurant_id: str
    amount_mxn: float
    justification: str
    diagnostic_context: dict
