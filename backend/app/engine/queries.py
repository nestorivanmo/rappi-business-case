import pandas as pd

from app.engine.scoring import SIGNAL_CONFIG


def _filter_kam(df: pd.DataFrame, kam_name: str | None) -> pd.DataFrame:
    if kam_name:
        return df[df["kam_asignado"] == kam_name]
    return df


def _restaurant_summary(row: pd.Series) -> dict:
    """Compact restaurant representation for lists."""
    # Determine dominant risk signals (top 2 by normalized contribution)
    signal_contributions = {}
    for signal, cfg in SIGNAL_CONFIG.items():
        norm_col = f"norm_{signal}"
        if norm_col in row.index:
            signal_contributions[signal] = cfg["weight"] * row[norm_col]

    sorted_signals = sorted(signal_contributions.items(), key=lambda x: x[1], reverse=True)
    dominant = [s[0] for s in sorted_signals[:2]]

    time_horizon = "2 weeks"
    if row.get("escalation_level") == "immediate":
        time_horizon = "today"
    elif row.get("escalation_level") == "5_day":
        time_horizon = "5 days"

    return {
        "restaurant_id": row["restaurant_id"],
        "nombre": row["nombre"],
        "ciudad": row["ciudad"],
        "vertical": row["vertical"],
        "health_score": float(row["health_score"]),
        "quadrant": row["quadrant"],
        "weekly_revenue": float(row["weekly_revenue"]),
        "escalation_level": row.get("escalation_level", "none"),
        "time_horizon": time_horizon,
        "dominant_risk_signals": dominant,
        "velocity_flag": bool(row.get("velocity_flag", False)),
        "rating_actual": float(row.get("rating_actual", 0)),
        "delta_rating": float(row.get("delta_rating", 0)),
        "valor_ticket_prom_mxn": float(row.get("valor_ticket_prom_mxn", 0)),
        "tasa_cancelacion_pct": float(row.get("tasa_cancelacion_pct", 0)),
        "tiempo_entrega_avg_min": float(row.get("tiempo_entrega_avg_min", 0)),
    }


def _restaurant_detail(row: pd.Series) -> dict:
    """Full restaurant profile."""
    summary = _restaurant_summary(row)
    signals_normalized = {}
    for signal in SIGNAL_CONFIG:
        norm_col = f"norm_{signal}"
        if norm_col in row.index:
            signals_normalized[signal] = round(float(row[norm_col]), 1)

    summary.update({
        "rating_actual": float(row["rating_actual"]),
        "rating_prom_30d": float(row["rating_prom_30d"]),
        "delta_rating": float(row["delta_rating"]),
        "tasa_cancelacion_pct": float(row["tasa_cancelacion_pct"]),
        "tiempo_entrega_avg_min": int(row["tiempo_entrega_avg_min"]),
        "quejas_7d": int(row["quejas_7d"]),
        "var_ordenes_pct": float(row["var_ordenes_pct"]),
        "nps_score": int(row["nps_score"]),
        "ordenes_7d": int(row["ordenes_7d"]),
        "valor_ticket_prom_mxn": float(row["valor_ticket_prom_mxn"]),
        "signals_normalized": signals_normalized,
        "kam_asignado": row["kam_asignado"],
        "activo_desde": row["activo_desde"],
        "semaforo_riesgo": row["semaforo_riesgo"],
    })
    return summary


def get_portfolio_overview(df: pd.DataFrame, kam_name: str | None = None) -> dict:
    filtered = _filter_kam(df, kam_name)
    quadrant_counts = filtered["quadrant"].value_counts().to_dict()
    rescue_triage = filtered[filtered["quadrant"].isin(["RESCUE", "TRIAGE"])]
    velocity_alerts = filtered[filtered["velocity_flag"] == True]

    return {
        "total_restaurants": len(filtered),
        "quadrant_distribution": {
            "GROW": quadrant_counts.get("GROW", 0),
            "RESCUE": quadrant_counts.get("RESCUE", 0),
            "NURTURE": quadrant_counts.get("NURTURE", 0),
            "TRIAGE": quadrant_counts.get("TRIAGE", 0),
        },
        "total_revenue": round(float(filtered["weekly_revenue"].sum()), 2),
        "revenue_at_risk": round(float(rescue_triage["weekly_revenue"].sum()), 2),
        "velocity_alert_count": int(velocity_alerts.shape[0]),
    }


def get_kam_briefing(df: pd.DataFrame, kam_name: str) -> list[dict]:
    filtered = _filter_kam(df, kam_name)

    # Priority ordering: RESCUE (asc health) → immediate velocity → 5_day velocity → TRIAGE (asc health) → GROW (desc revenue)
    priority_order = {"RESCUE": 0, "TRIAGE": 2, "NURTURE": 3, "GROW": 4}
    escalation_order = {"immediate": 0, "5_day": 1, "none": 2}

    def sort_key(idx):
        row = filtered.loc[idx]
        quadrant_priority = priority_order.get(row["quadrant"], 5)
        esc_priority = escalation_order.get(row["escalation_level"], 3)
        # Within same priority group, sort by health ascending (worst first)
        # except GROW which sorts by revenue descending
        if row["quadrant"] == "GROW":
            return (quadrant_priority, esc_priority, -row["weekly_revenue"])
        return (quadrant_priority, esc_priority, row["health_score"])

    sorted_idx = sorted(filtered.index, key=sort_key)
    return [_restaurant_summary(filtered.loc[idx]) for idx in sorted_idx]


