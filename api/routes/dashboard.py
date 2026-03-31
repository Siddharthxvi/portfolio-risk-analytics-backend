from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import Optional
import numpy as np
import datetime

from core.database import get_db
from core.auth import require_role
from models.portfolio import Portfolio
from models.simulation import SimulationRun, RiskMetric
from core.simulation.engine import run_gbm
from core.simulation.metrics import compute_metrics

router = APIRouter()
ReadAccess = Depends(require_role("ADMIN", "ANALYST", "VIEWER"))


@router.get("/{portfolio_id}", dependencies=[ReadAccess])
def get_dashboard_summary(portfolio_id: int, db: Session = Depends(get_db)):
    """
    Aggregate dashboard endpoint — returns in a single response:
      1. latest_metrics   → latest completed run's VaR / ES / Volatility / MaxDrawdown
      2. histogram        → latest run's histogram (for Risk Distribution chart)
      3. holdings         → weights + per-asset marginal risk contribution
      4. runs_summary     → total / completed / failed counts + last run timestamp
    """
    port = db.query(Portfolio).filter(Portfolio.portfolio_id == portfolio_id).first()
    if not port:
        raise HTTPException(status_code=404, detail="Portfolio not found")

    # ── 1. Latest completed run ──────────────────────────────────────────────
    latest_run = (
        db.query(SimulationRun)
        .filter(
            SimulationRun.portfolio_id == portfolio_id,
            SimulationRun.status == "completed",
        )
        .order_by(desc(SimulationRun.completed_at))
        .first()
    )

    latest_metrics = {}
    histogram = None
    sharpe_ratio = None

    if latest_run:
        for m in latest_run.risk_metrics:
            latest_metrics[m.metric_type] = m.metric_value
        histogram = latest_run.histogram_data

        # Sharpe = (mean_pnl / std) * sqrt(252) derived from histogram if available
        if histogram and histogram.get("mean_pnl") is not None:
            mean_pnl = histogram["mean_pnl"]
            # Approximate std from bin range
            pnl_range = histogram.get("pnl_max", 0) - histogram.get("pnl_min", 0)
            approx_std = pnl_range / 6  # ~6 sigma range heuristic
            if approx_std > 0:
                daily_sharpe = mean_pnl / approx_std
                sharpe_ratio = round(daily_sharpe * (252 ** 0.5), 4)

    # ── 2. Holdings + Marginal Risk Contribution ─────────────────────────────
    holdings = []
    has_run_data = latest_run and latest_metrics

    for pa in port.assets:
        asset = pa.asset
        asset_name = asset.asset_name if asset else f"Asset #{pa.asset_id}"
        ticker = asset.ticker if asset else "N/A"
        base_price = asset.base_price if asset else 0.0
        position_value = pa.weight * base_price * pa.quantity

        # Marginal VaR: run a mini 1000-iter simulation with just this asset scaled
        marginal_var = None
        if has_run_data and asset and latest_run:
            try:
                single_asset = [{
                    "asset_type": asset.asset_type.type_name if asset.asset_type else "equity",
                    "weight": 1.0,
                    "quantity": pa.quantity,
                    "base_price": base_price,
                    "annual_volatility": asset.annual_volatility,
                    "annual_return": asset.annual_return,
                }]
                scen = latest_run.scenario
                scenario_payload = {
                    "interest_rate_shock_bps": scen.interest_rate_shock_bps,
                    "volatility_multiplier": scen.volatility_multiplier,
                    "equity_shock_pct": scen.equity_shock_pct,
                }
                pnl = run_gbm(
                    single_asset, scenario_payload,
                    num_iterations=1000,
                    time_horizon_days=latest_run.time_horizon_days,
                    random_seed=latest_run.random_seed,
                )
                m = compute_metrics(pnl, 0.95, 1000)
                marginal_var = round(pa.weight * m.get("VaR_95", 0.0), 4)
            except Exception:
                marginal_var = None

        holdings.append({
            "asset_id": pa.asset_id,
            "asset_name": asset_name,
            "ticker": ticker,
            "weight": round(pa.weight, 4),
            "quantity": pa.quantity,
            "base_price": base_price,
            "position_value": round(position_value, 2),
            "marginal_var_95": marginal_var,
        })

    # ── 3. Runs summary counts ────────────────────────────────────────────────
    all_runs = db.query(SimulationRun).filter(SimulationRun.portfolio_id == portfolio_id).all()
    runs_summary = {
        "total": len(all_runs),
        "completed": sum(1 for r in all_runs if r.status == "completed"),
        "running":   sum(1 for r in all_runs if r.status == "running"),
        "failed":    sum(1 for r in all_runs if r.status == "failed"),
        "last_run_at": latest_run.completed_at.isoformat() if latest_run and latest_run.completed_at else None,
        "last_run_id": latest_run.run_id if latest_run else None,
        "last_run_type": latest_run.run_type if latest_run else None,
    }

    return {
        "portfolio_id": portfolio_id,
        "portfolio_name": port.name,
        "base_currency": port.base_currency,
        "status": port.status,
        "latest_metrics": latest_metrics,
        "sharpe_ratio": sharpe_ratio,
        "histogram": histogram,
        "holdings": holdings,
        "runs_summary": runs_summary,
    }


