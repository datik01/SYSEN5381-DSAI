# my_good_query.py
# Substantial API Query for Reporter Applications
# Loads API key from 01_query_api/.env and fetches time-series EOD data from Marketstack.

# -----------------------------------------------------------------------------
# Stage 3: Document Results (summary for reporters)
# -----------------------------------------------------------------------------
# API name:        Marketstack (APILayer)
# Endpoint:        GET https://api.marketstack.com/v1/eod
# Parameters:      access_key (required), symbols (required), limit (optional)
# Expected data:   Time series of end-of-day OHLCV (open, high, low, close, volume)
# Records:         10–20+ rows per request (controlled by limit)
# Key fields:      date, symbol, open, high, low, close, volume, exchange
# Data structure:  JSON with "pagination" (limit, offset, count, total) and "data" (list of records)
# Use case:        Daily stock reports, trend summaries, multi-day analysis
# -----------------------------------------------------------------------------

# 0. Setup #################################

## 0.1 Load Packages ############################

import os
from pathlib import Path

import requests
from dotenv import load_dotenv

## 0.2 Load Environment Variables ################

# Load .env from same folder as this script (01_query_api)
env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(env_path)

API_KEY = os.getenv("API_KEY")
if not API_KEY:
    raise ValueError(
        "API_KEY not found in .env. Add API_KEY=your_key to 01_query_api/.env "
        "(Marketstack key from https://marketstack.com)"
    )

## 1. Design Query (Stage 1) #####################

# Query design: time series data for reporter application
# - Endpoint: Marketstack EOD returns historical daily OHLCV per symbol
# - Choice: single symbol (AAPL) with limit=20 for 20 most recent trading days
# - Use case: build daily/weekly reports, show recent trend (open/close, volume)
# Required params: access_key, symbols
# Optional params: limit (default 100; we set 20 for a focused dataset), date_from, date_to

EOD_URL = "https://api.marketstack.com/v1/eod"
PARAMS = {
    "access_key": API_KEY,
    "symbols": "AAPL",   # one symbol for clean time series
    "limit": 20,         # 20 rows: last 20 trading days
}

## 2. Implement Query (Stage 2) ###################

response = requests.get(EOD_URL, params=PARAMS)

# Error handling: non-200 or API error payload
if not response.ok:
    raise RuntimeError(
        f"Marketstack API error: status {response.status_code}, body: {response.text[:200]}"
    )

payload = response.json()

# Some APIs return 200 but signal errors in JSON (e.g., invalid key)
if "error" in payload:
    raise RuntimeError(f"Marketstack API error: {payload.get('error', payload)}")

data = payload.get("data") or []
if not data:
    raise RuntimeError("Marketstack returned no data (check symbol and date range).")

# Verify we got the expected number of records (at least 10 for "substantial")
num_records = len(data)
if num_records < 10:
    raise RuntimeError(
        f"Expected at least 10 records for reporter use; got {num_records}."
    )

## 3. Document and Use Results ####################

# Record count and structure (Stage 3 documentation)
pagination = payload.get("pagination", {})
print("--- Query results (for reporter use) ---")
print(f"Records returned: {num_records}")
print(f"Pagination: limit={pagination.get('limit')}, total={pagination.get('total')}")
print("Key fields per row: date, symbol, open, high, low, close, volume, exchange")
print("Sample (first record):", data[0])
print("---")

# Expose for downstream reporter: list of dicts, one row per trading day
records = data
