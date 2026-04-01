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
    # 1. Ensure we have users to link to
    users = db.query(User).filter(User.username.like("%quantrisk%")).all()
    if not users:
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
        # Use a copy to avoid modifying the global constant across multiple runs
        data = a_data.copy()
        existing = db.query(Asset).filter(Asset.ticker == data["ticker"]).first()
        t_name = data.pop("type_name")
        data["type_id"] = type_map.get(t_name)
        
        if not existing:
            new_asset = Asset(**data)
            db.add(new_asset)
            db.flush()
            asset_map[data["ticker"]] = new_asset.asset_id
            results.append(f"Created Asset: {data['ticker']}")
        else:
            asset_map[data["ticker"]] = existing.asset_id
            results.append(f"Asset '{data['ticker']}' exists.")

    # 4. Seed Scenarios
    scenario_ids = []
    # Find an admin for scenario ownership
    admin_user = next((u for u in users if "admin" in u.username), users[0])
    for s_data in SCENARIOS:
        existing = db.query(Scenario).filter(Scenario.name == s_data["name"]).first()
        if not existing:
            data = s_data.copy()
            data["created_by"] = admin_user.user_id
            new_scen = Scenario(**data)
            db.add(new_scen)
            db.flush()
            scenario_ids.append(new_scen.scenario_id)
            results.append(f"Created Scenario: {s_data['name']}")
        else:
            scenario_ids.append(existing.scenario_id)
            results.append(f"Scenario '{s_data['name']}' exists.")

    # 5. Seed Portfolios for EACH user
    for user in users:
        for p_data in PORTFOLIOS:
            data = p_data.copy()
            assets_info = data.pop("assets")
            
            existing = db.query(Portfolio).filter(
                Portfolio.name == data["name"], 
                Portfolio.owner_id == user.user_id
            ).first()
            
            if not existing:
                data["owner_id"] = user.user_id
                new_port = Portfolio(**data)
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
                results.append(f"Created Portfolio '{data['name']}' for {user.username}")
                
                # --- SEED MOCK HISTORICAL RUNS for Tech Portfolio to light up the dashboard ---
                if data["name"] == "Aggressive Tech Portfolio":
                    for i in range(10):
                        days_ago = (10 - i) * 3
                        run_time = datetime.utcnow() - timedelta(days=days_ago)
                        
                        mock_run = SimulationRun(
                            portfolio_id=new_port.portfolio_id,
                            scenario_id=scenario_ids[0],
                            initiated_by=user.user_id,
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
                    results.append(f"Added historical simulation history for {user.username}")
            else:
                results.append(f"Portfolio '{data['name']}' already exists for {user.username}")

    db.commit()
    return {"status": "success", "actions": results}
            
    db.commit()
    return {"status": "success", "actions": results}
