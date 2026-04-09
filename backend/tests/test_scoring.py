from app.engine.scoring import SIGNAL_CONFIG


def test_weights_sum_to_one():
    total = sum(cfg["weight"] for cfg in SIGNAL_CONFIG.values())
    assert abs(total - 1.0) < 1e-9


def test_health_scores_in_range(df):
    assert df["health_score"].min() >= 0
    assert df["health_score"].max() <= 100


def test_estable_avg_health(df):
    estable = df[df["semaforo_riesgo"].str.contains("ESTABLE")]
    avg = estable["health_score"].mean()
    # Business case says ~86.9
    assert 80 <= avg <= 95, f"ESTABLE avg health {avg} outside expected range"


def test_en_riesgo_avg_health(df):
    en_riesgo = df[df["semaforo_riesgo"].str.contains("EN RIESGO")]
    avg = en_riesgo["health_score"].mean()
    # Business case says ~61.7
    assert 55 <= avg <= 70, f"EN RIESGO avg health {avg} outside expected range"


def test_critico_avg_health(df):
    critico = df[df["semaforo_riesgo"].str.contains("CRÍTICO")]
    avg = critico["health_score"].mean()
    # Business case says ~30.0
    assert 15 <= avg <= 45, f"CRITICO avg health {avg} outside expected range"


def test_health_separation(df):
    """ESTABLE avg should be clearly above EN RIESGO, which should be above CRITICO."""
    estable_avg = df[df["semaforo_riesgo"].str.contains("ESTABLE")]["health_score"].mean()
    riesgo_avg = df[df["semaforo_riesgo"].str.contains("EN RIESGO")]["health_score"].mean()
    critico_avg = df[df["semaforo_riesgo"].str.contains("CRÍTICO")]["health_score"].mean()
    assert estable_avg > riesgo_avg > critico_avg
