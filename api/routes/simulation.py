from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from core.database import get_db
from core.auth import require_role
from models.portfolio import Portfolio
from models.simulation import Scenario, SimulationRun
from models.user_settings import UserSettings
from schemas.simulation import (
    SimulationRunCreate, 
    SimulationRunResponse, 
    SimulationRunUpdate,
    AdHocSimulationRequest, 
    AdHocSimulationResponse, 
    HistogramResponse
)
from sqlalchemy.exc import IntegrityError
from services.simulation_service import run_adhoc_simulation, execute_background_simulation

router = APIRouter()

ReadAccess   = Depends(require_role("ADMIN", "ANALYST", "VIEWER"))
WriteAccess  = Depends(require_role("ADMIN", "ANALYST"))

def _get_user_settings(db: Session, user_id: int):
    # Retrieve user settings, or return a set of minimal defaults structure
    settings = db.query(UserSettings).filter(UserSettings.user_id == user_id).first()
    if settings:
        return settings.default_iterations, settings.default_horizon_days, settings.default_confidence_level
    return 10000, 252, 0.95

@router.post("/ad-hoc", response_model=AdHocSimulationResponse, dependencies=[WriteAccess])
def run_adhoc(
    req: AdHocSimulationRequest,
    db: Session = Depends(get_db),
    current_user: dict = WriteAccess
):
    """
    Stateless Monte Carlo simulation — no DB persistence.
    """
    assets_payload = [
        {
            "asset_type": asset.asset_type,
            "weight": asset.weight,
            "quantity": asset.quantity,
            "base_price": asset.base_price,
            "annual_volatility": asset.annual_volatility,
            "annual_return": asset.annual_return,
        }
        for asset in req.portfolio_assets
    ]
    scenario_payload = {
        "interest_rate_shock_bps": req.scenario.interest_rate_shock_bps,
        "volatility_multiplier": req.scenario.volatility_multiplier,
        "equity_shock_pct": req.scenario.equity_shock_pct,
    }
    
    iters, horiz, conf = _get_user_settings(db, current_user["user_id"])
    
    num_iterations = req.num_iterations or iters
    time_horizon = req.time_horizon_days or horiz
    confidence_level = req.confidence_level or conf

    try:
        metrics, histogram = run_adhoc_simulation(
            assets=assets_payload,
            scenario=scenario_payload,
            num_iterations=num_iterations,
            time_horizon_days=time_horizon,
            random_seed=req.random_seed,
            simulation_type=req.simulation_type,
            confidence_level=confidence_level,
        )
        return {"metrics": metrics, "histogram": histogram}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Simulation Engine Failure: {str(e)}")


@router.get("/", response_model=List[SimulationRunResponse], dependencies=[ReadAccess])
def get_runs(db: Session = Depends(get_db)):
    return db.query(SimulationRun).all()


@router.get("/{run_id}", response_model=SimulationRunResponse, dependencies=[ReadAccess])
def get_run(run_id: int, db: Session = Depends(get_db)):
    run = db.query(SimulationRun).filter(SimulationRun.run_id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    return run

@router.put("/{run_id}", response_model=SimulationRunResponse, dependencies=[WriteAccess])
def update_run(run_id: int, req: SimulationRunUpdate, db: Session = Depends(get_db)):
    run = db.query(SimulationRun).filter(SimulationRun.run_id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    update_data = req.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(run, field, value)

    db.commit()
    db.refresh(run)
    return run

@router.delete("/{run_id}", dependencies=[WriteAccess])
def delete_run(run_id: int, db: Session = Depends(get_db)):
    run = db.query(SimulationRun).filter(SimulationRun.run_id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    db.delete(run)
    db.commit()
    return {"detail": "Simulation Run deleted"}


@router.get("/{run_id}/distribution", response_model=HistogramResponse, dependencies=[ReadAccess])
def get_run_distribution(run_id: int, db: Session = Depends(get_db)):
    run = db.query(SimulationRun).filter(SimulationRun.run_id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    if not run.histogram_data:
        raise HTTPException(status_code=404, detail="Histogram data not available for this run")
    return run.histogram_data


@router.post("/", response_model=SimulationRunResponse)
def create_run_simulation(
    req: SimulationRunCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role("ADMIN", "ANALYST"))
):
    """
    Persistent simulation: Non-blocking, runs in background.
    """
    port = db.query(Portfolio).filter(Portfolio.portfolio_id == req.portfolio_id).first()
    scen = db.query(Scenario).filter(Scenario.scenario_id == req.scenario_id).first()

    if not port or not scen:
        raise HTTPException(status_code=404, detail="Portfolio or Scenario not found")

    iters, horiz, _ = _get_user_settings(db, current_user["user_id"])
    
    sim_run = SimulationRun(
        portfolio_id=req.portfolio_id,
        scenario_id=req.scenario_id,
        initiated_by=current_user["user_id"],
        status="running",
        run_type=req.simulation_type,
        num_simulations=req.num_simulations or iters,
        time_horizon_days=req.time_horizon_days or horiz,
        random_seed=req.random_seed,
    )
    db.add(sim_run)
    try:
        db.commit()
        db.refresh(sim_run)
        
        # Schedule background worker
        background_tasks.add_task(execute_background_simulation, sim_run.run_id)

        # Return immediately
        return SimulationRunResponse.model_validate(sim_run)
    except IntegrityError as e:
        db.rollback()
        # Handle case where sim parameters violate DB CHECK constraints
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid simulation parameters: {str(e.orig)}"
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Unexpected failure: {str(e)}")
