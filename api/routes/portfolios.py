from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from core.database import get_db
from core.auth import require_role, get_current_user
from models.portfolio import Portfolio, PortfolioAsset
from schemas.portfolio import PortfolioCreate, PortfolioResponse, PortfolioUpdate, PortfolioAssetCreate
from sqlalchemy.exc import IntegrityError
from models.asset import Asset

router = APIRouter()

ReadAccess  = Depends(require_role("ADMIN", "ANALYST", "VIEWER"))
WriteAccess = Depends(require_role("ADMIN", "ANALYST"))

def validate_portfolio_assets(db: Session, assets: List[PortfolioAssetCreate]):
    if not assets:
        return []
    
    asset_ids = [a.asset_id for a in assets]
    db_assets = {a.asset_id: a for a in db.query(Asset).filter(Asset.asset_id.in_(asset_ids)).all()}
    
    for aid in asset_ids:
        if aid not in db_assets:
            raise HTTPException(status_code=400, detail=f"Asset with ID {aid} not found")
            
    asset_values = []
    total_value = 0.0
    for a in assets:
        price = db_assets[a.asset_id].base_price
        val = a.quantity * price
        asset_values.append(val)
        total_value += val
        
    if total_value <= 0:
        raise HTTPException(status_code=400, detail="Total portfolio value must be greater than zero")
        
    resolved_assets = []
    sum_weights = 0.0
    
    for i, a in enumerate(assets):
        calculated_weight = asset_values[i] / total_value
        
        if a.weight is not None:
            # Data Integrity: Validate consistency if both provided
            if abs(a.weight - calculated_weight) > 1e-4:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Inconsistent data: Asset {a.asset_id} weight {a.weight} does not match quantity-based weight {calculated_weight:.4f}"
                )
            weight_to_use = a.weight
        else:
            # Calculate missing weight
            weight_to_use = calculated_weight
            
        sum_weights += weight_to_use
        resolved_assets.append({
            "asset_id": a.asset_id,
            "weight": weight_to_use,
            "quantity": a.quantity
        })
        
    # Final weight sum validation
    if abs(sum_weights - 1.0) > 1e-6:
        raise HTTPException(status_code=400, detail=f"Total weight sum must be 1.0. Current sum: {sum_weights:.6f}")
        
    return resolved_assets


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

    resolved_assets = validate_portfolio_assets(db, portfolio.assets)

    for ra in resolved_assets:
        pa = PortfolioAsset(
            portfolio_id=db_port.portfolio_id,
            asset_id=ra["asset_id"],
            weight=ra["weight"],
            quantity=ra["quantity"],
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
    
    resolved_assets = validate_portfolio_assets(db, assets)
    
    for ra in resolved_assets:
        pa = PortfolioAsset(
            portfolio_id=db_port.portfolio_id,
            asset_id=ra["asset_id"],
            weight=ra["weight"],
            quantity=ra["quantity"],
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
        
        resolved_assets = validate_portfolio_assets(db, payload.assets)
        
        for ra in resolved_assets:
            db.add(PortfolioAsset(
                portfolio_id=portfolio_id,
                asset_id=ra["asset_id"],
                weight=ra["weight"],
                quantity=ra["quantity"],
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
