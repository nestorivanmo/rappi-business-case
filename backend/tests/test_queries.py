def test_portfolio_overview_all(engine):
    overview = engine.get_portfolio_overview()
    assert overview["total_restaurants"] == 205
    dist = overview["quadrant_distribution"]
    assert sum(dist.values()) == 205
    assert overview["total_revenue"] > 0


def test_portfolio_overview_filtered(engine):
    overview = engine.get_portfolio_overview("Ana Torres")
    assert overview["total_restaurants"] > 0
    assert overview["total_restaurants"] < 205


def test_kam_briefing_ordering(engine):
    briefing = engine.get_kam_briefing("Ana Torres")
    assert len(briefing) > 0
    # RESCUE/TRIAGE should come before GROW
    quadrants = [r["quadrant"] for r in briefing]
    priority = {"RESCUE": 0, "TRIAGE": 1, "NURTURE": 2, "GROW": 3}
    priorities = [priority.get(q, 4) for q in quadrants]
    # Check that priorities are non-decreasing (allowing ties)
    for i in range(len(priorities) - 1):
        assert priorities[i] <= priorities[i + 1], \
            f"Briefing ordering violated at index {i}: {quadrants[i]} before {quadrants[i+1]}"


def test_restaurant_detail(engine):
    detail = engine.get_restaurant_detail("R0005")
    assert detail["restaurant_id"] == "R0005"
    assert "health_score" in detail
    assert "signals_normalized" in detail
    assert "quadrant" in detail
    assert "rating_actual" in detail


def test_restaurant_detail_not_found(engine):
    result = engine.get_restaurant_detail("XXXXX")
    assert "error" in result


def test_restaurants_by_quadrant(engine):
    grow = engine.get_restaurants_by_quadrant("GROW")
    assert len(grow) > 0
    assert all(r["quadrant"] == "GROW" for r in grow)


def test_compare_restaurants(engine):
    result = engine.compare_restaurants(["R0005", "R0054"])
    assert len(result) == 2


def test_search_restaurants(engine):
    results = engine.search_restaurants("Bogotá")
    assert len(results) > 0
    assert all("Bogotá" in r["ciudad"] for r in results)


def test_velocity_alerts(engine):
    alerts = engine.get_velocity_alerts()
    assert len(alerts) > 0
    assert all(r["velocity_flag"] for r in alerts)


def test_revenue_at_risk(engine):
    risk = engine.get_revenue_at_risk()
    assert risk["rescue_count"] == 5
    assert risk["total_at_risk"] > 0


def test_city_breakdown(engine):
    cities = engine.get_city_breakdown()
    assert len(cities) > 0
    assert "ciudad" in cities[0]
    assert "total_revenue" in cities[0]


def test_vertical_breakdown(engine):
    verticals = engine.get_vertical_breakdown()
    assert len(verticals) > 0
    assert "vertical" in verticals[0]
