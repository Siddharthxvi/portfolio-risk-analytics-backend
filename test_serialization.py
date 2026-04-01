import sys, os
sys.path.append('scratch/portfolio-risk-analytics-backend')

from schemas.asset import AssetResponse
from pydantic import ValidationError

# Mock an Asset model object
class MockAsset:
    def __init__(self):
        self.asset_id = 1
        self.ticker = "AAPL"
        self.asset_name = "Apple"
        self.currency = "USD"
        self.exchange = None  # This is the suspect
        self.sector = None
        self.country = None
        self.base_price = 150.0
        self.annual_volatility = 0.2
        self.annual_return = 0.1
        self.type_id = 1

try:
    mock = MockAsset()
    res = AssetResponse.model_validate(mock)
    print("Serialization success:", res.model_dump())
except ValidationError as e:
    print("Serialization failed:")
    print(e)
except Exception as e:
    print("Unexpected error:", str(e))
