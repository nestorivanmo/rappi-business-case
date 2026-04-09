from fastapi import APIRouter, Request
from pydantic import BaseModel

router = APIRouter(prefix="/api")


class LogInterventionRequest(BaseModel):
    kam_name: str
    restaurant_id: str
    amount_mxn: float
    category: str
    description: str


@router.get("/budget")
async def get_balance(request: Request, kam: str):
    budget_manager = request.app.state.budget_manager
    return budget_manager.get_budget_balance(kam)


@router.post("/budget/interventions")
async def log_spend(request: Request, body: LogInterventionRequest):
    budget_manager = request.app.state.budget_manager
    return budget_manager.log_intervention(
        kam_name=body.kam_name,
        restaurant_id=body.restaurant_id,
        amount=body.amount_mxn,
        category=body.category,
        description=body.description,
    )


@router.get("/budget/interventions")
async def get_history(
    request: Request, kam: str | None = None, restaurant_id: str | None = None
):
    budget_manager = request.app.state.budget_manager
    return budget_manager.get_intervention_history(
        restaurant_id=restaurant_id, kam_name=kam
    )
