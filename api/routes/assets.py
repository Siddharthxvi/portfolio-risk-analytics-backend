from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from core.database import get_db
from core.auth import require_role
from models.asset import Asset
from schemas.asset import AssetCreate, AssetResponse

router = APIRouter()

ReadAccess  = Depends(require_role("ADMIN", "ANALYST", "VIEWER"))
WriteAccess = Depends(require_role("ADMIN", "ANALYST"))


@router.get("/", response_model=List[AssetResponse], dependencies=[ReadAccess])
def get_assets(db: Session = Depends(get_db)):
    return db.query(Asset).all()


@router.get("/{asset_id}", response_model=AssetResponse, dependencies=[ReadAccess])
def get_asset(asset_id: int, db: Session = Depends(get_db)):
    asset = db.query(Asset).filter(Asset.asset_id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    return asset


@router.post("/", response_model=AssetResponse, dependencies=[WriteAccess])
def create_asset(asset: AssetCreate, db: Session = Depends(get_db)):
    db_asset = Asset(
        ticker=asset.ticker,
        asset_name=asset.asset_name,
        currency=asset.currency,
        base_price=asset.base_price,
        annual_volatility=asset.annual_volatility,
        annual_return=asset.annual_return,
    )
    db.add(db_asset)
    db.commit()
    db.refresh(db_asset)
    return db_asset


@router.delete("/{asset_id}", dependencies=[WriteAccess])
def delete_asset(asset_id: int, db: Session = Depends(get_db)):
    asset = db.query(Asset).filter(Asset.asset_id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    if asset.portfolios:
        raise HTTPException(status_code=400, detail="Asset is used in active portfolios")
    db.delete(asset)
    db.commit()
    return {"detail": "Asset deleted"}
