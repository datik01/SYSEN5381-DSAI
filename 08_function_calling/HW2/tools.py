# tools.py
# HW2: Tool Function Definitions (Function Calling)
# Danny Atik - SYSEN 5381
#
# This module defines tool functions that agents can call to interact
# with external APIs and perform computations. Each function includes
# metadata describing its parameters for LLM function-calling integration.
#
# Tools:
#   1. fetch_stock_data()             — Fetch quarterly OHLCV bars from Massive API
#   2. compute_performance_metrics()  — Compute return, volatility, EMA from price data
#   3. get_latest_price()             — Get previous day's close from Massive API

import json
import numpy as np
from datetime import datetime, timedelta


# ═══════════════════════════════════════════════════════════════
# Tool 1: Fetch Stock Data (API Call)
# ═══════════════════════════════════════════════════════════════

def fetch_stock_data(ticker, api_key):
    """
    Fetch 3 years of quarterly OHLCV bars from the Massive API.

    Uses quarterly aggregation (multiplier=3, timespan=month) with raw=True
    to guarantee exactly 1 API call per ticker — no auto-pagination.
    limit=50000 ensures all base daily bars are used to compute quarterly aggs.

    Parameters
    ----------
    ticker : str
        A single stock ticker symbol (e.g. "SOUN")
    api_key : str
        Massive API key

    Returns
    -------
    str
        JSON string with ticker, period, and list of quarterly OHLCV bars
    """
    from massive import RESTClient

    client = RESTClient(api_key=api_key)
    ticker = ticker.strip().upper()

    today = datetime.now().date()
    end_date = today
    start_date = today - timedelta(days=3 * 365)

    try:
        # raw=True → single HTTP response, no auto-pagination
        # limit=50000 → all base daily bars used to compute quarterly aggs
        resp = client.list_aggs(
            ticker=ticker, multiplier=3, timespan="month",
            from_=start_date.strftime("%Y-%m-%d"),
            to=end_date.strftime("%Y-%m-%d"),
            sort="asc", limit=50000, raw=True,
        )

        data = json.loads(resp.data.decode("utf-8"))
        bars = data.get("results", [])

        if not bars:
            return json.dumps({"ticker": ticker, "error": "No data returned"})

        # Extract OHLCV into clean format
        quarterly_bars = []
        for bar in bars:
            t = bar.get("t") or bar.get("timestamp")
            date_str = datetime.fromtimestamp(t / 1000).strftime("%Y-%m") if t else ""
            quarterly_bars.append({
                "quarter": date_str,
                "open": bar.get("o") or bar.get("open"),
                "high": bar.get("h") or bar.get("high"),
                "low": bar.get("l") or bar.get("low"),
                "close": bar.get("c") or bar.get("close"),
                "volume": bar.get("v") or bar.get("volume", 0),
            })

        result = {
            "ticker": ticker,
            "period": f"{start_date} to {end_date}",
            "bars_count": len(quarterly_bars),
            "bars": quarterly_bars,
        }
        return json.dumps(result, indent=2, default=str)

    except Exception as e:
        return json.dumps({"ticker": ticker, "error": str(e)})


# ═══════════════════════════════════════════════════════════════
# Tool 2: Compute Performance Metrics (Computation)
# ═══════════════════════════════════════════════════════════════

def compute_performance_metrics(price_data_json):
    """
    Compute performance metrics from raw quarterly OHLCV bar data.

    Calculates: total return, annualized return, annualized volatility,
    3-year high/low, average quarterly volume, and 2-quarter EMA trend.

    Parameters
    ----------
    price_data_json : str
        JSON string from fetch_stock_data() containing ticker and bars

    Returns
    -------
    str
        JSON string with computed performance metrics
    """
    try:
        data = json.loads(price_data_json)
    except (json.JSONDecodeError, TypeError):
        return json.dumps({"error": "Invalid JSON input"})

    if "error" in data:
        return json.dumps(data)

    ticker = data.get("ticker", "UNKNOWN")
    bars = data.get("bars", [])

    if len(bars) < 2:
        return json.dumps({"ticker": ticker, "error": "Insufficient data for metrics"})

    closes = [b["close"] for b in bars if b.get("close") is not None]
    highs = [b["high"] for b in bars if b.get("high") is not None]
    lows = [b["low"] for b in bars if b.get("low") is not None]
    volumes = [b.get("volume", 0) for b in bars]

    if len(closes) < 2:
        return json.dumps({"ticker": ticker, "error": "Insufficient close data"})

    # Total and annualized return
    total_return = ((closes[-1] - closes[0]) / closes[0]) * 100
    years = len(closes) / 4  # quarterly data
    annualized_return = ((closes[-1] / closes[0]) ** (1 / max(years, 0.5)) - 1) * 100

    # Annualized volatility (from quarterly returns)
    quarterly_returns = [(closes[i] - closes[i-1]) / closes[i-1] for i in range(1, len(closes))]
    volatility = float(np.std(quarterly_returns) * np.sqrt(4) * 100)

    # 3-year high/low
    high_3y = max(highs) if highs else 0
    low_3y = min(lows) if lows else 0

    # Average quarterly volume
    avg_volume = sum(volumes) / len(volumes) if volumes else 0

    # 2-quarter EMA for trend direction
    ema_span = 2
    mult = 2 / (ema_span + 1)
    ema = closes[0]
    for price in closes[1:]:
        ema = price * mult + ema * (1 - mult)

    trend = "bullish" if closes[-1] > ema else "bearish"

    # Quarterly close history for context
    quarterly_closes = [{"quarter": b["quarter"], "close": round(b["close"], 2)}
                        for b in bars if b.get("close") is not None]

    result = {
        "ticker": ticker,
        "period": data.get("period", ""),
        "quarters_of_data": len(closes),
        "first_close": round(closes[0], 2),
        "latest_close": round(closes[-1], 2),
        "total_return_pct": round(total_return, 2),
        "annualized_return_pct": round(annualized_return, 2),
        "annualized_volatility_pct": round(volatility, 2),
        "3_year_high": round(high_3y, 2),
        "3_year_low": round(low_3y, 2),
        "avg_quarterly_volume": round(avg_volume),
        "ema_2q": round(ema, 2),
        "trend": trend,
        "quarterly_closes": quarterly_closes,
    }
    return json.dumps(result, indent=2, default=str)


