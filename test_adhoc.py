import urllib.request
import urllib.parse
import json

# Login
login_data = json.dumps({'username': 'analyst@analyst.quantrisk', 'password': 'Password123!'}).encode()
req = urllib.request.Request("http://127.0.0.1:8000/auth/login", data=login_data, headers={'Content-Type': 'application/json'}, method='POST')
try:
    with urllib.request.urlopen(req) as response:
        token_data = json.loads(response.read().decode())
        token = token_data['access_token']
        print("Got token")
except Exception as e:
    print(f"Login failed: {e}")
    exit(1)

# Test POST ad-hoc
post_data = json.dumps({
    "portfolio_assets": [
        {"asset_name": "Test", "asset_type": "equity", "base_price": 100.0, "annual_volatility": 0.2, "annual_return": 0.05, "weight": 1.0, "quantity": 100}
    ],
    "scenario": {
        "interest_rate_shock_bps": 0,
        "volatility_multiplier": 1.0,
        "equity_shock_pct": 0.0
    },
    "simulation_type": "monte_carlo"
}).encode()
req3 = urllib.request.Request("http://127.0.0.1:8000/simulation-runs/ad-hoc", data=post_data, headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}, method='POST')
try:
    with urllib.request.urlopen(req3) as response:
        print("POST /ad-hoc:", response.getcode())
except urllib.error.HTTPError as e:
    print(f"POST ad-hoc HTTPError: {e.code}")
    print(e.read().decode())
