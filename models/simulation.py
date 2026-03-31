from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from core.database import Base

class Scenario(Base):
    __tablename__ = "scenario"

    scenario_id = Column(Integer, primary_key=True, index=True)
    created_by = Column(Integer, ForeignKey("users.user_id"))
    name = Column(String, unique=True, nullable=False)
    description = Column(String)
    interest_rate_shock_bps = Column(Integer, nullable=False)
    volatility_multiplier = Column(Float, nullable=False)
    equity_shock_pct = Column(Float, nullable=False)
    created_at = Column(DateTime, default=func.now())
    is_active = Column(Boolean, default=True)

    creator = relationship("User", back_populates="scenarios")
    simulation_runs = relationship("SimulationRun", back_populates="scenario")


class SimulationRun(Base):
    __tablename__ = "simulation_run"

    run_id = Column(Integer, primary_key=True, index=True)
    portfolio_id = Column(Integer, ForeignKey("portfolio.portfolio_id"), nullable=False)
    scenario_id = Column(Integer, ForeignKey("scenario.scenario_id"), nullable=False)
    initiated_by = Column(Integer, ForeignKey("users.user_id"))
    run_type = Column(String, nullable=False, default="monte_carlo")
    status = Column(String, nullable=False, default="pending")
    num_simulations = Column(Integer, nullable=False, default=10000)
    started_at = Column(DateTime, default=func.now())
    completed_at = Column(DateTime, nullable=True)
    execution_time_ms = Column(Float)
    random_seed = Column(Integer, nullable=False)
    time_horizon_days = Column(Integer, nullable=False)
    run_timestamp = Column(DateTime, nullable=False, default=func.now())
    histogram_data = Column(JSON, nullable=True)

    portfolio = relationship("Portfolio", back_populates="simulation_runs")
    scenario = relationship("Scenario", back_populates="simulation_runs")
    initiator = relationship("User", back_populates="simulation_runs")
    risk_metrics = relationship("RiskMetric", back_populates="simulation_run", cascade="all, delete-orphan")
    reports = relationship("Report", back_populates="simulation_run")


class RiskMetric(Base):
    __tablename__ = "risk_metric"

    run_id = Column(Integer, ForeignKey("simulation_run.run_id"), primary_key=True)
    metric_type = Column(String, primary_key=True)
    metric_value = Column(Float, nullable=False)
    confidence_level = Column(Float, nullable=True)
    computed_at = Column(DateTime, default=func.now())

    simulation_run = relationship("SimulationRun", back_populates="risk_metrics")
