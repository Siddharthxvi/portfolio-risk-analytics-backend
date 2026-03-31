from fastapi import APIRouter
from api.routes import assets, portfolios, scenarios, simulation, comparison

api_router = APIRouter()

api_router.include_router(assets.router, prefix="/assets", tags=["Assets"])
api_router.include_router(portfolios.router, prefix="/portfolios", tags=["Portfolios"])
api_router.include_router(scenarios.router, prefix="/scenarios", tags=["Scenarios"])
api_router.include_router(simulation.router, prefix="/simulation-runs", tags=["Simulation Runs"])
api_router.include_router(comparison.router, prefix="/comparison", tags=["Comparison Dashboard"])
