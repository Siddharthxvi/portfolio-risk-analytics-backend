import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from core.database import engine
from models.user import User
from models.asset import Asset, AssetType
from models.portfolio import Portfolio, PortfolioAsset
from models.simulation import Scenario, SimulationRun, RiskMetric
from services.simulation import run_monte_carlo
from datetime import datetime
import traceback

def seed_db():
    print("Starting database seed...")
    with Session(engine) as db:
        try:
            # 1. User
            user = db.query(User).filter_by(username="demo").first()
            if not user:
                user = User(username="demo", email="demo@example.com", password_hash="hash")
                db.add(user)
                db.flush()
            
            # 2. Asset Types
            types = ["equity", "bond", "commodity", "derivative"]
            db_types = {}
            for t in types:
                atype = db.query(AssetType).filter_by(type_name=t).first()
                if not atype:
                    atype = AssetType(type_name=t)
                    db.add(atype)
                    db.flush()
                db_types[t] = atype

            # 3. Assets
            asset_data = [
                ("AAPL", "Apple Inc.", "equity", "USD", 0.28, 0.12),
                ("MSFT", "Microsoft", "equity", "USD", 0.24, 0.15),
                ("TSLA", "Tesla", "equity", "USD", 0.55, 0.20),
                ("US10Y", "US 10-Year Treasury", "bond", "USD", 0.05, 0.04),
                ("DE10Y", "German Bund", "bond", "EUR", 0.04, 0.02),
                ("GOLD", "Gold Futures", "commodity", "USD", 0.15, 0.06),
                ("EURUSD", "EUR/USD Forward", "derivative", "EUR", 0.08, 0.01),
                ("SPY", "S&P 500 ETF", "equity", "USD", 0.18, 0.10)
            ]
            db_assets = {}
            for ticker, name, atype, curr, vol, ret in asset_data:
                a = db.query(Asset).filter_by(ticker=ticker).first()
                if not a:
                    a = Asset(
                        ticker=ticker, asset_name=name, type_id=db_types[atype].type_id,
                        currency=curr, annual_volatility=vol, annual_return=ret, 
                        base_price=100.0
                    )
                    db.add(a)
                    db.flush()
                db_assets[ticker] = a

            # 4. Portfolios
            portfolios = [
                ("Aggressive Growth", [("AAPL", 0.60), ("TSLA", 0.30), ("MSFT", 0.10)]),
                ("Conservative Bond", [("US10Y", 0.50), ("DE10Y", 0.30), ("GOLD", 0.20)]),
                ("Balanced", [("SPY", 0.30), ("MSFT", 0.20), ("US10Y", 0.20), ("GOLD", 0.20), ("EURUSD", 0.10)])
            ]
            db_ports = []
            for name, holdings in portfolios:
                p = db.query(Portfolio).filter_by(name=name).first()
                if not p:
                    p = Portfolio(name=name, description=f"{name} strategy", owner_id=user.user_id)
                    db.add(p)
                    db.flush()
                    
                    for ticker, weight in holdings:
                        pa = PortfolioAsset(
                            portfolio_id=p.portfolio_id, asset_id=db_assets[ticker].asset_id,
                            weight=weight, quantity=100.0
                        )
                        db.add(pa)
                    db_ports.append(p)
                else:
                    db_ports.append(p)

            # 5. Scenarios
            scenario_data = [
                ("Baseline", 0, 1.0, 0.0),
                ("2008 Crisis", -150, 2.5, -0.35),
                ("2022 Rate Hike", 300, 1.4, -0.18),
                ("Mild Stress", 100, 1.2, -0.08)
            ]
            db_scens = []
            for name, rate, vol, eq in scenario_data:
                s = db.query(Scenario).filter_by(name=name).first()
                if not s:
                    s = Scenario(name=name, interest_rate_shock_bps=rate, volatility_multiplier=vol, equity_shock_pct=eq, created_by=user.user_id)
                    db.add(s)
                    db.flush()
                    db_scens.append(s)
                else:
                    db_scens.append(s)
            
            # Commit to ensure DB consistency before making MC runs
            db.commit()

            print("Base data seeded. Running predefined simulations...")
            
            # 6. Runs
            total_runs = len(db_ports) * len(db_scens)
            idx = 1
            for p in db_ports:
                for s in db_scens:
                    # check if run exists
                    ex = db.query(SimulationRun).filter_by(portfolio_id=p.portfolio_id, scenario_id=s.scenario_id).first()
                    if ex:
                        continue
                        
                    print(f"Running {idx}/{total_runs}: Portfolio='{p.name}', Scenario='{s.name}'")
                    
                    assets_payload = []
                    for pa in p.assets:
                        assets_payload.append({
                            'asset_type': pa.asset.asset_type.type_name,
                            'weight': pa.weight,
                            'quantity': pa.quantity,
                            'base_price': pa.asset.base_price,
                            'annual_volatility': pa.asset.annual_volatility,
                            'annual_return': pa.asset.annual_return
                        })
                    
                    scenario_payload = {
                        'interest_rate_shock_bps': s.interest_rate_shock_bps,
                        'volatility_multiplier': s.volatility_multiplier,
                        'equity_shock_pct': s.equity_shock_pct
                    }
                    
                    try:
                        metrics = run_monte_carlo(assets_payload, scenario_payload, 10000, 252, 42)
                        
                        sr = SimulationRun(portfolio_id=p.portfolio_id, scenario_id=s.scenario_id, initiated_by=user.user_id, status='completed', completed_at=datetime.utcnow())
                        db.add(sr)
                        db.flush()
                        
                        for k, v in metrics.items():
                            conf = 0.95 if '95' in k else (0.99 if '99' in k else None)
                            rm = RiskMetric(run_id=sr.run_id, metric_type=k, metric_value=v, confidence_level=conf)
                            db.add(rm)
                        db.commit()
                        
                    except Exception as e:
                        print(f"FAILED RUN: {str(e)}")
                        traceback.print_exc()
                        db.rollback()
                        
                    idx += 1
                    
            print("Seeding logic completed!")

        except Exception as ex:
            db.rollback()
            print("Failed seeding: ", str(ex))
            traceback.print_exc()

if __name__ == "__main__":
    seed_db()
