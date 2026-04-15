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

    # Use or 0.0 to prevent TypeError if weight is None
    total_weight = sum(float(a.get("weight") or 0.0) for a in assets)
    if abs(total_weight - 1.0) > 0.001:
        raise PortfolioValidationError(f"Portfolio weights must sum to 1.0, got {total_weight:.4f}")

    for a in assets:
        price = a.get("base_price")
        qty = a.get("quantity")
        
        if price is None or float(price) <= 0:
            raise PortfolioValidationError(f"Asset price must be positive, got {price} for {a.get('asset_type')}")
        if qty is None or float(qty) <= 0:
            raise PortfolioValidationError(f"Asset quantity must be positive, got {qty}")
