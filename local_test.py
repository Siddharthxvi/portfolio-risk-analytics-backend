from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

response = client.get("/simulation-runs/test")
print(response.status_code)
try:
    print(response.json())
except Exception as e:
    print(response.text)
