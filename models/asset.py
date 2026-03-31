from sqlalchemy import Column, Integer, String, Float, Date, BigInteger, ForeignKey
from sqlalchemy.orm import relationship
from core.database import Base

class AssetType(Base):
    __tablename__ = "asset_type"

    type_id = Column(Integer, primary_key=True, index=True)
    type_name = Column(String, nullable=False)
    description = Column(String)
    risk_category = Column(String)

    assets = relationship("Asset", back_populates="asset_type")


class Asset(Base):
    __tablename__ = "asset"

    asset_id = Column(Integer, primary_key=True, index=True)
    type_id = Column(Integer, ForeignKey("asset_type.type_id"))
    ticker = Column(String, unique=True, nullable=False)
    asset_name = Column(String, nullable=False)
    currency = Column(String)
    exchange = Column(String)
    sector = Column(String)
    country = Column(String)
    
    base_price = Column(Float, nullable=False, default=1.0)
    annual_volatility = Column(Float, nullable=False, default=0.1)
    annual_return = Column(Float, nullable=False, default=0.05)

    asset_type = relationship("AssetType", back_populates="assets")
    market_data = relationship("MarketData", back_populates="asset")
    portfolios = relationship("PortfolioAsset", back_populates="asset")

    type_disc = Column(String)
    __mapper_args__ = {
        'polymorphic_on': type_disc,
        'polymorphic_identity': 'asset'
    }


class Equity(Asset):
    __tablename__ = "equity"
    asset_id = Column(Integer, ForeignKey('asset.asset_id'), primary_key=True)
    dividend_yield = Column(Float)
    market_cap_cat = Column(String)
    index_membership = Column(String)

    __mapper_args__ = {
        'polymorphic_identity': 'equity',
    }


class Bond(Asset):
    __tablename__ = "bond"
    asset_id = Column(Integer, ForeignKey('asset.asset_id'), primary_key=True)
    maturity_date = Column(Date)
    coupon_rate = Column(Float)
    bond_type = Column(String)
    credit_rating = Column(String)

    __mapper_args__ = {
        'polymorphic_identity': 'bond',
    }


class Derivative(Asset):
    __tablename__ = "derivative"
    asset_id = Column(Integer, ForeignKey('asset.asset_id'), primary_key=True)
    underlying_asset_id = Column(Integer, ForeignKey('asset.asset_id'))
    expiry_date = Column(Date)
    contract_type = Column(String)
    strike_price = Column(Float)

    __mapper_args__ = {
        'polymorphic_identity': 'derivative',
        'inherit_condition': asset_id == Asset.asset_id
    }


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
