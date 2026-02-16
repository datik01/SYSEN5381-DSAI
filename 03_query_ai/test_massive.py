# test_massive.py
# Test the Massive.com REST API using the official Python client.
# Uses MASSIVE_API_KEY from .env (script directory or project root).

# 0. Setup #################################

from pathlib import Path

from dotenv import load_dotenv

# Load .env from this folder or project root so key is found when run from anywhere
_script_dir = Path(__file__).resolve().parent
load_dotenv(_script_dir / ".env")
load_dotenv(_script_dir.parent / ".env")

import os

api_key = os.getenv("MASSIVE_API_KEY")
if not api_key:
    raise ValueError(
        "MASSIVE_API_KEY not set. Add MASSIVE_API_KEY=your_key to .env "
        "(get a key from https://massive.com)"
    )

# 1. Test Massive API #################################

from massive import RESTClient

# Initialize client with key from .env
client = RESTClient(api_key=api_key)

# Free-plan test: previous day bar (OHLC) is included on Stocks Basic
# get_last_trade / real-time require paid plans
print("Testing Massive API (free plan): get_previous_close_agg(ticker='AAPL')")
result = client.get_previous_close_agg(ticker="AAPL")
print("Result:", result)
print("\n✅ Massive API test succeeded.")
