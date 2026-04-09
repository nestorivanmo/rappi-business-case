import pandas as pd


def compute_revenue(df: pd.DataFrame) -> pd.Series:
    """Weekly revenue = ordenes_7d * valor_ticket_prom_mxn."""
    return (df["ordenes_7d"] * df["valor_ticket_prom_mxn"]).round(2)


def compute_pareto_threshold(df: pd.DataFrame) -> float:
    """Find the revenue threshold where top restaurants account for ~80% of total GMV."""
    sorted_rev = df["weekly_revenue"].sort_values(ascending=False)
    cumulative = sorted_rev.cumsum()
    total = sorted_rev.sum()
    # Find the revenue of the last restaurant included in the top 80%
    mask = cumulative <= total * 0.80
    if mask.any():
        threshold = sorted_rev[mask].iloc[-1]
    else:
        threshold = sorted_rev.iloc[0]
    return float(threshold)


def assign_quadrants(
    df: pd.DataFrame, health_threshold: float, pareto_threshold: float
) -> pd.Series:
    """Classify each restaurant into GROW/RESCUE/NURTURE/TRIAGE."""

    def _classify(row: pd.Series) -> str:
        high_health = row["health_score"] >= health_threshold
        high_value = row["weekly_revenue"] >= pareto_threshold
        if high_health and high_value:
            return "GROW"
        elif not high_health and high_value:
            return "RESCUE"
        elif high_health and not high_value:
            return "NURTURE"
        else:
            return "TRIAGE"

    return df.apply(_classify, axis=1)
