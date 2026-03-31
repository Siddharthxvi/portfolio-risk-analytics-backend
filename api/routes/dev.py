from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any

from core.database import get_db, engine
from core.auth import require_role
from models.simulation import SimulationRun
from services.simulation_service import run_adhoc_simulation

router = APIRouter()
AdminOnly = Depends(require_role("ADMIN"))

@router.get("/test-simulation", dependencies=[AdminOnly])
def test_simulation_engine():
    """Hardcoded sanity-check: 60% AAPL / 40% US10Y in a 2008-style crisis."""
    dummy_assets = [
        {"asset_type": "equity", "weight": 0.6, "quantity": 600, "base_price": 100.0, "annual_volatility": 0.28, "annual_return": 0.12},
        {"asset_type": "bond",   "weight": 0.4, "quantity": 400, "base_price": 100.0, "annual_volatility": 0.05, "annual_return": 0.04},
    ]
    dummy_scenario = {"interest_rate_shock_bps": -150, "volatility_multiplier": 2.5, "equity_shock_pct": -0.35}
    metrics, histogram = run_adhoc_simulation(
        assets=dummy_assets, 
        scenario=dummy_scenario, 
        num_iterations=10000, 
        time_horizon_days=100, 
        random_seed=42, 
        simulation_type='monte_carlo', 
        confidence_level=0.95
    )
    return {"metrics": metrics, "histogram": histogram}

@router.get("/verify-metrics/{run_id}", dependencies=[AdminOnly])
def verify_metrics(run_id: int, db: Session = Depends(get_db)):
    """Recomputes metrics for an existing run and compares with DB rows."""
    from services.simulation_service import extract_payloads, ENGINES
    from core.simulation.metrics import compute_metrics
    
    run = db.query(SimulationRun).filter(SimulationRun.run_id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    if run.status != "completed":
        raise HTTPException(status_code=400, detail="Run not completed")
        
    assets_payload, scenario_payload = extract_payloads(run.portfolio, run.scenario)
    engine_func = ENGINES.get(run.run_type, ENGINES['monte_carlo'])
    
    pnl = engine_func(
        assets_payload, scenario_payload, 
        run.num_simulations, run.time_horizon_days, run.random_seed
    )
    computed = compute_metrics(pnl, 0.95, run.num_simulations)
    
    db_metrics = {m.metric_type: m.metric_value for m in run.risk_metrics}
    
    drift = {}
    for k, v in computed.items():
        if k in db_metrics:
            if abs(db_metrics[k] - v) > 0.001:
                drift[k] = {"db": db_metrics[k], "recomputed": v}
        
    return {
        "run_id": run_id,
        "is_perfect_match": len(drift) == 0,
        "drift": drift,
        "db_metrics": db_metrics,
        "recomputed": computed
    }

@router.get("/system-info", dependencies=[AdminOnly])
def system_info(db: Session = Depends(get_db)):
    from sqlalchemy import text
    try:
        db.execute(text("SELECT 1"))
        db_status = "healthy"
    except Exception:
        db_status = "unhealthy"
        
    runs = db.query(SimulationRun).all()
    total = len(runs)
    times = [r.execution_time_ms for r in runs if hasattr(r, 'execution_time_ms') and r.execution_time_ms]
    
    # We fallback to completed_at - started_at if execution_time_ms is not historically tracked properly
    time_diffs = []
    for r in runs:
        if r.status == "completed" and r.completed_at and r.started_at:
            time_diffs.append((r.completed_at - r.started_at).total_seconds())
            
    avg_time = sum(time_diffs) / len(time_diffs) if time_diffs else 0.0
    
    return {
        "db_status": db_status,
        "total_runs": total,
        "average_execution_time_seconds": round(avg_time, 3),
        "engines_available": ["monte_carlo", "historical", "parametric"]
    }
