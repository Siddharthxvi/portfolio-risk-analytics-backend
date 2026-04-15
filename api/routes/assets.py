from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from core.database import get_db
from core.auth import require_role
from models.asset import Asset
from schemas.asset import AssetCreate, AssetResponse, AssetUpdate

router = APIRouter()

ReadAccess  = Depends(require_role("ADMIN", "ANALYST", "VIEWER"))
WriteAccess = Depends(require_role("ADMIN", "ANALYST"))

import yfinance as yf
import numpy as np

@router.get("/fetch-data/{ticker}")
def fetch_asset_data(ticker: str):
    """
    Fetch asset metadata and calculate risk metrics from Yahoo Finance.
    Public endpoint to assist in asset creation.
    """
    try:
        tick = yf.Ticker(ticker)
        info = tick.info
        
        # Multi-stage check for ticker validity
        if not info or not any(k in info for k in ['regularMarketPrice', 'currentPrice', 'previousClose']):
            # Fallback check
            hist_test = tick.history(period="1d")
            if hist_test.empty:
                raise HTTPException(status_code=404, detail="Invalid ticker or data unavailable")

        hist = tick.history(period="1y")
        if hist.empty:
            raise HTTPException(status_code=404, detail="Historical data unavailable for metric calculations")

        # Calculate annualized metrics using pandas/numpy
        daily_returns = hist['Close'].pct_change().dropna()
        if daily_returns.empty:
            annual_return = 0.0
            annual_volatility = 0.0
        else:
            # Assumes 252 trading days
            annual_return = float(daily_returns.mean() * 252)
            annual_volatility = float(daily_returns.std() * np.sqrt(252))

        # Extract metadata
        base_price = info.get('currentPrice') or info.get('regularMarketPrice') or info.get('previousClose') or hist['Close'].iloc[-1]
        asset_name = info.get('longName') or info.get('shortName') or ticker.upper()
        currency = info.get('currency', 'USD')
        
        return {
            "ticker": ticker.upper(),
            "asset_name": asset_name,
            "currency": currency,
            "exchange": info.get('exchange', 'N/A'),
            "sector": info.get('sector', 'N/A'),
            "country": info.get('country', 'N/A'),
            "base_price": round(float(base_price), 2),
            "annual_volatility": round(float(annual_volatility), 4),
            "annual_return": round(float(annual_return), 4),
            "type_name": "equity"  # Default type for Yahoo Finance fetches
        }
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=400, detail=f"Failed to fetch data: {str(e)}")


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


@router.put("/{asset_id}", response_model=AssetResponse, dependencies=[WriteAccess])
def update_asset(asset_id: int, asset_in: AssetUpdate, db: Session = Depends(get_db)):
    asset = db.query(Asset).filter(Asset.asset_id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    update_data = asset_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(asset, field, value)

    db.commit()
    db.refresh(asset)
    return asset


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