# ═══════════════════════════════════════════════════════════════
# Tool 3: Get Latest Price (API Call)
# ═══════════════════════════════════════════════════════════════

def get_latest_price(ticker, api_key):
    """
    Get the previous trading day's OHLCV data for a single ticker
    using the Massive API's previous close endpoint.

    This is a lightweight API call (1 call, no pagination) that
    provides the most recent trading day's data.

    Parameters
    ----------
    ticker : str
        A single stock ticker symbol (e.g. "SOUN")
    api_key : str
        Massive API key

    Returns
    -------
    str
        JSON string with previous day open, high, low, close, volume
    """
    from massive import RESTClient

    client = RESTClient(api_key=api_key)
    ticker = ticker.strip().upper()

    try:
        agg = client.get_previous_close_agg(ticker=ticker)
        results = getattr(agg, "results", None)
        if results is None and isinstance(agg, dict):
            results = agg.get("results")

        if results and isinstance(results, list) and len(results) > 0:
            bar = results[0]
            o = getattr(bar, "o", None) or (bar.get("o") if isinstance(bar, dict) else None)
            h = getattr(bar, "h", None) or (bar.get("h") if isinstance(bar, dict) else None)
            l_ = getattr(bar, "l", None) or (bar.get("l") if isinstance(bar, dict) else None)
            c = getattr(bar, "c", None) or (bar.get("c") if isinstance(bar, dict) else None)
            v = getattr(bar, "v", None) or (bar.get("v") if isinstance(bar, dict) else None)

            result = {
                "ticker": ticker,
                "previous_close": round(c, 2) if c else None,
                "previous_open": round(o, 2) if o else None,
                "previous_high": round(h, 2) if h else None,
                "previous_low": round(l_, 2) if l_ else None,
                "previous_volume": v,
                "daily_range_pct": round(((h - l_) / l_) * 100, 2) if h and l_ else None,
            }
            return json.dumps(result, indent=2, default=str)
        else:
            return json.dumps({"ticker": ticker, "error": "No previous close data"})

    except Exception as e:
        return json.dumps({"ticker": ticker, "error": str(e)})


# ═══════════════════════════════════════════════════════════════
# Tool Metadata (for LLM function calling)
# ═══════════════════════════════════════════════════════════════

tool_fetch_stock_data = {
    "type": "function",
    "function": {
        "name": "fetch_stock_data",
        "description": (
            "Fetch 3 years of quarterly OHLCV stock price bars from the "
            "Massive API for a given ticker symbol"
        ),
        "parameters": {
            "type": "object",
            "required": ["ticker"],
            "properties": {
                "ticker": {
                    "type": "string",
                    "description": "Stock ticker symbol (e.g. 'SOUN', 'BBAI')"
                }
            }
        }
    }
}

tool_compute_metrics = {
    "type": "function",
    "function": {
        "name": "compute_performance_metrics",
        "description": (
            "Compute performance metrics (return, volatility, EMA trend) "
            "from raw quarterly OHLCV price data"
        ),
        "parameters": {
            "type": "object",
            "required": ["price_data_json"],
            "properties": {
                "price_data_json": {
                    "type": "string",
                    "description": "JSON string of quarterly OHLCV data from fetch_stock_data()"
                }
            }
        }
    }
}

tool_get_latest_price = {
    "type": "function",
    "function": {
        "name": "get_latest_price",
        "description": (
            "Get the previous trading day's OHLCV data for a stock ticker "
            "from the Massive API"
        ),
        "parameters": {
            "type": "object",
            "required": ["ticker"],
            "properties": {
                "ticker": {
                    "type": "string",
                    "description": "Stock ticker symbol (e.g. 'SOUN', 'BBAI')"
                }
            }
        }
    }
}
