from pydantic import BaseModel, ConfigDict, Field

class SettingsUpdate(BaseModel):
    default_iterations: int = Field(default=10000, ge=100, le=10000)
    default_horizon_days: int = Field(default=252, ge=1)
    default_confidence_level: float = Field(default=0.95, ge=0.5, lt=1.0)
    risk_threshold_pct: float = Field(default=0.10, ge=0.0, le=1.0)

    model_config = ConfigDict(from_attributes=True)

class SettingsResponse(SettingsUpdate):
    user_id: int
