from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import random
import json

from core.database import SessionLocal
from models.user import User
from models.asset import Asset, AssetType
from models.portfolio import Portfolio, PortfolioAsset
from models.simulation import Scenario, SimulationRun, RiskMetric
from scripts.seed_data import ASSET_TYPES, ASSETS, SCENARIOS, PORTFOLIOS

def bootstrap_full_data(db: Session):
    results = []
    
    # 1. Ensure we have users to link to
    admin = db.query(User).filter(User.username.like("%admin%")).first()
    analyst = db.query(User).filter(User.username.like("%analyst%")).first()
    
    if not admin or not analyst:
        return {"status": "error", "message": "Users not found. Run /bootstrap-users first."}

    # 2. Seed Asset Types
    type_map = {}
    for t_data in ASSET_TYPES:
        existing = db.query(AssetType).filter(AssetType.type_name == t_data["type_name"]).first()
        if not existing:
            new_type = AssetType(**t_data)
            db.add(new_type)
            db.flush()
            type_map[t_data["type_name"]] = new_type.type_id
            results.append(f"Created AssetType: {t_data['type_name']}")
        else:
            type_map[t_data["type_name"]] = existing.type_id
            results.append(f"AssetType '{t_data['type_name']}' exists.")

    # 3. Seed Assets
    asset_map = {}
    for a_data in ASSETS:
        existing = db.query(Asset).filter(Asset.ticker == a_data["ticker"]).first()
        t_name = a_data.pop("type_name")
        a_data["type_id"] = type_map.get(t_name)
        
        if not existing:
            new_asset = Asset(**a_data)
            db.add(new_asset)
            db.flush()
            asset_map[a_data["ticker"]] = new_asset.asset_id
            results.append(f"Created Asset: {a_data['ticker']}")
        else:
            asset_map[a_data["ticker"]] = existing.asset_id
            results.append(f"Asset '{a_data['ticker']}' exists.")

    # 4. Seed Scenarios
    scenario_ids = []
    for s_data in SCENARIOS:
        existing = db.query(Scenario).filter(Scenario.name == s_data["name"]).first()
        if not existing:
            s_data["created_by"] = admin.user_id
            new_scen = Scenario(**s_data)
            db.add(new_scen)
            db.flush()
            scenario_ids.append(new_scen.scenario_id)
            results.append(f"Created Scenario: {s_data['name']}")
        else:
            scenario_ids.append(existing.scenario_id)
            results.append(f"Scenario '{s_data['name']}' exists.")

    # 5. Seed Portfolios
    for p_data in PORTFOLIOS:
        existing = db.query(Portfolio).filter(Portfolio.name == p_data["name"]).first()
        assets_info = p_data.pop("assets")
        
        if not existing:
            p_data["owner_id"] = analyst.user_id
            new_port = Portfolio(**p_data)
            db.add(new_port)
            db.flush()
            
            for a_info in assets_info:
                pa = PortfolioAsset(
                    portfolio_id=new_port.portfolio_id,
                    asset_id=asset_map[a_info["ticker"]],
                    weight=a_info["weight"],
                    quantity=a_info["quantity"]
                )
                db.add(pa)
            results.append(f"Created Portfolio: {p_data['name']}")
            
            # --- SEED MOCK HISTORICAL RUNS for this new portfolio ---
            if p_data["name"] == "Aggressive Tech Portfolio":
                for i in range(10):
                    days_ago = (10 - i) * 3
                    run_time = datetime.utcnow() - timedelta(days=days_ago)
                    
                    mock_run = SimulationRun(
                        portfolio_id=new_port.portfolio_id,
                        scenario_id=scenario_ids[0],
                        initiated_by=analyst.user_id,
                        status="completed",
                        run_type="monte_carlo",
                        num_simulations=10000,
                        started_at=run_time - timedelta(minutes=5),
                        completed_at=run_time,
                        random_seed=42,
                        time_horizon_days=252,
                        histogram_data={
                            "bin_edges": [round(-10000 + (j * 500), 2) for j in range(41)],
                            "counts": [random.randint(0, 1000) for _ in range(40)],
                            "mean_pnl": random.uniform(-2000, 5000),
                            "pnl_min": -10000,
                            "pnl_max": 10000,
                            "bin_width": 500
                        }
                    )
                    db.add(mock_run)
                    db.flush()
                    
                    metrics = [
                        {"type": "VaR_95", "val": random.uniform(2000, 5000)},
                        {"type": "VaR_99", "val": random.uniform(5000, 8000)},
                        {"type": "ES_95", "val": random.uniform(6000, 9000)},
                        {"type": "volatility", "val": random.uniform(0.1, 0.3)},
                        {"type": "max_drawdown", "val": random.uniform(0.15, 0.4)},
                    ]
                    for m in metrics:
                        rm = RiskMetric(
                            run_id=mock_run.run_id,
                            metric_type=m["type"],
                            metric_value=m["val"],
                            confidence_level=0.95 if "95" in m["type"] else (0.99 if "99" in m["type"] else None)
                        )
                        db.add(rm)
                results.append(f"Added 10 historical simulation runs for {p_data['name']}")
        else:
            results.append(f"Portfolio '{p_data['name']}' exists.")
            
    db.commit()
    return {"status": "success", "actions": results}
