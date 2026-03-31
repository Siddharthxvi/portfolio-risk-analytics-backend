from sqlalchemy import Column, Integer, String, Float, Date, BigInteger, ForeignKey, CHAR, Text
from sqlalchemy.orm import relationship
from core.database import Base

class AssetType(Base):
    __tablename__ = "asset_type"

    type_id = Column(Integer, primary_key=True, index=True)
    type_name = Column(String(20))
    description = Column(Text)
    risk_category = Column(String(20))

    assets = relationship("Asset", back_populates="asset_type")


class Asset(Base):
    __tablename__ = "asset"

    asset_id = Column(Integer, primary_key=True, index=True)
    type_id = Column(Integer, ForeignKey("asset_type.type_id"))
    ticker = Column(String(20), unique=True, nullable=False)
    asset_name = Column(String(100), nullable=False)
    currency = Column(CHAR(3), nullable=False)
    exchange = Column(String(50))
    sector = Column(String(50))
    country = Column(String(50))
    
    base_price = Column(Float, nullable=False)
    annual_volatility = Column(Float, nullable=False)
    annual_return = Column(Float, nullable=False)

    asset_type = relationship("AssetType", back_populates="assets")
    market_data = relationship("MarketData", back_populates="asset")
    portfolios = relationship("PortfolioAsset", back_populates="asset")

    equity_details = relationship("Equity", back_populates="core_asset", uselist=False)
    bond_details = relationship("Bond", back_populates="core_asset", uselist=False)
    derivative_details = relationship("Derivative", foreign_keys="[Derivative.asset_id]", back_populates="core_asset", uselist=False)

class Equity(Base):
    __tablename__ = "equity"
    asset_id = Column(Integer, ForeignKey('asset.asset_id'), primary_key=True)
    dividend_yield = Column(Float)
    market_cap_cat = Column(String(20))
    index_membership = Column(String(50))

    core_asset = relationship("Asset", back_populates="equity_details")

class Bond(Base):
    __tablename__ = "bond"
    asset_id = Column(Integer, ForeignKey('asset.asset_id'), primary_key=True)
    maturity_date = Column(Date)
    coupon_rate = Column(Float)
    bond_type = Column(String(50))
    credit_rating = Column(String(20))

    core_asset = relationship("Asset", back_populates="bond_details")

class Derivative(Base):
    __tablename__ = "derivative"
    asset_id = Column(Integer, ForeignKey('asset.asset_id'), primary_key=True)
    underlying_asset_id = Column(Integer, ForeignKey('asset.asset_id'))
    expiry_date = Column(Date)
    contract_type = Column(String(20))
    strike_price = Column(Float)

    core_asset = relationship("Asset", foreign_keys=[asset_id], back_populates="derivative_details")

class MarketData(Base):
    __tablename__ = "market_data"
    data_id = Column(Integer, primary_key=True, index=True)
    asset_id = Column(Integer, ForeignKey("asset.asset_id"))
    trading_date = Column(Date, nullable=False)
    open_price = Column(Float)
    close_price = Column(Float, nullable=False)
    high_price = Column(Float)
    low_price = Column(Float)
    volume = Column(BigInteger)
    adjusted_close = Column(Float)

    asset = relationship("Asset", back_populates="market_data")
