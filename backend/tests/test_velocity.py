def test_velocity_flag_count(df):
    velocity = df[df["velocity_flag"] == True]
    assert len(velocity) > 0


def test_immediate_escalation(df):
    immediate = df[df["escalation_level"] == "immediate"]
    # All immediate should have both signals
    for _, row in immediate.iterrows():
        assert row["delta_rating"] < -0.4
        assert row["var_ordenes_pct"] < -20.0


def test_five_day_escalation(df):
    five_day = df[df["escalation_level"] == "5_day"]
    # Should have at least one signal, but not necessarily both
    for _, row in five_day.iterrows():
        has_delta = row["delta_rating"] < -0.4
        has_var = row["var_ordenes_pct"] < -20.0
        assert has_delta or has_var
        assert not (has_delta and has_var)  # If both, should be "immediate"


def test_no_escalation_means_no_flag(df):
    no_esc = df[df["escalation_level"] == "none"]
    assert (no_esc["velocity_flag"] == False).all()
