from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_

from core.database import get_db
from core.auth import require_role
from models.asset import Asset
from models.portfolio import Portfolio
from models.simulation import Scenario

router = APIRouter()
ReadAccess = Depends(require_role("ADMIN", "ANALYST", "VIEWER"))

@router.get("/")
def global_search(
    q: str = Query(..., min_length=1, description="Search query string"),
    db: Session = Depends(get_db),
    current_user: dict = ReadAccess
):
    """
    Unified omni-search endpoint. 
    Searches across Assets, Portfolios, and Scenarios using a single query string.
    """
    search_term = f"%{q}%"
    
    # 1. Search Assets
    assets = db.query(Asset).filter(
        or_(
            Asset.asset_name.ilike(search_term),
            Asset.ticker.ilike(search_term),
            Asset.sector.ilike(search_term)
        )
    ).limit(5).all()

    # 2. Search Portfolios
    portfolios = db.query(Portfolio).filter(
        or_(
            Portfolio.name.ilike(search_term),
            Portfolio.description.ilike(search_term)
        )
    ).limit(5).all()

    # 3. Search Scenarios
    scenarios = db.query(Scenario).filter(
        or_(
            Scenario.name.ilike(search_term),
            Scenario.description.ilike(search_term)
        )
    ).limit(5).all()

    # Format the unified response
    return {
        "query": q,
        "results": {
            "assets": [
                {"id": a.asset_id, "name": a.asset_name, "ticker": a.ticker, "type": "asset"}
                for a in assets
            ],
            "portfolios": [
                {"id": p.portfolio_id, "name": p.name, "description": p.description, "type": "portfolio"}
                for p in portfolios
            ],
            "scenarios": [
                {"id": s.scenario_id, "name": s.name, "description": s.description, "type": "scenario"}
                for s in scenarios
            ]
        }
    }
