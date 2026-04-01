from datetime import date, datetime, timedelta

# Asset Types
ASSET_TYPES = [
    {"type_name": "equity", "description": "Common stocks and ETFs", "risk_category": "high"},
    {"type_name": "bond", "description": "Government and corporate bonds", "risk_category": "low"},
    {"type_name": "derivative", "description": "Options and futures", "risk_category": "very_high"},
    {"type_name": "commodity", "description": "Gold, Oil, etc.", "risk_category": "medium"},
]

# Assets
ASSETS = [
    {
        "ticker": "AAPL",
        "asset_name": "Apple Inc.",
        "currency": "USD",
        "exchange": "NASDAQ",
        "sector": "Technology",
        "country": "USA",
        "base_price": 185.0,
        "annual_volatility": 0.22,
        "annual_return": 0.12,
        "type_name": "equity"
    },
    {
        "ticker": "MSFT",
        "asset_name": "Microsoft Corp.",
        "currency": "USD",
        "exchange": "NASDAQ",
        "sector": "Technology",
        "country": "USA",
        "base_price": 400.0,
        "annual_volatility": 0.19,
        "annual_return": 0.15,
        "type_name": "equity"
    },
    {
        "ticker": "TSLA",
        "asset_name": "Tesla, Inc.",
        "currency": "USD",
        "exchange": "NASDAQ",
        "sector": "Consumer Cyclical",
        "country": "USA",
        "base_price": 175.0,
        "annual_volatility": 0.45,
        "annual_return": 0.20,
        "type_name": "equity"
    },
    {
        "ticker": "SPY",
        "asset_name": "S&P 500 ETF Trust",
        "currency": "USD",
        "exchange": "NYSE",
        "sector": "Index",
        "country": "USA",
        "base_price": 510.0,
        "annual_volatility": 0.15,
        "annual_return": 0.10,
        "type_name": "equity"
    },
    {
        "ticker": "TLT",
        "asset_name": "iShares 20+ Year Treasury Bond ETF",
        "currency": "USD",
        "exchange": "NASDAQ",
        "sector": "Fixed Income",
        "country": "USA",
        "base_price": 95.0,
        "annual_volatility": 0.12,
        "annual_return": 0.04,
        "type_name": "bond"
    },
]

# Scenarios
SCENARIOS = [
    {
        "name": "Standard Market Conditions",
        "description": "Baseline simulation with no major shocks.",
        "interest_rate_shock_bps": 0,
        "volatility_multiplier": 1.0,
        "equity_shock_pct": 0.0
    },
    {
        "name": "Severe Global Recession",
        "description": "Equity markets crash by 30%, volatility spikes 2.5x.",
        "interest_rate_shock_bps": -150,
        "volatility_multiplier": 2.5,
        "equity_shock_pct": -0.30
    },
    {
        "name": "Hyperinflation Spike",
        "description": "Interest rates rise by 200bps, equities drop 15%.",
        "interest_rate_shock_bps": 200,
        "volatility_multiplier": 1.5,
        "equity_shock_pct": -0.15
    }
]

# Portfolios
PORTFOLIOS = [
    {
        "name": "Aggressive Tech Portfolio",
        "description": "High-growth tech focused allocation.",
        "base_currency": "USD",
        "assets": [
            {"ticker": "AAPL", "weight": 0.4, "quantity": 200},
            {"ticker": "MSFT", "weight": 0.4, "quantity": 100},
            {"ticker": "TSLA", "weight": 0.2, "quantity": 150},
        ]
    },
    {
        "name": "Conservative 60/40",
        "description": "Classic balanced allocation for lower risk.",
        "base_currency": "USD",
        "assets": [
            {"ticker": "SPY", "weight": 0.4, "quantity": 100},
            {"ticker": "TLT", "weight": 0.6, "quantity": 600},
        ]
    }
]
