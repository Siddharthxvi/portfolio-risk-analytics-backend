from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from core.database import get_db
from core.auth import require_role, get_current_user
from models.portfolio import Portfolio, PortfolioAsset
from schemas.portfolio import PortfolioCreate, PortfolioResponse, PortfolioUpdate, PortfolioAssetCreate
from sqlalchemy.exc import IntegrityError

router = APIRouter()

ReadAccess  = Depends(require_role("ADMIN", "ANALYST", "VIEWER"))
WriteAccess = Depends(require_role("ADMIN", "ANALYST"))


@router.get("/", response_model=List[PortfolioResponse], dependencies=[ReadAccess])
def get_portfolios(db: Session = Depends(get_db)):
    return db.query(Portfolio).all()


@router.get("/{portfolio_id}", response_model=PortfolioResponse, dependencies=[ReadAccess])
def get_portfolio(portfolio_id: int, db: Session = Depends(get_db)):
    port = db.query(Portfolio).filter(Portfolio.portfolio_id == portfolio_id).first()
    if not port:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    return port


@router.post("/", response_model=PortfolioResponse)
def create_portfolio(
    portfolio: PortfolioCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role("ADMIN", "ANALYST")),
):
    db_port = Portfolio(
        name=portfolio.name,
        description=portfolio.description,
        base_currency=portfolio.base_currency,
        owner_id=current_user["user_id"],   # use the logged-in user's ID
    )
    db.add(db_port)
    db.flush()

    for a in portfolio.assets:
        pa = PortfolioAsset(
            portfolio_id=db_port.portfolio_id,
            asset_id=a.asset_id,
            weight=a.weight,
            quantity=a.quantity,
        )
        db.add(pa)

    try:
        db.commit()
        db.refresh(db_port)
        return db_port
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e.orig))


@router.put("/{portfolio_id}/assets", dependencies=[WriteAccess])
def update_portfolio_assets(
    portfolio_id: int,
    assets: List[PortfolioAssetCreate],
    db: Session = Depends(get_db)
):
    db_port = db.query(Portfolio).filter(Portfolio.portfolio_id == portfolio_id).first()
    if not db_port:
        raise HTTPException(status_code=404, detail="Portfolio not found")

    db.query(PortfolioAsset).filter(PortfolioAsset.portfolio_id == portfolio_id).delete()
    for a in assets:
        pa = PortfolioAsset(
            portfolio_id=db_port.portfolio_id,
            asset_id=a.asset_id,
            weight=a.weight,
            quantity=a.quantity,
        )
        db.add(pa)

    try:
        db.commit()
        return {"detail": "Portfolio assets updated."}
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e.orig))


@router.put("/{portfolio_id}", response_model=PortfolioResponse)
def update_portfolio(
    portfolio_id: int,
    payload: PortfolioUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role("ADMIN", "ANALYST")),
):
    """
    Edit portfolio metadata (name, description, currency, status)
    and optionally replace the full asset allocation in one request.
    Access: ADMIN, ANALYST
    """
    port = db.query(Portfolio).filter(Portfolio.portfolio_id == portfolio_id).first()
    if not port:
        raise HTTPException(status_code=404, detail="Portfolio not found")

    for field in ("name", "description", "base_currency", "status"):
        value = getattr(payload, field)
        if value is not None:
            setattr(port, field, value)

    if payload.assets is not None:
        db.query(PortfolioAsset).filter(PortfolioAsset.portfolio_id == portfolio_id).delete()
        for a in payload.assets:
            db.add(PortfolioAsset(
                portfolio_id=portfolio_id,
                asset_id=a.asset_id,
                weight=a.weight,
                quantity=a.quantity,
            ))

    try:
        db.commit()
        db.refresh(port)
        return port
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e.orig))


@router.delete("/{portfolio_id}", dependencies=[WriteAccess])
def delete_portfolio(portfolio_id: int, db: Session = Depends(get_db)):
    port = db.query(Portfolio).filter(Portfolio.portfolio_id == portfolio_id).first()
    if not port:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    if port.simulation_runs:
        raise HTTPException(
            status_code=400, detail="Cannot delete a portfolio with associated simulation runs"
        )
    db.delete(port)
    db.commit()
    return {"detail": "Portfolio deleted"}
