import pandas as pd

SIGNAL_CONFIG = {
    "delta_rating": {"min": -0.89, "max": 0.30, "weight": 0.25, "invert": True},
    "tasa_cancelacion_pct": {"min": 1.0, "max": 41.6, "weight": 0.20, "invert": False},
    "quejas_7d": {"min": 0, "max": 45, "weight": 0.20, "invert": False},
    "rating_actual": {"min": 1.3, "max": 5.0, "weight": 0.15, "invert": True},
    "tiempo_entrega_avg_min": {"min": 18, "max": 95, "weight": 0.10, "invert": False},
    "var_ordenes_pct": {"min": -42.9, "max": 19.9, "weight": 0.10, "invert": True},
}


def normalize_signal(series: pd.Series, min_val: float, max_val: float, invert: bool) -> pd.Series:
    """Normalize a signal to 0-100 risk scale. Higher = more risk."""
    clipped = series.clip(lower=min_val, upper=max_val)
    if invert:
        # Higher raw value = healthier → low risk score
        return (max_val - clipped) / (max_val - min_val) * 100
    else:
        # Higher raw value = worse → high risk score
        return (clipped - min_val) / (max_val - min_val) * 100


def compute_health_scores(df: pd.DataFrame) -> pd.Series:
    """Compute composite health score (0-100, higher = healthier) for each restaurant."""
    risk_score = pd.Series(0.0, index=df.index)

    for signal, cfg in SIGNAL_CONFIG.items():
        normalized = normalize_signal(df[signal], cfg["min"], cfg["max"], cfg["invert"])
        df[f"norm_{signal}"] = normalized
        risk_score += cfg["weight"] * normalized

    return (100 - risk_score).round(1)