@router.get("/{portfolio_id}/nav-history", dependencies=[ReadAccess])
def get_nav_history(
    portfolio_id: int,
    period: str = Query("1M", pattern="^(1D|1W|1M|3M|1Y)$"),
    db: Session = Depends(get_db),
):
    """
    Synthetic NAV time-series derived from the portfolio's simulation runs.
    For each completed run ordered by timestamp, we compute portfolio NAV =
    sum(weight * base_price * quantity) and return it as a time-series.

    This gives the frontend a real data-backed chart, anchored to actual
    simulation timestamps, for the Performance History chart.
    """
    port = db.query(Portfolio).filter(Portfolio.portfolio_id == portfolio_id).first()
    if not port:
        raise HTTPException(status_code=404, detail="Portfolio not found")

    period_days = {"1D": 1, "1W": 7, "1M": 30, "3M": 90, "1Y": 365}
    cutoff = datetime.datetime.utcnow() - datetime.timedelta(days=period_days[period])

    runs = (
        db.query(SimulationRun)
        .filter(
            SimulationRun.portfolio_id == portfolio_id,
            SimulationRun.status == "completed",
            SimulationRun.completed_at >= cutoff,
        )
        .order_by(SimulationRun.completed_at)
        .all()
    )

    # Baseline NAV from current holdings
    baseline_nav = sum(
        pa.weight * (pa.asset.base_price if pa.asset else 0.0) * pa.quantity
        for pa in port.assets
    )

    if not runs:
        # Return a flat baseline single point so frontend doesn't crash
        return {
            "portfolio_id": portfolio_id,
            "period": period,
            "baseline_nav": round(baseline_nav, 2),
            "series": [{"timestamp": datetime.datetime.utcnow().isoformat(), "nav": round(baseline_nav, 2), "run_id": None}],
        }

    series = []
    for run in runs:
        # Adjust NAV by mean_pnl from histogram (actual derived value from real simulation)
        nav = baseline_nav
        if run.histogram_data and run.histogram_data.get("mean_pnl") is not None:
            nav = baseline_nav + run.histogram_data["mean_pnl"]

        series.append({
            "timestamp": run.completed_at.isoformat(),
            "nav": round(nav, 2),
            "run_id": run.run_id,
        })

    # Compute period return %
    period_return_pct = None
    if len(series) >= 2:
        period_return_pct = round((series[-1]["nav"] - series[0]["nav"]) / series[0]["nav"] * 100, 4)

    return {
        "portfolio_id": portfolio_id,
        "period": period,
        "baseline_nav": round(baseline_nav, 2),
        "period_return_pct": period_return_pct,
        "series": series,
    }
