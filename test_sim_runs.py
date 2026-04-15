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

# Test GET simulation runs
req2 = urllib.request.Request("http://127.0.0.1:8000/simulation-runs/", headers={'Authorization': f'Bearer {token}'})
try:
    with urllib.request.urlopen(req2) as response:
        print("GET / runs:", response.getcode())
        print(response.read().decode()[:200])
except urllib.error.HTTPError as e:
    print(f"GET runs HTTPError: {e.code}")
    print(e.read().decode())
