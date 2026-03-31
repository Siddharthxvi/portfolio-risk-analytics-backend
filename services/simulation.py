import numpy as np
from typing import List, Dict

# ── Monte Carlo (GBM) ─────────────────────────────────────────────────────────
def _run_gbm(assets, scenario, num_iterations: int, time_horizon_days: int, random_seed: int) -> np.ndarray:
    """Geometric Brownian Motion — the default simulation engine."""
    np.random.seed(random_seed)
    asset_values = np.zeros(len(assets))
    asset_returns = np.zeros((len(assets), num_iterations))

    for j, asset in enumerate(assets):
        eff_vol = asset['annual_volatility'] * scenario['volatility_multiplier']
        eff_ret = asset['annual_return']

        atype = asset.get('asset_type', '').lower()
        if 'equity' in atype:
            eff_ret += scenario['equity_shock_pct']
        elif 'bond' in atype:
            eff_ret -= scenario['interest_rate_shock_bps'] / 10000.0

        mu_horizon    = (eff_ret / 252.0) * time_horizon_days
        sigma_horizon = (eff_vol / np.sqrt(252.0)) * np.sqrt(time_horizon_days)

        asset_values[j]  = asset['weight'] * asset['base_price'] * asset['quantity']
        asset_returns[j] = np.random.normal(mu_horizon, sigma_horizon, num_iterations)

    return np.dot(asset_values, asset_returns)


# ── Historical Bootstrap ──────────────────────────────────────────────────────
def _run_historical_bootstrap(assets, scenario, num_iterations: int, time_horizon_days: int, random_seed: int) -> np.ndarray:
    """
    Bootstrap: resample from a synthetic historical return distribution
    (normally distributed with historical params), then apply scenario shocks.
    """
    rng = np.random.default_rng(random_seed)
    pnl = np.zeros(num_iterations)

    for asset in assets:
        eff_vol = asset['annual_volatility'] * scenario['volatility_multiplier']
        eff_ret = asset['annual_return']

        atype = asset.get('asset_type', '').lower()
        if 'equity' in atype:
            eff_ret += scenario['equity_shock_pct']
        elif 'bond' in atype:
            eff_ret -= scenario['interest_rate_shock_bps'] / 10000.0

        daily_mu    = eff_ret / 252.0
        daily_sigma = eff_vol / np.sqrt(252.0)

        # Simulate daily returns and sum over horizon (bootstrap aggregation)
        daily_draws = rng.normal(daily_mu, daily_sigma, (num_iterations, time_horizon_days))
        path_returns = daily_draws.sum(axis=1)

        position_value = asset['weight'] * asset['base_price'] * asset['quantity']
        pnl += position_value * path_returns

    return pnl


# ── Parametric (Variance-Covariance) ─────────────────────────────────────────
def _run_parametric(assets, scenario, num_iterations: int, time_horizon_days: int, random_seed: int) -> np.ndarray:
    """
    Variance-Covariance: analytical normal distribution assumption.
    Computes portfolio mu/sigma analytically, then samples from that distribution.
    (Assumes zero cross-asset covariance for now — a standard simplification.)
    """
    np.random.seed(random_seed)
    port_mu    = 0.0
    port_var   = 0.0
    port_value = 0.0

    for asset in assets:
        eff_vol = asset['annual_volatility'] * scenario['volatility_multiplier']
        eff_ret = asset['annual_return']

        atype = asset.get('asset_type', '').lower()
        if 'equity' in atype:
            eff_ret += scenario['equity_shock_pct']
        elif 'bond' in atype:
            eff_ret -= scenario['interest_rate_shock_bps'] / 10000.0

        pos_value = asset['weight'] * asset['base_price'] * asset['quantity']
        mu_h      = (eff_ret / 252.0) * time_horizon_days
        sigma_h   = (eff_vol / np.sqrt(252.0)) * np.sqrt(time_horizon_days)

        port_value += pos_value
        port_mu    += pos_value * mu_h
        port_var   += (pos_value * sigma_h) ** 2   # diagonal covariance assumption

    port_sigma = np.sqrt(port_var)
    return np.random.normal(port_mu, port_sigma, num_iterations)


# ── Metric computation ────────────────────────────────────────────────────────
def _compute_metrics(pnl: np.ndarray, confidence_level: float, num_iterations: int) -> Dict[str, float]:
    """Derive the 5 standard risk metrics from a P&L distribution."""
    tail_pct    = 1.0 - confidence_level           # e.g. 0.05 for 95% CL
    tail_pct_99 = 0.01                             # VaR_99 always a 99% metric

    pnl_sorted = np.sort(pnl)
    idx_tail   = max(1, int(num_iterations * tail_pct))
    idx_99     = max(1, int(num_iterations * tail_pct_99))

    var_cl  = float(-pnl_sorted[idx_tail])
    var_99  = float(-pnl_sorted[idx_99])
    es_cl   = float(-np.mean(pnl_sorted[:idx_tail]))

    total_value = np.sum(np.abs(pnl)) / num_iterations
    volatility  = float(np.std(pnl) / total_value) if total_value > 0 else 0.0
    max_drawdown = float(-np.min(pnl))

    cl_label = f"{int(confidence_level * 100)}"
    return {
        f'VaR_{cl_label}':  max(0.0, var_cl),
        'VaR_99':           max(0.0, var_99),
        f'ES_{cl_label}':   max(0.0, es_cl),
        'volatility':       max(0.0, volatility),
        'max_drawdown':     max(0.0, max_drawdown),
    }


# ── Public entry point ────────────────────────────────────────────────────────
SIMULATION_ENGINES = {
    'monte_carlo': _run_gbm,
    'historical':  _run_historical_bootstrap,
    'parametric':  _run_parametric,
}

def run_monte_carlo(
    assets,
    scenario,
    num_iterations: int,
    time_horizon_days: int,
    random_seed: int,
    simulation_type: str = 'monte_carlo',
    confidence_level: float = 0.95,
) -> Dict[str, float]:
    """
    Unified simulation dispatcher.

    :param simulation_type: 'monte_carlo' | 'historical' | 'parametric'
    :param confidence_level: 0.90 | 0.95 | 0.99
    """
    engine = SIMULATION_ENGINES.get(simulation_type, _run_gbm)
    pnl    = engine(assets, scenario, num_iterations, time_horizon_days, random_seed)
    return _compute_metrics(pnl, confidence_level, num_iterations)
