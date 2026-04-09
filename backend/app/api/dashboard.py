from fastapi import APIRouter, Request

router = APIRouter(prefix="/api")


@router.get("/dashboard")
async def dashboard(request: Request, kam: str | None = None):
    engine = request.app.state.engine
    return engine.get_portfolio_overview(kam)


@router.get("/dashboard/restaurants")
async def restaurants(request: Request, kam: str | None = None, quadrant: str | None = None):
    engine = request.app.state.engine
    if quadrant:
        return engine.get_restaurants_by_quadrant(quadrant, kam)
    return engine.get_kam_briefing(kam) if kam else engine.get_portfolio_overview()


@router.get("/dashboard/restaurants/{restaurant_id}")
async def restaurant_detail(request: Request, restaurant_id: str):
    engine = request.app.state.engine
    return engine.get_restaurant_detail(restaurant_id)


@router.get("/dashboard/alerts")
async def alerts(request: Request, kam: str | None = None):
    engine = request.app.state.engine
    return engine.get_velocity_alerts(kam)
