from datetime import date, datetime, timedelta

# Asset Types
ASSET_TYPES = [
    {"type_name": "equity", "description": "Common stocks and ETFs", "risk_category": "high"},
    {"type_name": "bond", "description": "Government and corporate bonds", "risk_category": "low"},
    {"type_name": "derivative", "description": "Options and futures", "risk_category": "high"},
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
    {
        "ticker": "GOOGL",
        "asset_name": "Alphabet Inc.",
        "currency": "USD",
        "exchange": "NASDAQ",
        "sector": "Technology",
        "country": "USA",
        "base_price": 150.0,
        "annual_volatility": 0.24,
        "annual_return": 0.13,
        "type_name": "equity"
    },
    {
        "ticker": "AMZN",
        "asset_name": "Amazon.com Inc.",
        "currency": "USD",
        "exchange": "NASDAQ",
        "sector": "Consumer Cyclical",
        "country": "USA",
        "base_price": 180.0,
        "annual_volatility": 0.28,
        "annual_return": 0.14,
        "type_name": "equity"
    },
    {
        "ticker": "NVDA",
        "asset_name": "NVIDIA Corporation",
        "currency": "USD",
        "exchange": "NASDAQ",
        "sector": "Technology",
        "country": "USA",
        "base_price": 900.0,
        "annual_volatility": 0.45,
        "annual_return": 0.25,
        "type_name": "equity"
    },
    {
        "ticker": "GLD",
        "asset_name": "SPDR Gold Shares",
        "currency": "USD",
        "exchange": "NYSE",
        "sector": "Commodity",
        "country": "USA",
        "base_price": 215.0,
        "annual_volatility": 0.14,
        "annual_return": 0.06,
        "type_name": "commodity"
    },
    {
        "ticker": "META",
        "asset_name": "Meta Platforms, Inc.",
        "currency": "USD",
        "exchange": "NASDAQ",
        "sector": "Technology",
        "country": "USA",
        "base_price": 480.0,
        "annual_volatility": 0.32,
        "annual_return": 0.16,
        "type_name": "equity"
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
    },
    {
        "name": "COVID-19 Market Crash",
        "description": "Global lockdown. Equities -25%, Vol 2.0x, Rates cut by 50bps.",
        "interest_rate_shock_bps": -50,
        "volatility_multiplier": 2.0,
        "equity_shock_pct": -0.25
    },
    {
        "name": "2008 Financial Crisis",
        "description": "Lehman collapse. Equities -45%, Vol 3.0x, Rates cut by 150bps.",
        "interest_rate_shock_bps": -150,
        "volatility_multiplier": 3.0,
        "equity_shock_pct": -0.45
    },
    {
        "name": "Great Depression (1929)",
        "description": "Systemic collapse. Equities -85%, Vol 4.0x, Deflationary rate shock.",
        "interest_rate_shock_bps": -300,
        "volatility_multiplier": 4.0,
        "equity_shock_pct": -0.85
    }
]

# Portfolios
PORTFOLIOS = [
    {
        "name": "Aggressive Tech Portfolio",
        "description": "High-growth tech focused allocation.",
        "base_currency": "USD",
        "assets": [
            {"ticker": "AAPL", "weight": 0.25, "quantity": 200},
            {"ticker": "MSFT", "weight": 0.25, "quantity": 100},
            {"ticker": "AMZN", "weight": 0.25, "quantity": 150},
            {"ticker": "NVDA", "weight": 0.25, "quantity": 50},
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
