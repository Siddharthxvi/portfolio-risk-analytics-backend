import numpy as np
from core.simulation.engine import run_gbm
from core.simulation.metrics import compute_metrics
from core.simulation.validation.portfolio_validator import validate_portfolio, PortfolioValidationError
from core.simulation.validation.scenario_validator import validate_scenario, ScenarioValidationError

def test_engine_and_metrics():
    # 1. Setup Data
    assets = [
        {"asset_type": "equity", "weight": 0.6, "quantity": 100, "base_price": 100.0, "annual_volatility": 0.20, "annual_return": 0.08},
        {"asset_type": "bond", "weight": 0.4, "quantity": 100, "base_price": 100.0, "annual_volatility": 0.05, "annual_return": 0.04}
    ]
    scenario = {"interest_rate_shock_bps": 0, "volatility_multiplier": 1.0, "equity_shock_pct": 0.0}

    # 2. Validation Checks
    validate_portfolio(assets)
    validate_scenario(scenario)

    # 3. Execution
    num_iters = 10000
    pnl = run_gbm(assets, scenario, num_iterations=num_iters, time_horizon_days=10, random_seed=42)
    
    assert len(pnl) == num_iters, "Output array must match iterations"

    # 4. Metrics verification
    metrics = compute_metrics(pnl, confidence_level=0.95, num_iterations=num_iters)
    
    assert 'VaR_95' in metrics
    assert 'VaR_99' in metrics
    assert 'ES_95' in metrics
    
    # Fundamental Risk Math Constraints
    assert metrics['VaR_99'] >= metrics['VaR_95'], "VaR 99% must be >= VaR 95%"
    assert metrics['ES_95'] >= metrics['VaR_95'], "Expected Shortfall must be >= VaR"

def test_portfolio_validation_fails():
    assets_bad_weights = [{"weight": 0.5}]
    try:
        validate_portfolio(assets_bad_weights)
        assert False, "Should have raised PortfolioValidationError"
    except PortfolioValidationError:
        pass

def test_scenario_validation_fails():
    scenario_bad_vol = {"volatility_multiplier": -1.0}
    try:
        validate_scenario(scenario_bad_vol)
        assert False, "Should have raised ScenarioValidationError"
    except ScenarioValidationError:
        pass

if __name__ == "__main__":
    test_engine_and_metrics()
    test_portfolio_validation_fails()
    test_scenario_validation_fails()
    print("✅ All Simulation Engine and Metrics tests passed!")
