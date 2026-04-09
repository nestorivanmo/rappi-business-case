from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import Settings


settings = Settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: load data, initialize engine and budget manager
    from app.engine import DiagnosticEngine
    from app.budget.manager import BudgetManager

    engine = DiagnosticEngine(
        data_path=settings.data_path,
        health_threshold=settings.health_threshold,
    )
    budget_manager = BudgetManager(
        weekly_allocation=settings.budget_weekly_allocation_mxn,
        interventions_path=settings.interventions_path,
        engine=engine,
    )
    app.state.engine = engine
    app.state.budget_manager = budget_manager
    app.state.settings = settings
    yield


app = FastAPI(title="Rappi KAM Intelligence", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import and mount route modules
from app.api.dashboard import router as dashboard_router
from app.api.budget_routes import router as budget_router
from app.api.chat import router as chat_router

app.include_router(dashboard_router)
app.include_router(budget_router)
app.include_router(chat_router)


@app.get("/health")
async def health_check():
    engine = app.state.engine
    return {"status": "ok", "restaurants_loaded": len(engine.df)}
