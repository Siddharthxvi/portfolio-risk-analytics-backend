from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

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
    metric_type: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    query = (
        db.query(
            Portfolio.name.label("portfolio_name"),
            Scenario.name.label("scenario_name"),
            RiskMetric.metric_type,
            RiskMetric.metric_value,
        )
        .join(Portfolio, SimulationRun.portfolio_id == Portfolio.portfolio_id)
        .join(Scenario, SimulationRun.scenario_id == Scenario.scenario_id)
        .join(RiskMetric, SimulationRun.run_id == RiskMetric.run_id)
        .filter(SimulationRun.status == "completed")
    )

    if portfolio_ids:
        query = query.filter(SimulationRun.portfolio_id.in_(portfolio_ids))
    if scenario_ids:
        query = query.filter(SimulationRun.scenario_id.in_(scenario_ids))
    if metric_type:
        query = query.filter(RiskMetric.metric_type == metric_type)

    results = query.all()
    return [
        {
            "portfolio": r.portfolio_name,
            "scenario": r.scenario_name,
            "metric_type": r.metric_type,
            "metric_value": r.metric_value,
        }
        for r in results
    ]
