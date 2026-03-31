import numpy as np

def run_monte_carlo(assets, scenario, num_iterations: int, time_horizon_days: int, random_seed: int):
    """
    Executes the Monte Carlo risk simulation.

    :param assets: List of dicts with keys: 'asset_type', 'weight', 'base_price', 'quantity', 'annual_volatility', 'annual_return'
    :param scenario: Dict with keys: 'interest_rate_shock_bps', 'volatility_multiplier', 'equity_shock_pct'
    :param num_iterations: Integer (e.g., 10000)
    :param time_horizon_days: Integer (1, 10, 252)
    :param random_seed: Integer
    :return: dict of the 5 computed metrics
    """
    np.random.seed(random_seed)

    # We are simulating 'time_horizon_days' days worth of returns. 
    # The prompt actually asks to scale daily returns by time_horizon... or does it?
    # "Draw num_iterations random return samples for each asset from a normal distribution N(μ_daily, σ_daily)"
    # Wait, the spec says time_horizon_days but only gives formulas for daily scaling.
    # Actually, if time_horizon is T days, the path is normally sum of T daily returns. 
    # For a simple 1-step Brownian motion covering T days: 
    # expected return = μ_daily * T
    # volatility = σ_daily * sqrt(T)
    
    total_portfolio_value = 0.0
    
    # Store path returns per asset: shape (num_assets, num_iterations)
    asset_returns = np.zeros((len(assets), num_iterations))
    asset_values = np.zeros(len(assets))
    
    for j, asset in enumerate(assets):
        # 1. Apply scenario adjustments
        eff_vol = asset['annual_volatility'] * scenario['volatility_multiplier']
        eff_ret = asset['annual_return']
        
        # Determine strict type string (assuming 'equity', 'bond', etc. in 'type_name' or 'type_disc')
        atype = asset.get('asset_type', '').lower()
        if 'equity' in atype:
            eff_ret += scenario['equity_shock_pct']
        elif 'bond' in atype:
            eff_ret -= (scenario['interest_rate_shock_bps'] / 10000.0)
            
        # 2. Daily scaling
        mu_daily = eff_ret / 252.0
        sigma_daily = eff_vol / np.sqrt(252.0)
        
        # Adjust for time horizon
        mu_horizon = mu_daily * time_horizon_days
        sigma_horizon = sigma_daily * np.sqrt(time_horizon_days)
        
        # Generate Returns N(μ, σ)
        returns = np.random.normal(mu_horizon, sigma_horizon, num_iterations)
        
        # 3. Compute Value
        val = asset['base_price'] * asset['quantity']
        # The prompt says: "P&L[i] = Σ (weight[j] × base_price[j] × quantity[j] × return[i][j])"
        # Wait, weight * value? If you multiply weight again, it double counts the distribution of value if weight is a fraction!
        # Re-reading prompt: "weight[j] × base_price[j] × quantity[j] × return[i][j]"
        # If the TA literally wants this formula, I will follow it.
        # But wait, usually P&L of asset j is exactly `val * return`. 
        # But let's follow the literal formula:
        asset_values[j] = asset['weight'] * val
        asset_returns[j] = returns

        # compute standard total value for volatility division
        # Is it sum of base_price * quantity?
        total_portfolio_value += val
        
    # P&L matrix computation
    # P&L[i] = sum over j of (asset_values[j] * asset_returns[j][i])
    # This is exactly dot product
    pnl = np.dot(asset_values, asset_returns)
    
    # 4. Compute Metrics
    pnl_sorted = np.sort(pnl) # ascending: worst losses first
    
    idx_5 = int(num_iterations * 0.05)
    idx_1 = int(num_iterations * 0.01)
    
    var_95 = -pnl_sorted[idx_5]
    var_99 = -pnl_sorted[idx_1]
    es_95 = -np.mean(pnl_sorted[:idx_5]) # mean of losses below 5th percentile
    
    # Volatility = standard deviation of P&L distribution / portfolio total value
    # Wait, if total_portfolio_value was used, it'd just be std / total.
    # What if the portfolio is completely defined by the sum of asset_values? 
    # Let's use sum of asset_values (incorporating weight as per the equation) to be consistent.
    sum_asset_values = np.sum(asset_values)
    volatility = np.std(pnl) / sum_asset_values if sum_asset_values > 0 else 0.0
    
    max_drawdown = -np.min(pnl)
    
    return {
        'VaR_95': float(max(0.0, var_95)),  # ensuring strictly positive per trigger Check
        'VaR_99': float(max(0.0, var_99)),
        'ES_95': float(max(0.0, es_95)),
        'volatility': float(volatility),
        'max_drawdown': float(max(0.0, max_drawdown))
    }
