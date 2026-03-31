from typing import Dict

class ScenarioValidationError(Exception):
    pass

def validate_scenario(scenario: Dict) -> None:
    """
    Validates scenario inputs before simulation run.
    - volatility_multiplier > 0
    - equity_shock_pct is bounded [-1.0, 1.0]
    """
    if "volatility_multiplier" not in scenario:
        raise ScenarioValidationError("Scenario must include volatility_multiplier")
        
    vol_mult = scenario["volatility_multiplier"]
    if vol_mult <= 0:
        raise ScenarioValidationError(f"Volatility multiplier must be strictly positive, got {vol_mult}")
        
    equity_shock = scenario.get("equity_shock_pct", 0.0)
    if not (-1.0 <= equity_shock <= 1.0):
        raise ScenarioValidationError(f"Equity shock percentage must be between -100% and +100%, got {equity_shock}")
