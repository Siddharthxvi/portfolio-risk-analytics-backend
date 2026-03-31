from pydantic import BaseModel, Field
from typing import List, Optional
from .asset import AssetResponse

class PortfolioAssetBase(BaseModel):
    asset_id: int
    weight: float = Field(..., gt=0, le=1.0)
    quantity: float = Field(..., gt=0)

class PortfolioAssetCreate(PortfolioAssetBase):
    pass

class PortfolioAssetResponse(PortfolioAssetBase):
    asset: Optional[AssetResponse] = None
    
    class Config:
        from_attributes = True

class PortfolioBase(BaseModel):
    name: str
    description: Optional[str] = None
    base_currency: str = "USD"

class PortfolioCreate(PortfolioBase):
    assets: List[PortfolioAssetCreate] = []

class PortfolioUpdate(BaseModel):
    """Update portfolio metadata and/or replace its asset allocation."""
    name: Optional[str] = None
    description: Optional[str] = None
    base_currency: Optional[str] = None
    status: Optional[str] = None
    assets: Optional[List[PortfolioAssetCreate]] = None  # if provided, replaces all assets

class PortfolioResponse(PortfolioBase):
    portfolio_id: int
    assets: List[PortfolioAssetResponse] = []
    
    class Config:
        from_attributes = True
