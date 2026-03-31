from fastapi.testclient import TestClient
from main import app
import json

client = TestClient(app)

def run_sample_test():
    payload = {
        "portfolio_assets": [
            {
                "asset_name": "AAPL",
                "asset_type": "equity",
                "base_price": 100.0,
                "annual_volatility": 0.28,
                "annual_return": 0.12,
                "weight": 0.60,
                "quantity": 600
            },
            {
                "asset_name": "US10Y",
                "asset_type": "bond",
                "base_price": 100.0,
                "annual_volatility": 0.05,
                "annual_return": 0.04,
                "weight": 0.40,
                "quantity": 400
            }
        ],
        "scenario": {
            "interest_rate_shock_bps": -150,
            "volatility_multiplier": 2.5,
            "equity_shock_pct": -0.35
        },
        "num_iterations": 10000,
        "time_horizon_days": 100,                 
        "random_seed": 42
    }

    print(f"Sending POST request to /simulation-runs/ad-hoc with Payload:\n{json.dumps(payload, indent=2)}\n")
    
    response = client.post("/simulation-runs/ad-hoc", json=payload)
    
    print(f"Response Status Code: {response.status_code}")
    print("-" * 40)
    
    if response.status_code == 200:
        print("Success (200 OK)! Risk Metrics returned:")
        metrics = response.json()
        for key, value in metrics.items():
            print(f"  {key:<15}: {value:.2f}")
            
    elif response.status_code == 422:
        print("Validation Error (422 Unprocessable Entity):")
        print(json.dumps(response.json(), indent=2))
        
    else:
        print("Internal Server Error (500):")
        print(response.json())

if __name__ == "__main__":
    print("=== Testing FastAPI Simulation Endpoint Pipeline ===\n")
    run_sample_test()
