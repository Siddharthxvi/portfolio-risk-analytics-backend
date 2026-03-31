import numpy as np
from typing import Dict, Any, Tuple

def compute_metrics(pnl: np.ndarray, confidence_level: float, num_iterations: int) -> Dict[str, float]:
    """Derive strict quantitative metrics from P&L array."""
    tail_pct = 1.0 - confidence_level
    pnl_sorted = np.sort(pnl)

    idx_tail = max(1, int(num_iterations * tail_pct))
    idx_99 = max(1, int(num_iterations * 0.01))

    # Calculate base risk measures
    var_cl = float(-pnl_sorted[idx_tail])
    var_99 = float(-pnl_sorted[idx_99])
    
    # Expected Shortfall: mean of losses that exceed VaR
    es_cl = float(-np.mean(pnl_sorted[:idx_tail]))

    total_value = float(np.sum(np.abs(pnl)) / num_iterations)
    volatility = float(np.std(pnl) / total_value) if total_value > 0 else 0.0
    max_drawdown = float(-pnl.min())

    # Constraints per DB triggers
    var_cl = max(0.0, var_cl)
    var_99 = max(var_cl, var_99)   # VaR_99 >= VaR_CL
    es_cl = max(var_cl, es_cl)     # ES >= VaR

    cl_label = str(int(confidence_level * 100))
    return {
        f'VaR_{cl_label}': var_cl,
        'VaR_99':          var_99,
        f'ES_{cl_label}':  es_cl,
        'volatility':      max(0.0, volatility),
        'max_drawdown':    max(0.0, max_drawdown)
    }

def build_histogram(pnl: np.ndarray, num_bins: int = 60) -> Dict[str, Any]:
    """Generates charting structures for P&L binning."""
    counts, bin_edges = np.histogram(pnl, bins=num_bins)
    return {
        "bin_edges": [round(float(e), 4) for e in bin_edges],
        "counts": [int(c) for c in counts],
        "bin_width": round(float(bin_edges[1] - bin_edges[0]), 4),
        "pnl_min": round(float(pnl.min()), 4),
        "pnl_max": round(float(pnl.max()), 4),
        "mean_pnl": round(float(pnl.mean()), 4),
    }
