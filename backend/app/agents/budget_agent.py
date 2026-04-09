import os

from app.agents.base import BaseAgent
from app.agents.tools import BUDGET_TOOLS


def _load_prompt() -> str:
    path = os.path.join(os.path.dirname(__file__), "prompts", "budget.txt")
    with open(path) as f:
        return f.read()


class BudgetAgentImpl(BaseAgent):
    def __init__(self, provider, budget_manager, kam_name: str):
        system_prompt = _load_prompt()
        tool_handlers = {
            "get_budget_balance": lambda **kw: budget_manager.get_budget_balance(**kw),
            "log_intervention": lambda **kw: budget_manager.log_intervention(**kw),
            "get_intervention_history": lambda **kw: (
                budget_manager.get_intervention_history(**kw)
            ),
            "get_budget_roi": lambda **kw: budget_manager.get_budget_roi(**kw),
            "request_escalation": lambda **kw: budget_manager.request_escalation(**kw),
        }
        super().__init__("budget", provider, system_prompt, BUDGET_TOOLS, tool_handlers)
