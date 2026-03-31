from sqlalchemy import Column, Integer, String, Float, DateTime, Date, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from core.database import Base

class Portfolio(Base):
    __tablename__ = "portfolio"

    portfolio_id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.user_id"))
    name = Column(String, nullable=False)
    description = Column(String)
    base_currency = Column(String)
    created_at = Column(DateTime, default=func.now())
    status = Column(String, default="active")

    owner = relationship("User", back_populates="portfolios")
    assets = relationship("PortfolioAsset", back_populates="portfolio", cascade="all, delete-orphan")
    benchmarks = relationship("PortfolioBenchmark", back_populates="portfolio")
    simulation_runs = relationship("SimulationRun", back_populates="portfolio")


class PortfolioAsset(Base):
    __tablename__ = "portfolio_asset"

    portfolio_id = Column(Integer, ForeignKey("portfolio.portfolio_id"), primary_key=True)
    asset_id = Column(Integer, ForeignKey("asset.asset_id"), primary_key=True)
    weight = Column(Float, nullable=False)
    quantity = Column(Float, nullable=False)
    purchase_price = Column(Float)
    added_date = Column(Date, default=func.current_date())
    removed_date = Column(Date, nullable=True)

    portfolio = relationship("Portfolio", back_populates="assets")
    asset = relationship("Asset", back_populates="portfolios")


class Benchmark(Base):
    __tablename__ = "benchmark"

    benchmark_id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    description = Column(String)
    benchmark_type = Column(String)
    base_date = Column(Date)
    currency = Column(String)

    portfolios = relationship("PortfolioBenchmark", back_populates="benchmark")


class PortfolioBenchmark(Base):
    __tablename__ = "portfolio_benchmark"

    portfolio_id = Column(Integer, ForeignKey("portfolio.portfolio_id"), primary_key=True)
    benchmark_id = Column(Integer, ForeignKey("benchmark.benchmark_id"), primary_key=True)
    assigned_at = Column(Date, default=func.current_date())

    portfolio = relationship("Portfolio", back_populates="benchmarks")
    benchmark = relationship("Benchmark", back_populates="portfolios")
