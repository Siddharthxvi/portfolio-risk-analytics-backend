from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
from core.database import get_db
from models.portfolio import Portfolio
from models.simulation import Scenario, SimulationRun, RiskMetric
from schemas.simulation import SimulationRunCreate, SimulationRunResponse
from services.simulation import run_monte_carlo
from sqlalchemy.exc import IntegrityError

router = APIRouter()

@router.post("/", response_model=SimulationRunResponse)
def run_simulation(req: SimulationRunCreate, db: Session = Depends(get_db)):
    port = db.query(Portfolio).filter(Portfolio.portfolio_id == req.portfolio_id).first()
    scen = db.query(Scenario).filter(Scenario.scenario_id == req.scenario_id).first()
    
    if not port or not scen:
        raise HTTPException(status_code=404, detail="Portfolio or Scenario not found")
        
    assets_payload = []
    for pa in port.assets:
        assets_payload.append({
            'asset_type': pa.asset.type_disc,
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
