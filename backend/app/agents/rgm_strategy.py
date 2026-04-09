import os

from app.agents.base import BaseAgent
from app.agents.tools import RGM_TOOLS


def _load_prompt() -> str:
    path = os.path.join(os.path.dirname(__file__), "prompts", "rgm_strategy.txt")
    with open(path) as f:
        return f.read()


class RGMStrategyAgent(BaseAgent):
    def __init__(self, provider, engine, budget_manager, kam_name: str):
        system_prompt = _load_prompt()
        tool_handlers = {
            "get_restaurant_detail": lambda **kw: engine.get_restaurant_detail(**kw),
            "get_restaurants_by_quadrant": lambda **kw: engine.get_restaurants_by_quadrant(**kw),
            "get_intervention_history": lambda **kw: budget_manager.get_intervention_history(**kw),
        }
        super().__init__("rgm_strategy", provider, system_prompt, RGM_TOOLS, tool_handlers)
