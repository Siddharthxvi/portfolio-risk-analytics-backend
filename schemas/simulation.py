from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Literal, Dict
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
    num_simulations: Optional[int] = Field(default=None, ge=1, le=10000)
    time_horizon_days: Optional[int] = Field(default=None)
    random_seed: int = Field(default=42)
    simulation_type: Literal['monte_carlo', 'historical', 'parametric'] = 'monte_carlo'
    confidence_level: Optional[Literal[0.90, 0.95, 0.99]] = None

    @field_validator('time_horizon_days')
    @classmethod
    def validate_horizon(cls, v):
        if v is not None and v not in (1, 10, 252):
            raise ValueError('Time horizon must be 1, 10, or 252')
        return v

class SimulationRunUpdate(BaseModel):
    num_simulations: Optional[int] = Field(None, ge=1, le=10000)
    time_horizon_days: Optional[int] = Field(None)
    random_seed: Optional[int] = None
    simulation_type: Optional[Literal['monte_carlo', 'historical', 'parametric']] = None
    confidence_level: Optional[Literal[0.90, 0.95, 0.99]] = None
    status: str = "pending"

class HistogramResponse(BaseModel):
    bin_edges: List[float]
    counts: List[int]
    bin_width: float
    pnl_min: float
    pnl_max: float
    mean_pnl: float

class SimulationRunResponse(BaseModel):
    run_id: int
    portfolio_id: int
    scenario_id: int
    status: str
    run_type: str
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    risk_metrics: List[RiskMetricResponse] = []
    histogram_data: Optional[HistogramResponse] = None

    class Config:
        from_attributes = True

class AdHocSimulationResponse(BaseModel):
    metrics: Dict[str, float]
    histogram: HistogramResponse

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
    num_iterations: Optional[int] = Field(default=None, ge=1, le=10000, description="Number of independent MC paths")
    time_horizon_days: Optional[int] = Field(default=None, description="Between 1 and 252 (inclusive) trading days")
    random_seed: int = Field(default=42, description="Numpy RNG seed for reproducibility")
    simulation_type: Literal['monte_carlo', 'historical', 'parametric'] = 'monte_carlo'
    confidence_level: Optional[Literal[0.90, 0.95, 0.99]] = None

    @field_validator('time_horizon_days')
    @classmethod
    def validate_time_horizon(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and not (1 <= v <= 252):
            raise ValueError("time_horizon_days must be between 1 and 252 (inclusive).")
        return v

    @field_validator('portfolio_assets')
    @classmethod
    def validate_weights(cls, assets: List[AssetInput]) -> List[AssetInput]:
        total_weight = sum(a.weight for a in assets)
        if abs(total_weight - 1.0) > 0.001:
            raise ValueError(f"Portfolio weights must sum to 1.0. Found: {total_weight:.4f}")
        return assets


