from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, asc
from typing import List, Optional, Literal

from core.database import get_db
from core.auth import require_role
from models.simulation import SimulationRun, RiskMetric, Scenario
from models.portfolio import Portfolio

router = APIRouter()
ReadAccess = Depends(require_role("ADMIN", "ANALYST", "VIEWER"))

@router.get("/", dependencies=[ReadAccess])
def compare_runs(
    portfolio_ids: List[int] = Query(None),
    scenario_ids: List[int] = Query(None),
    metric_type: str = Query("VaR_95"),
    group_by: Literal["portfolio", "scenario"] = Query("portfolio"),
    aggregate: Literal["avg", "max", "min"] = Query("avg"),
    sort_order: Literal["asc", "desc"] = Query("desc"),
    db: Session = Depends(get_db),
):
    """
    Advanced Comparison Analytics: Supports aggregation, grouping, sorting and charting structures.
    """
    # Base query for aggregation
    agg_funcs = {
        "avg": func.avg,
        "max": func.max,
        "min": func.min
    }
    agg_val = agg_funcs[aggregate](RiskMetric.metric_value).label("agg_val")
    
    group_col = Portfolio.name.label("group_name") if group_by == "portfolio" else Scenario.name.label("group_name")
    
    query = (
        db.query(group_col, agg_val)
        .select_from(SimulationRun)
        .join(Portfolio, SimulationRun.portfolio_id == Portfolio.portfolio_id)
        .join(Scenario, SimulationRun.scenario_id == Scenario.scenario_id)
        .join(RiskMetric, SimulationRun.run_id == RiskMetric.run_id)
        .filter(SimulationRun.status == "completed")
        .filter(RiskMetric.metric_type == metric_type)
    )

    if portfolio_ids:
        query = query.filter(SimulationRun.portfolio_id.in_(portfolio_ids))
    if scenario_ids:
        query = query.filter(SimulationRun.scenario_id.in_(scenario_ids))

    # Grouping
    group_target = Portfolio.name if group_by == "portfolio" else Scenario.name
    query = query.group_by(group_target)

    # Sorting
    if sort_order == "desc":
        query = query.order_by(desc("agg_val"))
    else:
        query = query.order_by(asc("agg_val"))

    results = query.all()
    
    # ── Formatting for visual charts ──
    labels = [r.group_name for r in results]
    data = [float(r.agg_val) if r.agg_val else 0.0 for r in results]
    
    return {
        "metadata": {
            "metric_type": metric_type,
            "group_by": group_by,
            "aggregate": aggregate,
            "sort_order": sort_order
        },
        "bar_chart": {
            "labels": labels,
            "datasets": [{"label": metric_type, "data": data}]
        },
        "line_chart": {
            "labels": labels,
            "datasets": [{"label": f"{aggregate.upper()} {metric_type}", "data": data}]
        },
        "heatmap": {
            "x_axis": labels,
            "y_axis": [metric_type],
            "values": [data]
        },
        "raw_data": [{"name": l, "value": d} for l, d in zip(labels, data)]
    }
