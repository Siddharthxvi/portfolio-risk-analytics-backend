import requests

try:
    response = requests.get("http://localhost:8000/assets/fetch-data/MSFT")
    print(response.status_code)
    print(response.json())
except Exception as e:
    print(e)
