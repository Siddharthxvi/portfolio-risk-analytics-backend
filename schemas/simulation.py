from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime

class RiskMetricResponse(BaseModel):
    metric_type: str
    metric_value: float
    confidence_level: Optional[float] = None
    
    class Config:
        from_attributes = True

class SimulationRunCreate(BaseModel):
    portfolio_id: int
    scenario_id: int
    num_simulations: int = Field(default=10000, ge=1000, le=100000)
    time_horizon_days: int = Field(default=252)
    random_seed: int = Field(default=42)

    @field_validator('time_horizon_days')
    @classmethod
    def validate_horizon(cls, v):
        if v not in (1, 10, 252):
            raise ValueError('Time horizon must be 1, 10, or 252')
        return v

class SimulationRunResponse(BaseModel):
    run_id: int
    portfolio_id: int
    scenario_id: int
    status: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    risk_metrics: List[RiskMetricResponse] = []
    
    class Config:
        from_attributes = True
