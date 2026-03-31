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

from typing import Literal

class AssetInput(BaseModel):
    asset_name: str
    asset_type: Literal['equity', 'bond', 'derivative', 'commodity']
    base_price: float = Field(gt=0, description="Reference price used in simulation")
    annual_volatility: float = Field(gt=0, description="Annualised standard deviation, e.g. 0.25 = 25%")
    annual_return: float = Field(description="Expected annualised return")
    weight: float = Field(gt=0, le=1.0, description="Portfolio allocation fraction")
    quantity: float = Field(gt=0, description="Number of units held")

class ScenarioInput(BaseModel):
    interest_rate_shock_bps: int = Field(description="Basis points; positive = rise, negative = cut")
    volatility_multiplier: float = Field(gt=0, description="Applied to each asset's volatility")
    equity_shock_pct: float = Field(ge=-1.0, le=1.0, description="Additive shock to equity asset returns")

class AdHocSimulationRequest(BaseModel):
    portfolio_assets: List[AssetInput]
    scenario: ScenarioInput
    num_iterations: int = Field(ge=1000, le=100000, description="Number of independent MC paths")
    time_horizon_days: int = Field(description="Between 1 and 252 (inclusive) trading days")
    random_seed: int = Field(description="Numpy RNG seed for reproducibility")

    @field_validator('time_horizon_days')
    @classmethod
    def validate_time_horizon(cls, v: int) -> int:
        if not (1 <= v <= 252):
            raise ValueError("time_horizon_days must be between 1 and 252 (inclusive).")
        return v

    @field_validator('portfolio_assets')
    @classmethod
    def validate_weights(cls, assets: List[AssetInput]) -> List[AssetInput]:
        total_weight = sum(a.weight for a in assets)
        if abs(total_weight - 1.0) > 0.001:
            raise ValueError(f"Portfolio weights must sum to 1.0. Found: {total_weight:.4f}")
        return assets
