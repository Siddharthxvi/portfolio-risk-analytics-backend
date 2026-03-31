import numpy as np
from typing import List, Dict, Tuple, Any

# ── Monte Carlo (GBM) ─────────────────────────────────────────────────────────
def _run_gbm(assets, scenario, num_iterations: int, time_horizon_days: int, random_seed: int) -> np.ndarray:
    """Geometric Brownian Motion — the default simulation engine."""
    np.random.seed(random_seed)
    asset_values  = np.zeros(len(assets))
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
    Bootstrap: simulate T daily returns per iteration and sum them.
    Captures compounding / path-dependence that simple GBM misses.
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

        # shape: (num_iterations, time_horizon_days) → sum over days
        daily_draws  = rng.normal(daily_mu, daily_sigma, (num_iterations, time_horizon_days))
        path_returns = daily_draws.sum(axis=1)

        position_value = asset['weight'] * asset['base_price'] * asset['quantity']
        pnl += position_value * path_returns

    return pnl


# ── Parametric (Variance-Covariance) ─────────────────────────────────────────
def _run_parametric(assets, scenario, num_iterations: int, time_horizon_days: int, random_seed: int) -> np.ndarray:
    """
    Variance-Covariance: aggregate portfolio μ / σ analytically then sample once.
    Diagonal covariance assumption (no cross-asset correlation).
    """
    np.random.seed(random_seed)
    port_mu  = 0.0
    port_var = 0.0

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

        port_mu  += pos_value * mu_h
        port_var += (pos_value * sigma_h) ** 2

    port_sigma = np.sqrt(port_var)
    return np.random.normal(port_mu, port_sigma, num_iterations)


# ── Histogram builder ─────────────────────────────────────────────────────────
def _build_histogram(pnl: np.ndarray, num_bins: int = 60) -> Dict[str, Any]:
    """
    Pre-bins the P&L distribution into `num_bins` buckets.
    Returns compact data ready for frontend charting — no raw array ever leaves the server.

    :returns: {
        "bin_edges":  [float, ...],   # length num_bins + 1
        "counts":     [int,   ...],   # length num_bins
        "bin_width":  float,
        "pnl_min":    float,
        "pnl_max":    float,
        "mean_pnl":   float,
    }
    """
    counts, bin_edges = np.histogram(pnl, bins=num_bins)
    return {
        "bin_edges":  [round(float(e), 4) for e in bin_edges],
        "counts":     [int(c) for c in counts],
        "bin_width":  round(float(bin_edges[1] - bin_edges[0]), 4),
        "pnl_min":    round(float(pnl.min()), 4),
        "pnl_max":    round(float(pnl.max()), 4),
        "mean_pnl":   round(float(pnl.mean()), 4),
    }


# ── Metric computation ────────────────────────────────────────────────────────
def _compute_metrics(pnl: np.ndarray, confidence_level: float, num_iterations: int) -> Dict[str, float]:
    """Derive the 5 standard risk metrics from a P&L distribution."""
    tail_pct = 1.0 - confidence_level
    pnl_sorted = np.sort(pnl)

    idx_tail = max(1, int(num_iterations * tail_pct))
    idx_99   = max(1, int(num_iterations * 0.01))

    var_cl = float(-pnl_sorted[idx_tail])
    var_99 = float(-pnl_sorted[idx_99])
    es_cl  = float(-np.mean(pnl_sorted[:idx_tail]))

    total_value  = float(np.sum(np.abs(pnl)) / num_iterations)
    volatility   = float(np.std(pnl) / total_value) if total_value > 0 else 0.0
    max_drawdown = float(-pnl.min())

    cl_label = str(int(confidence_level * 100))
    return {
        f'VaR_{cl_label}': max(0.0, var_cl),
        'VaR_99':          max(0.0, var_99),
        f'ES_{cl_label}':  max(0.0, es_cl),
        'volatility':      max(0.0, volatility),
        'max_drawdown':    max(0.0, max_drawdown),
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
    num_histogram_bins: int = 60,
) -> Tuple[Dict[str, float], Dict[str, Any]]:
    """
    Unified simulation dispatcher.

    Returns a tuple of (metrics_dict, histogram_dict).

    :param simulation_type:    'monte_carlo' | 'historical' | 'parametric'
    :param confidence_level:   0.90 | 0.95 | 0.99
    :param num_histogram_bins: Number of histogram bins for charting (default 60)
    """
    engine    = SIMULATION_ENGINES.get(simulation_type, _run_gbm)
    pnl       = engine(assets, scenario, num_iterations, time_horizon_days, random_seed)
    metrics   = _compute_metrics(pnl, confidence_level, num_iterations)
    histogram = _build_histogram(pnl, num_histogram_bins)
    return metrics, histogram
