import pandas as pd

from app.engine.scoring import compute_health_scores
from app.engine.classification import compute_revenue, compute_pareto_threshold, assign_quadrants
from app.engine.velocity import compute_velocity_overrides

REQUIRED_COLUMNS = [
    "restaurant_id", "nombre", "ciudad", "vertical",
    "rating_actual", "rating_prom_30d", "delta_rating",
    "tasa_cancelacion_pct", "tiempo_entrega_avg_min",
    "ordenes_7d", "ordenes_7d_anterior", "var_ordenes_pct",
    "quejas_7d", "nps_score", "valor_ticket_prom_mxn",
    "kam_asignado", "activo_desde", "semaforo_riesgo",
]


def load_dataset(path: str, health_threshold: float = 60.0) -> pd.DataFrame:
    """Load CSV and compute all derived columns."""
    df = pd.read_csv(path)

    missing = set(REQUIRED_COLUMNS) - set(df.columns)
    if missing:
        raise ValueError(f"Dataset missing required columns: {missing}")

    # Compute derived columns
    df["weekly_revenue"] = compute_revenue(df)
    df["health_score"] = compute_health_scores(df)

    pareto_threshold = compute_pareto_threshold(df)
    df["quadrant"] = assign_quadrants(df, health_threshold, pareto_threshold)

    df = compute_velocity_overrides(df)

    return df
