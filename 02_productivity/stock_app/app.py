# app.py
# Stock EOD Dashboard (Streamlit)
# Uses Marketstack EOD API; logic ported from my_good_query.py.

# Interactive dashboard: symbol + days input, candlestick chart, and raw data table.
# API key loaded from .env in this folder; data fetching cached to avoid repeated calls.

# 0. Setup #################################

import os
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import requests
import streamlit as st
from dotenv import load_dotenv

# Load .env from app folder first, then parent (02_productivity) so one key works for both
app_dir = Path(__file__).resolve().parent
load_dotenv(app_dir / ".env")
load_dotenv(app_dir.parent / ".env")

EOD_URL = "https://api.marketstack.com/v1/eod"

# 1. Data Fetching ############################


@st.cache_data(ttl=300)
def get_stock_data(symbol: str, limit: int) -> pd.DataFrame:
    """
    Fetch EOD data from Marketstack for the given symbol and limit.
    Returns a DataFrame with columns date, open, high, low, close, volume, etc.
    Raises ValueError with a user-friendly message on API or validation errors.
    """
    api_key = os.getenv("API_KEY")
    if not api_key or api_key.strip() == "your_marketstack_key":
        raise ValueError(
            "API_KEY not set. Add a line API_KEY=your_actual_key to "
            "02_productivity/stock_app/.env or 02_productivity/.env "
            "(replace your_marketstack_key with a key from https://marketstack.com)."
        )

    params = {"access_key": api_key, "symbols": symbol.strip().upper(), "limit": limit}
    response = requests.get(EOD_URL, params=params, timeout=15)

    if not response.ok:
        raise ValueError(
            f"Marketstack API error: HTTP {response.status_code}. "
            f"Response: {response.text[:200]}"
        )

    payload = response.json()
    if "error" in payload:
        err = payload.get("error", payload)
        raise ValueError(f"Marketstack API error: {err}")

    data = payload.get("data") or []
    if not data:
        raise ValueError(
            f"No data returned for symbol '{symbol}'. Check the symbol or try another."
        )

    # Build DataFrame and sort by date ascending for candlestick (oldest first)
    df = pd.DataFrame(data)
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"])
        df = df.sort_values("date").reset_index(drop=True)

    return df


# 2. Streamlit UI ############################

st.set_page_config(page_title="Stock EOD Dashboard", page_icon="📈", layout="wide")
st.title("📈 Stock End-of-Day Dashboard")
st.caption("Data from Marketstack EOD API (logic from my_good_query.py)")

# User inputs: symbol and days (maps to limit)
symbol = st.text_input(
    "Stock Symbol",
    value="AAPL",
    placeholder="e.g. AAPL, MSFT",
    help="Ticker symbol for the stock.",
)
days = st.slider(
    "Days to Retrieve",
    min_value=10,
    max_value=100,
    value=20,
    step=1,
    help="Number of most recent trading days (API limit parameter).",
)

# Fetch data and handle errors
try:
    df = get_stock_data(symbol, days)
except ValueError as e:
    st.error(str(e))
    st.stop()

# Candlestick chart (Open, High, Low, Close)
st.subheader("Candlestick Chart (OHLC)")
fig = go.Figure(
    data=[
        go.Candlestick(
            x=df["date"],
            open=df["open"],
            high=df["high"],
            low=df["low"],
            close=df["close"],
            name=symbol,
        )
    ]
)
fig.update_layout(
    xaxis_title="Date",
    yaxis_title="Price",
    xaxis_rangeslider_visible=False,
    height=450,
)
st.plotly_chart(fig, use_container_width=True)

# Raw data table
st.subheader("Raw Data")
# Show key columns in a consistent order for readability
display_cols = ["date", "symbol", "open", "high", "low", "close", "volume"]
available = [c for c in display_cols if c in df.columns]
st.dataframe(df[available] if available else df, use_container_width=True)
