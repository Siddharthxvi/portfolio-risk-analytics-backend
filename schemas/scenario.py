from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class ScenarioBase(BaseModel):
    name: str
    description: Optional[str] = None
    interest_rate_shock_bps: int
    volatility_multiplier: float = Field(..., gt=0)
    equity_shock_pct: float = Field(..., ge=-1.0, le=1.0)

class ScenarioCreate(ScenarioBase):
    pass

class ScenarioUpdate(BaseModel):
    """All fields optional — only provided fields are updated."""
    name: Optional[str] = None
    description: Optional[str] = None
    interest_rate_shock_bps: Optional[int] = None
    volatility_multiplier: Optional[float] = Field(None, gt=0)
    equity_shock_pct: Optional[float] = Field(None, ge=-1.0, le=1.0)
    is_active: Optional[bool] = None

class ScenarioResponse(ScenarioBase):
    scenario_id: int
    created_at: datetime
    is_active: bool
    
    class Config:
        from_attributes = True
