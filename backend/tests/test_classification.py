def test_quadrant_counts(df):
    counts = df["quadrant"].value_counts().to_dict()
    assert counts.get("GROW", 0) > 0
    assert counts.get("RESCUE", 0) == 5, f"Expected 5 RESCUE, got {counts.get('RESCUE', 0)}"
    assert counts.get("NURTURE", 0) > 0
    assert counts.get("TRIAGE", 0) > 0
    assert sum(counts.values()) == 205


def test_rescue_restaurants_are_high_value(engine, df):
    rescue = df[df["quadrant"] == "RESCUE"]
    for _, row in rescue.iterrows():
        assert row["weekly_revenue"] >= engine.pareto_threshold


def test_grow_restaurants_are_healthy(df):
    grow = df[df["quadrant"] == "GROW"]
    assert (grow["health_score"] >= 60).all()


def test_triage_restaurants_are_low_on_both(engine, df):
    triage = df[df["quadrant"] == "TRIAGE"]
    for _, row in triage.iterrows():
        assert row["health_score"] < 60
        assert row["weekly_revenue"] < engine.pareto_threshold


def test_pareto_threshold_approx(engine):
    # Business case says ~$71,800
    assert 50000 <= engine.pareto_threshold <= 100000, \
        f"Pareto threshold {engine.pareto_threshold} outside expected range"
