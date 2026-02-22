# api_query.py
# Massive API Query for HW1 Reporter
# Pairs with LAB 1 (API query). Fetches previous close OHLC data from Massive API.

# Fetches stock data from Massive API (free tier: previous day bar).
# Use get_stock_data() for one ticker or get_stock_data_batch() for multiple (rate-limited).
# Data is returned as a list of dicts for use by the Streamlit app and AI reporter.

# 0. Setup #################################

import os
import time
from pathlib import Path

from dotenv import load_dotenv

# Load .env from hw1 folder or 03_query_ai so key is found when run from anywhere
_script_dir = Path(__file__).resolve().parent
load_dotenv(_script_dir / ".env")
load_dotenv(_script_dir.parent / ".env")

def _get_client():
    """Lazy client so we only require MASSIVE_API_KEY when actually calling the API."""
    key = os.getenv("MASSIVE_API_KEY")
    if not key:
        raise ValueError(
            "MASSIVE_API_KEY not found in .env. Add MASSIVE_API_KEY=your_key to "
            "03_query_ai/hw1/.env or 03_query_ai/.env (get a key from https://massive.com)."
        )
    from massive import RESTClient
    return RESTClient(api_key=key)

# Free tier: 5 API calls per minute — use delay between batch calls
RATE_LIMIT_DELAY_SEC = 13


def _get_bar_val(bar, *keys):
    """Get value from a bar (PreviousCloseAgg object or dict). Tries each key in order."""
    for key in keys:
        val = getattr(bar, key, None) if not isinstance(bar, dict) else bar.get(key)
        if val is not None:
            return val
    return None


def _extract_bar(agg, ticker: str) -> dict:
    """
    Extract the first OHLC bar from Massive API response.
    The client returns the results list directly (list of PreviousCloseAgg with .open, .high, etc.).
    Lab fallback: agg may be object with .results or dict with "results" (bars use o/h/l/c/v in JSON).
    """
    # Client returns list of bars directly; no .results wrapper (see rest/base.py _get)
    if isinstance(agg, list):
        results = agg
    else:
        results = getattr(agg, "results", None) or (
            agg.get("results") if isinstance(agg, dict) else None
        )
    if not results or len(results) == 0:
        return {"ticker": ticker, "open": None, "high": None, "low": None, "close": None, "volume": None}

    bar = results[0]
    return {
        "ticker": ticker,
        "open": _get_bar_val(bar, "open", "o"),
        "high": _get_bar_val(bar, "high", "h"),
        "low": _get_bar_val(bar, "low", "l"),
        "close": _get_bar_val(bar, "close", "c"),
        "volume": _get_bar_val(bar, "volume", "v"),
    }


# 1. Single-ticker query #################################


def get_stock_data(ticker: str) -> dict:
    """
    Fetch previous close OHLC for one ticker from Massive API.
    Returns a single dict: ticker, open, high, low, close, volume.
    """
    ticker = ticker.strip().upper()
    client = _get_client()
    agg = client.get_previous_close_agg(ticker=ticker)
    return _extract_bar(agg, ticker)


# 2. Range aggregates (minute or daily bars) #################################

def _agg_bar_to_dict(bar, ticker: str):
    """Convert Agg (or dict) to our standard bar dict; include timestamp if present."""
    out = {
        "ticker": ticker,
        "open": _get_bar_val(bar, "open", "o"),
        "high": _get_bar_val(bar, "high", "h"),
        "low": _get_bar_val(bar, "low", "l"),
        "close": _get_bar_val(bar, "close", "c"),
        "volume": _get_bar_val(bar, "volume", "v"),
    }
    ts = _get_bar_val(bar, "timestamp", "t")
    if ts is not None:
        out["timestamp"] = ts
    return out


def get_aggs_bars(
    ticker: str,
    multiplier: int,
    timespan: str,
    from_date: str,
    to_date: str,
    limit: int = 5000,
    sort: str = "asc",
) -> list[dict]:
    """
    Fetch OHLC bars over a date range (minute or daily). Uses Massive get_aggs.
    timespan: "minute" | "hour" | "day" etc. from_date/to_date: YYYY-MM-DD.
    Returns list of dicts with ticker, open, high, low, close, volume, timestamp (ms).
    """
    ticker = ticker.strip().upper()
    client = _get_client()
    raw = client.get_aggs(
        ticker=ticker,
        multiplier=multiplier,
        timespan=timespan,
        from_=from_date,
        to=to_date,
        limit=limit,
        sort=sort,
    )
    # Client returns list of Agg objects
    if not raw or not isinstance(raw, list):
        return []
    return [_agg_bar_to_dict(bar, ticker) for bar in raw]


# 3. Multi-ticker query (rate-limited) #################################


def get_stock_data_batch(tickers: list[str]) -> list[dict]:
    """
    Fetch previous close OHLC for multiple tickers. Waits RATE_LIMIT_DELAY_SEC
    between calls to stay within Massive free tier (5 requests/minute).
    Returns a list of dicts, one per ticker.
    """
    out = []
    for i, ticker in enumerate(tickers):
        t = ticker.strip().upper()
        if not t:
            continue
        rec = get_stock_data(t)
        out.append(rec)
        if i < len(tickers) - 1:
            time.sleep(RATE_LIMIT_DELAY_SEC)
    return out


# 4. Script entry (run as standalone) #################################

if __name__ == "__main__":
    # Example: fetch AAPL and print result (for testing and documentation)
    print("--- Massive API query (previous close) ---")
    data = get_stock_data("AAPL")
    print("Sample record:", data)
    print("---")
