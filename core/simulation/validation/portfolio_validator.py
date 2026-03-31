from typing import List, Dict

class PortfolioValidationError(Exception):
    pass

def validate_portfolio(assets: List[Dict]) -> None:
    """
    Validates that a portfolio is mathematically sound for simulation.
    - Weights sum ~ 1.0
    - Quantities > 0
    - Prices > 0
    """
    if not assets:
        raise PortfolioValidationError("Portfolio must contain at least one asset")

    total_weight = sum(a.get("weight", 0.0) for a in assets)
    if abs(total_weight - 1.0) > 0.001:
        raise PortfolioValidationError(f"Portfolio weights must sum to 1.0, got {total_weight:.4f}")

    for a in assets:
        if a.get("base_price", 0) <= 0:
            raise PortfolioValidationError(f"Asset price must be positive, got {a.get('base_price')} for {a.get('asset_type')}")
        if a.get("quantity", 0) <= 0:
            raise PortfolioValidationError(f"Asset quantity must be positive, got {a.get('quantity')}")
