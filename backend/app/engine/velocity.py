import pandas as pd

DELTA_RATING_THRESHOLD = -0.4
VAR_ORDENES_THRESHOLD = -20.0


def compute_velocity_overrides(df: pd.DataFrame) -> pd.DataFrame:
    """Add velocity_flag and escalation_level columns."""
    delta_rating_alert = df["delta_rating"] < DELTA_RATING_THRESHOLD
    var_ordenes_alert = df["var_ordenes_pct"] < VAR_ORDENES_THRESHOLD

    both = delta_rating_alert & var_ordenes_alert
    either = delta_rating_alert | var_ordenes_alert

    df["velocity_flag"] = either
    df["escalation_level"] = "none"
    df.loc[either, "escalation_level"] = "5_day"
    df.loc[both, "escalation_level"] = "immediate"

    return df
