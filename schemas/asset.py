from pydantic import BaseModel, Field
from typing import Optional

class AssetBase(BaseModel):
    ticker: str
    asset_name: str
    currency: str
    exchange: str = "N/A"
    sector: str = "N/A"
    country: str = "N/A"
    base_price: float = Field(..., gt=0)
    annual_volatility: float = Field(..., gt=0)
    annual_return: float

class AssetUpdate(BaseModel):
    ticker: Optional[str] = None
    asset_name: Optional[str] = None
    currency: Optional[str] = None
    exchange: Optional[str] = None
    sector: Optional[str] = None
    country: Optional[str] = None
    base_price: Optional[float] = Field(None, gt=0)
    annual_volatility: Optional[float] = Field(None, gt=0)
    annual_return: Optional[float] = None

class AssetCreate(AssetBase):
    type_name: str = "equity" # 'equity', 'bond', 'derivative', etc.

class AssetResponse(AssetBase):
    asset_id: int
    type_id: Optional[int] = None
    
    class Config:
        from_attributes = True
