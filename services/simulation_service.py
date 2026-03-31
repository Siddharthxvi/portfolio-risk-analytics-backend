import logging
from datetime import datetime
from typing import Dict, Any, Tuple
from sqlalchemy.orm import Session

from core.database import SessionLocal
from models.portfolio import Portfolio
from models.simulation import Scenario, SimulationRun, RiskMetric
from core.simulation.engine import ENGINES
from core.simulation.metrics import compute_metrics, build_histogram
from core.simulation.validation.portfolio_validator import validate_portfolio, PortfolioValidationError
from core.simulation.validation.scenario_validator import validate_scenario, ScenarioValidationError

logger = logging.getLogger("simulation_service")

def extract_payloads(port: Portfolio, scen: Scenario) -> Tuple[list, dict]:
    """Helper to shape DB entities into mathematical payloads."""
    assets_payload = [
        {
            "asset_type": pa.asset.asset_type.type_name if pa.asset.asset_type else "equity",
            "weight": pa.weight,
            "quantity": pa.quantity,
            "base_price": pa.asset.base_price,
            "annual_volatility": pa.asset.annual_volatility,
            "annual_return": pa.asset.annual_return,
        }
        for pa in port.assets
    ]
    scenario_payload = {
        "interest_rate_shock_bps": scen.interest_rate_shock_bps,
        "volatility_multiplier": scen.volatility_multiplier,
        "equity_shock_pct": scen.equity_shock_pct,
    }
    return assets_payload, scenario_payload


def run_adhoc_simulation(
    assets: list,
    scenario: dict,
    num_iterations: int,
    time_horizon_days: int,
    random_seed: int,
    simulation_type: str,
    confidence_level: float,
) -> Tuple[Dict[str, float], Dict[str, Any]]:
    """Runs a stateless simulation with full validation."""
    logger.info(f"Starting ad-hoc {simulation_type} simulation ({num_iterations} runs)")
    
    validate_portfolio(assets)
    validate_scenario(scenario)

    engine_func = ENGINES.get(simulation_type, ENGINES['monte_carlo'])
    pnl = engine_func(assets, scenario, num_iterations, time_horizon_days, random_seed)
    
    metrics = compute_metrics(pnl, confidence_level, num_iterations)
    histogram = build_histogram(pnl, num_bins=60)
    
    logger.info("Ad-hoc simulation complete.")
    return metrics, histogram


def execute_background_simulation(run_id: int):
    """Background task logic wrapper — opens a fresh DB session and controls the atomic transaction."""
    logger.info(f"Background worker picked up Simulation Run ID: {run_id}")
    db: Session = SessionLocal()
    
    try:
        sim_run = db.query(SimulationRun).filter(SimulationRun.run_id == run_id).first()
        if not sim_run:
            logger.error(f"SimulationRun {run_id} not found in DB.")
            return

        port = db.query(Portfolio).filter(Portfolio.portfolio_id == sim_run.portfolio_id).first()
        scen = db.query(Scenario).filter(Scenario.scenario_id == sim_run.scenario_id).first()

        if not port or not scen:
            raise ValueError("Portfolio or Scenario lookup failed.")

        # Map to math payloads
        assets_payload, scenario_payload = extract_payloads(port, scen)

        # Validate
        validate_portfolio(assets_payload)
        validate_scenario(scenario_payload)

        # Dispatch
        engine_func = ENGINES.get(sim_run.run_type, ENGINES['monte_carlo'])
        pnl = engine_func(
            assets_payload, 
            scenario_payload, 
            sim_run.num_simulations, 
            sim_run.time_horizon_days, 
            sim_run.random_seed
        )

        # We assume 0.95 confidence level if not explicitly defined on model, using default param
        metrics = compute_metrics(pnl, 0.95, sim_run.num_simulations)
        histogram = build_histogram(pnl, num_bins=60)

        # Persist results atomically
        for k, v in metrics.items():
            conf = 0.95 if "95" in k else (0.99 if "99" in k else None)
            db.add(RiskMetric(run_id=sim_run.run_id, metric_type=k, metric_value=v, confidence_level=conf))

        sim_run.histogram_data = histogram
        sim_run.status = "completed"
        sim_run.completed_at = datetime.utcnow()
        db.commit()
        
        logger.info(f"Successfully processed Simulation Run ID: {run_id}")

    except (PortfolioValidationError, ScenarioValidationError) as e:
        logger.warning(f"Validation failed for run {run_id}: {str(e)}")
        _mark_failed(db, run_id, str(e))
    except Exception as e:
        logger.warning(f"System failure during run {run_id}: {str(e)}")
        _mark_failed(db, run_id, str(e))
    finally:
        db.close()


def _mark_failed(db: Session, run_id: int, error_msg: str):
    """Marks a persistent simulation run as failed and commits."""
    try:
        db.rollback()
        run = db.query(SimulationRun).filter(SimulationRun.run_id == run_id).first()
        if run:
            run.status = "failed"
            # Note: We could save the error_msg somewhere if the schema supported it.
            run.completed_at = datetime.utcnow()
            db.commit()
    except Exception as e:
        logger.error(f"CRITICAL: Failed to mark run {run_id} as failed: {e}")
