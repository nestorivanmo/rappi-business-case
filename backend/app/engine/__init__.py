from app.engine.loader import load_dataset
from app.engine import scoring, classification, velocity, queries


class DiagnosticEngine:
    def __init__(self, data_path: str, health_threshold: float = 60.0):
        self.df = load_dataset(data_path, health_threshold)
        self.health_threshold = health_threshold
        self.pareto_threshold = classification.compute_pareto_threshold(self.df)

    def get_portfolio_overview(self, kam_name: str | None = None) -> dict:
        return queries.get_portfolio_overview(self.df, kam_name)

    def get_kam_briefing(self, kam_name: str) -> list[dict]:
        return queries.get_kam_briefing(self.df, kam_name)

    def get_velocity_alerts(self, kam_name: str | None = None) -> list[dict]:
        return queries.get_velocity_alerts(self.df, kam_name)

    def get_revenue_at_risk(self, kam_name: str | None = None) -> dict:
        return queries.get_revenue_at_risk(self.df, kam_name)

    def get_restaurant_detail(self, restaurant_id: str) -> dict:
        return queries.get_restaurant_detail(self.df, restaurant_id)

    def get_restaurants_by_quadrant(self, quadrant: str, kam_name: str | None = None) -> list[dict]:
        return queries.get_restaurants_by_quadrant(self.df, quadrant, kam_name)

    def compare_restaurants(self, restaurant_ids: list[str]) -> list[dict]:
        return queries.compare_restaurants(self.df, restaurant_ids)

    def get_city_breakdown(self, kam_name: str | None = None) -> list[dict]:
        return queries.get_city_breakdown(self.df, kam_name)

    def get_vertical_breakdown(self, kam_name: str | None = None) -> list[dict]:
        return queries.get_vertical_breakdown(self.df, kam_name)

    def search_restaurants(self, query: str) -> list[dict]:
        return queries.search_restaurants(self.df, query)
