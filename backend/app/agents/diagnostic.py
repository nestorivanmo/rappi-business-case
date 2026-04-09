import os

from app.agents.base import BaseAgent
from app.agents.tools import DIAGNOSTIC_TOOLS
from app.llm.types import ToolDefinition


def _load_prompt() -> str:
    path = os.path.join(os.path.dirname(__file__), "prompts", "diagnostic.txt")
    with open(path) as f:
        return f.read()


class DiagnosticAgent(BaseAgent):
    def __init__(self, provider, engine, kam_name: str):
        system_prompt = _load_prompt()
        tool_handlers = {
            "get_portfolio_overview": lambda **kw: engine.get_portfolio_overview(**kw),
            "get_kam_briefing": lambda **kw: engine.get_kam_briefing(**kw),
            "get_velocity_alerts": lambda **kw: engine.get_velocity_alerts(**kw),
            "get_revenue_at_risk": lambda **kw: engine.get_revenue_at_risk(**kw),
            "get_restaurant_detail": lambda **kw: engine.get_restaurant_detail(**kw),
            "get_restaurants_by_quadrant": lambda **kw: (
                engine.get_restaurants_by_quadrant(**kw)
            ),
            "compare_restaurants": lambda **kw: engine.compare_restaurants(**kw),
            "get_city_breakdown": lambda **kw: engine.get_city_breakdown(**kw),
            "get_vertical_breakdown": lambda **kw: engine.get_vertical_breakdown(**kw),
            "search_restaurants": lambda **kw: engine.search_restaurants(**kw),
        }
        super().__init__(
            "diagnostic", provider, system_prompt, DIAGNOSTIC_TOOLS, tool_handlers
        )
