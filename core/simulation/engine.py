import numpy as np
from typing import List, Dict

def _apply_shocks(asset: dict, scenario: dict) -> tuple[float, float]:
    """Applies scenario shocks to core macro parameters."""
    eff_vol = asset['annual_volatility'] * scenario['volatility_multiplier']
    eff_ret = asset['annual_return']

    atype = asset.get('asset_type', '').lower()
    if 'equity' in atype:
        eff_ret += scenario['equity_shock_pct']
    elif 'bond' in atype:
        eff_ret -= scenario['interest_rate_shock_bps'] / 10000.0

    return eff_vol, eff_ret

def run_gbm(assets: List[Dict], scenario: Dict, num_iterations: int, time_horizon_days: int, random_seed: int) -> np.ndarray:
    """Geometric Brownian Motion vector-optimized simulation."""
    np.random.seed(random_seed)
    asset_values = np.zeros(len(assets))
    asset_returns = np.zeros((len(assets), num_iterations))

    for j, asset in enumerate(assets):
        eff_vol, eff_ret = _apply_shocks(asset, scenario)

        mu_horizon = (eff_ret / 252.0) * time_horizon_days
        sigma_horizon = (eff_vol / np.sqrt(252.0)) * np.sqrt(time_horizon_days)

        asset_values[j] = asset['weight'] * asset['base_price'] * asset['quantity']
        asset_returns[j] = np.random.normal(mu_horizon, sigma_horizon, num_iterations)

    return np.dot(asset_values, asset_returns)

def run_historical_bootstrap(assets: List[Dict], scenario: Dict, num_iterations: int, time_horizon_days: int, random_seed: int) -> np.ndarray:
    """Bootstrap: simulate daily returns and sum over horizon."""
    rng = np.random.default_rng(random_seed)
    pnl = np.zeros(num_iterations)

    for asset in assets:
        eff_vol, eff_ret = _apply_shocks(asset, scenario)

        daily_mu = eff_ret / 252.0
        daily_sigma = eff_vol / np.sqrt(252.0)

        daily_draws = rng.normal(daily_mu, daily_sigma, (num_iterations, time_horizon_days))
        path_returns = daily_draws.sum(axis=1)

        position_value = asset['weight'] * asset['base_price'] * asset['quantity']
        pnl += position_value * path_returns

    return pnl

def run_parametric(assets: List[Dict], scenario: Dict, num_iterations: int, time_horizon_days: int, random_seed: int) -> np.ndarray:
    """Analytical variance-covariance based simulation (diagonal covariance)."""
    np.random.seed(random_seed)
    port_mu, port_var = 0.0, 0.0

    for asset in assets:
        eff_vol, eff_ret = _apply_shocks(asset, scenario)
        pos_value = asset['weight'] * asset['base_price'] * asset['quantity']

        mu_h = (eff_ret / 252.0) * time_horizon_days
        sigma_h = (eff_vol / np.sqrt(252.0)) * np.sqrt(time_horizon_days)

        port_mu += pos_value * mu_h
        port_var += (pos_value * sigma_h) ** 2

    return np.random.normal(port_mu, np.sqrt(port_var), num_iterations)

# Engine dispatch map
ENGINES = {
    'monte_carlo': run_gbm,
    'historical': run_historical_bootstrap,
    'parametric': run_parametric
}