def get_velocity_alerts(df: pd.DataFrame, kam_name: str | None = None) -> list[dict]:
    filtered = _filter_kam(df, kam_name)
    alerts = filtered[filtered["velocity_flag"] == True]
    # Sort: immediate first, then 5_day, then by health ascending
    escalation_order = {"immediate": 0, "5_day": 1}
    sorted_alerts = alerts.assign(
        _esc_order=alerts["escalation_level"].map(escalation_order)
    ).sort_values(["_esc_order", "health_score"])
    return [_restaurant_summary(sorted_alerts.loc[idx]) for idx in sorted_alerts.index]


def get_revenue_at_risk(df: pd.DataFrame, kam_name: str | None = None) -> dict:
    filtered = _filter_kam(df, kam_name)
    rescue = filtered[filtered["quadrant"] == "RESCUE"]
    triage = filtered[filtered["quadrant"] == "TRIAGE"]
    velocity_threatened = filtered[
        (filtered["velocity_flag"] == True) & (filtered["quadrant"].isin(["GROW", "NURTURE"]))
    ]

    return {
        "rescue_revenue": round(float(rescue["weekly_revenue"].sum()), 2),
        "triage_revenue": round(float(triage["weekly_revenue"].sum()), 2),
        "velocity_threatened_revenue": round(float(velocity_threatened["weekly_revenue"].sum()), 2),
        "total_at_risk": round(float(
            rescue["weekly_revenue"].sum()
            + triage["weekly_revenue"].sum()
            + velocity_threatened["weekly_revenue"].sum()
        ), 2),
        "rescue_count": len(rescue),
        "triage_count": len(triage),
        "velocity_threatened_count": len(velocity_threatened),
    }


def get_restaurant_detail(df: pd.DataFrame, restaurant_id: str) -> dict:
    matches = df[df["restaurant_id"] == restaurant_id]
    if matches.empty:
        return {"error": f"Restaurant {restaurant_id} not found"}
    return _restaurant_detail(matches.iloc[0])


def get_restaurants_by_quadrant(
    df: pd.DataFrame, quadrant: str, kam_name: str | None = None
) -> list[dict]:
    filtered = _filter_kam(df, kam_name)
    in_quadrant = filtered[filtered["quadrant"] == quadrant.upper()]
    if quadrant.upper() in ("RESCUE", "TRIAGE"):
        in_quadrant = in_quadrant.sort_values("health_score", ascending=True)
    else:
        in_quadrant = in_quadrant.sort_values("health_score", ascending=False)
    return [_restaurant_summary(in_quadrant.loc[idx]) for idx in in_quadrant.index]


def compare_restaurants(df: pd.DataFrame, restaurant_ids: list[str]) -> list[dict]:
    matches = df[df["restaurant_id"].isin(restaurant_ids)]
    return [_restaurant_detail(matches.loc[idx]) for idx in matches.index]


def get_city_breakdown(df: pd.DataFrame, kam_name: str | None = None) -> list[dict]:
    filtered = _filter_kam(df, kam_name)
    result = []
    for city, group in filtered.groupby("ciudad"):
        quadrant_counts = group["quadrant"].value_counts().to_dict()
        result.append({
            "ciudad": city,
            "restaurant_count": len(group),
            "avg_health_score": round(float(group["health_score"].mean()), 1),
            "total_revenue": round(float(group["weekly_revenue"].sum()), 2),
            "velocity_alerts": int(group["velocity_flag"].sum()),
            "quadrant_distribution": {
                "GROW": quadrant_counts.get("GROW", 0),
                "RESCUE": quadrant_counts.get("RESCUE", 0),
                "NURTURE": quadrant_counts.get("NURTURE", 0),
                "TRIAGE": quadrant_counts.get("TRIAGE", 0),
            },
        })
    return sorted(result, key=lambda x: x["total_revenue"], reverse=True)


def get_vertical_breakdown(df: pd.DataFrame, kam_name: str | None = None) -> list[dict]:
    filtered = _filter_kam(df, kam_name)
    result = []
    for vertical, group in filtered.groupby("vertical"):
        quadrant_counts = group["quadrant"].value_counts().to_dict()
        result.append({
            "vertical": vertical,
            "restaurant_count": len(group),
            "avg_health_score": round(float(group["health_score"].mean()), 1),
            "total_revenue": round(float(group["weekly_revenue"].sum()), 2),
            "velocity_alerts": int(group["velocity_flag"].sum()),
            "quadrant_distribution": {
                "GROW": quadrant_counts.get("GROW", 0),
                "RESCUE": quadrant_counts.get("RESCUE", 0),
                "NURTURE": quadrant_counts.get("NURTURE", 0),
                "TRIAGE": quadrant_counts.get("TRIAGE", 0),
            },
        })
    return sorted(result, key=lambda x: x["total_revenue"], reverse=True)


def search_restaurants(df: pd.DataFrame, query: str) -> list[dict]:
    q = query.lower()
    mask = (
        df["nombre"].str.lower().str.contains(q, na=False)
        | df["ciudad"].str.lower().str.contains(q, na=False)
        | df["vertical"].str.lower().str.contains(q, na=False)
        | df["kam_asignado"].str.lower().str.contains(q, na=False)
        | df["restaurant_id"].str.lower().str.contains(q, na=False)
    )
    matches = df[mask]
    return [_restaurant_summary(matches.loc[idx]) for idx in matches.index]
