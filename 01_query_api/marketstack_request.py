# marketstack_request.py
# Marketstack API GET Request
# Pairs with 02_example.py pattern
# Loads API key from .env and requests end-of-day data from Marketstack.

# This script shows how to:
# - Load an API key from a .env file in 01_query_api (API_KEY var)
# - Make a GET request to the Marketstack API (EOD endpoint)
# - Inspect the HTTP status code and JSON response

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

# Marketstack uses access_key as the query parameter; we read API_KEY from .env
ACCESS_KEY = os.getenv("API_KEY")
if not ACCESS_KEY:
    raise ValueError(
        "API_KEY not found in .env. "
        "Add API_KEY=your_key to 01_query_api/.env (get one at https://marketstack.com)"
    )

## 1. Make API Request ###########################

# Marketstack EOD endpoint: https://api.marketstack.com/v1/eod
# API key is passed as access_key query parameter; symbols is required for EOD.
# See: https://docs.apilayer.com/marketstack/docs/api-documentation
url = "https://api.marketstack.com/v1/eod"
params = {"access_key": ACCESS_KEY, "symbols": "AAPL"}

response = requests.get(url, params=params)

## 2. Inspect Response ###########################

print("Status code:", response.status_code)

if response.status_code == 200:
    print("Success. Sample response:")
    data = response.json()
    print(data)
else:
    print("Response body:", response.text)
