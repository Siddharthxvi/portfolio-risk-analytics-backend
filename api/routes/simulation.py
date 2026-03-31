from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict
from datetime import datetime
from core.database import get_db
from models.portfolio import Portfolio
from models.simulation import Scenario, SimulationRun, RiskMetric
from schemas.simulation import SimulationRunCreate, SimulationRunResponse, AdHocSimulationRequest
from services.simulation import run_monte_carlo
from sqlalchemy.exc import IntegrityError

router = APIRouter()

@router.post("/ad-hoc", response_model=Dict[str, float])
def run_adhoc_simulation(req: AdHocSimulationRequest):
    assets_payload = []
    for asset in req.portfolio_assets:
        assets_payload.append({
            'asset_type': asset.asset_type,
            'weight': asset.weight,
            'quantity': asset.quantity,
            'base_price': asset.base_price,
            'annual_volatility': asset.annual_volatility,
            'annual_return': asset.annual_return
        })
        
    scenario_payload = {
        'interest_rate_shock_bps': req.scenario.interest_rate_shock_bps,
        'volatility_multiplier': req.scenario.volatility_multiplier,
        'equity_shock_pct': req.scenario.equity_shock_pct
    }
    
    try:
        metrics = run_monte_carlo(
            assets=assets_payload, 
            scenario=scenario_payload, 
            iterations=req.num_iterations, 
            horizon=req.time_horizon_days, 
            seed=req.random_seed
        )
        return metrics
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Simulation Math Engine Failure: {str(e)}")

@router.get("/test", response_model=Dict[str, float])
def test_simulation_engine():
    """
    Dummy endpoint you can open in your browser to instantly verify the Monte Carlo engine works. 
    Hardcoded with 60% AAPL, 40% US10Y against a 2008-style crisis scenario.
    """
    dummy_assets = [
        {'asset_type': 'equity', 'weight': 0.6, 'quantity': 600, 'base_price': 100.0, 'annual_volatility': 0.28, 'annual_return': 0.12},
        {'asset_type': 'bond', 'weight': 0.4, 'quantity': 400, 'base_price': 100.0, 'annual_volatility': 0.05, 'annual_return': 0.04}
    ]
    dummy_scenario = {'interest_rate_shock_bps': -150, 'volatility_multiplier': 2.5, 'equity_shock_pct': -0.35}
    
    return run_monte_carlo(assets=dummy_assets, scenario=dummy_scenario, iterations=10000, horizon=100, seed=42)

@router.post("/", response_model=SimulationRunResponse)
def run_simulation(req: SimulationRunCreate, db: Session = Depends(get_db)):
    port = db.query(Portfolio).filter(Portfolio.portfolio_id == req.portfolio_id).first()
    scen = db.query(Scenario).filter(Scenario.scenario_id == req.scenario_id).first()
    
    if not port or not scen:
        raise HTTPException(status_code=404, detail="Portfolio or Scenario not found")
        
    assets_payload = []
    for pa in port.assets:
        assets_payload.append({
            'asset_type': pa.asset.asset_type.type_name,
            'weight': pa.weight,
            'quantity': pa.quantity,
            'base_price': pa.asset.base_price,
            'annual_volatility': pa.asset.annual_volatility,
            'annual_return': pa.asset.annual_return
        })
        
    scenario_payload = {
        'interest_rate_shock_bps': scen.interest_rate_shock_bps,
        'volatility_multiplier': scen.volatility_multiplier,
        'equity_shock_pct': scen.equity_shock_pct
    }
    
    sim_run = SimulationRun(
        portfolio_id=req.portfolio_id,
        scenario_id=req.scenario_id,
        initiated_by=1, 
        status='running',
        num_simulations=req.num_simulations,
        time_horizon_days=req.time_horizon_days,
        random_seed=req.random_seed
    )
    db.add(sim_run)
    db.flush()
    
    try:
        metrics = run_monte_carlo(assets_payload, scenario_payload, req.num_simulations, req.time_horizon_days, req.random_seed)
        
        for k, v in metrics.items():
            conf = 0.95 if '95' in k else (0.99 if '99' in k else None)
            rm = RiskMetric(run_id=sim_run.run_id, metric_type=k, metric_value=v, confidence_level=conf)
            db.add(rm)
            
        sim_run.status = 'completed'
        sim_run.completed_at = datetime.utcnow()
        db.commit()
        db.refresh(sim_run)
        return sim_run
    except Exception as e:
        db.rollback()
        db_sim_fail = SimulationRun(
            portfolio_id=req.portfolio_id,
            scenario_id=req.scenario_id,
            initiated_by=1,
            status='failed',
            num_simulations=req.num_simulations
        )
        db.add(db_sim_fail)
        db.commit()
        raise HTTPException(status_code=500, detail=f"Simulation failed: {str(e)}")

@router.get("/", response_model=List[SimulationRunResponse])
def get_runs(db: Session = Depends(get_db)):
    return db.query(SimulationRun).all()

@router.get("/{run_id}", response_model=SimulationRunResponse)
def get_run(run_id: int, db: Session = Depends(get_db)):
    run = db.query(SimulationRun).filter(SimulationRun.run_id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    return run
