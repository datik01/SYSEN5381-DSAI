# lab_multi_agent.py
# Multi-Agent System with Tools — Stock Market EMA Analyzer
# Danny Atik - SYSEN 5381 Lab
#
# This script builds a 2-agent workflow using function calling:
#   Agent 1 (Data Fetcher): Uses a tool to call the Massive API, fetch
#     recent stock data, and compute an Exponential Moving Average (EMA).
#   Agent 2 (Market Analyst): Takes the processed data and generates a
#     markdown market analysis report via the LLM.
#
# Tool function: fetch_stock_with_ema() — Calls Massive API to fetch daily
#   OHLCV bars for the last full trading week across multiple tickers and
#   computes an EMA on daily closing prices. Returns JSON-formatted results.
#
# Agent workflow: Agent 1 uses the tool to retrieve and process data, then
#   Agent 2 (an LLM without tools) interprets the results into a readable
#   market report with trend signals and key observations.

# 0. SETUP ###################################

## 0.1 Load Packages #################################

import sys
import os
import json
import time

import requests
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv

## 0.2 Working Directory #################################

script_dir = Path(__file__).resolve().parent
os.chdir(script_dir.parent)  # change to 08_function_calling/

## 0.3 Load Environment Variables #################################

# Load .env from project root
load_dotenv(script_dir.parent.parent / ".env")

MASSIVE_API_KEY = os.getenv("MASSIVE_API_KEY")
if not MASSIVE_API_KEY:
    raise ValueError("MASSIVE_API_KEY not found in .env. Please set it up first.")

## 0.4 Start Ollama Server #################################

import runpy
ollama_script_path = os.path.join(os.getcwd(), "01_ollama.py")
_ = runpy.run_path(ollama_script_path)

## 0.5 Load Functions #################################

sys.path.insert(0, os.getcwd())
from functions import agent_run, df_as_text
import functions as _fn

## 0.6 Configuration #################################

MODEL = "smollm2:1.7b"
PORT = 11434
OLLAMA_HOST = f"http://localhost:{PORT}"


# 1. DEFINE TOOL FUNCTION ###################################

def fetch_stock_with_ema(tickers="AAPL,MSFT,GOOGL", ema_span=5):
    """
    Fetch daily OHLCV data for the last full trading week from the Massive API
    and compute an Exponential Moving Average (EMA) on daily close prices.

    Parameters
    ----------
    tickers : str
        Comma-separated stock ticker symbols (e.g. "AAPL,MSFT,GOOGL")
    ema_span : int
        The span (number of periods) for the EMA calculation (default: 5)

    Returns
    -------
    str
        JSON string with daily stock data and EMA values per ticker
    """
    from massive import RESTClient
    from datetime import datetime, timedelta

    client = RESTClient(api_key=MASSIVE_API_KEY)
    ticker_list = [t.strip().upper() for t in tickers.split(",")]

    # Determine last full trading week (Mon–Fri)
    today = datetime.now().date()
    # Walk back to most recent Friday
    days_since_friday = (today.weekday() - 4) % 7
    if days_since_friday == 0 and today.weekday() != 4:
        days_since_friday = 7
    last_friday = today - timedelta(days=days_since_friday)
    last_monday = last_friday - timedelta(days=4)

    from_date = last_monday.strftime("%Y-%m-%d")
    to_date = last_friday.strftime("%Y-%m-%d")

    all_data = []

    for i, ticker in enumerate(ticker_list):
        try:
            bars = list(client.list_aggs(
                ticker=ticker,
                multiplier=1,
                timespan="day",
                from_=from_date,
                to=to_date,
                sort="asc",
                limit=10,
            ))

            if bars:
                closes = []
                for bar in bars:
                    o = getattr(bar, "open", None) or getattr(bar, "o", None)
                    h = getattr(bar, "high", None) or getattr(bar, "h", None)
                    l_ = getattr(bar, "low", None) or getattr(bar, "l", None)
                    c = getattr(bar, "close", None) or getattr(bar, "c", None)
                    v = getattr(bar, "volume", None) or getattr(bar, "v", None)
                    t = getattr(bar, "timestamp", None) or getattr(bar, "t", None)

                    # Convert timestamp (ms) to date string
                    date_str = ""
                    if t:
                        date_str = datetime.fromtimestamp(t / 1000).strftime("%Y-%m-%d")

                    entry = {
                        "ticker": ticker,
                        "date": date_str,
                        "open": o,
                        "high": h,
                        "low": l_,
                        "close": c,
                        "volume": v,
                    }
                    all_data.append(entry)
                    if c is not None:
                        closes.append(c)

                # Compute EMA on this ticker's daily closes
                if len(closes) >= 2:
                    multiplier = 2 / (ema_span + 1)
                    ema_values = [closes[0]]
                    for price in closes[1:]:
                        ema_values.append(price * multiplier + ema_values[-1] * (1 - multiplier))

                    # Attach EMA to each daily entry for this ticker
                    ema_idx = 0
                    for entry in all_data:
                        if entry["ticker"] == ticker and entry.get("close") is not None:
                            entry["ema"] = round(ema_values[ema_idx], 2)
                            entry["ema_span"] = ema_span
                            entry["ema_vs_close"] = "above" if entry["close"] > ema_values[ema_idx] else "below"
                            ema_idx += 1
            else:
                all_data.append({"ticker": ticker, "error": "No data returned"})

        except Exception as e:
            all_data.append({"ticker": ticker, "error": str(e)})

        # Rate limit: free plan allows 5 API calls/min
        if i < len(ticker_list) - 1:
            time.sleep(13)

    # Add metadata about the date range
    summary = {
        "period": f"{from_date} to {to_date}",
        "tickers": ticker_list,
        "ema_span": ema_span,
        "daily_bars": all_data,
    }

    return json.dumps(summary, indent=2, default=str)


# Register tool function in functions module's global scope
_fn.fetch_stock_with_ema = fetch_stock_with_ema

# 2. DEFINE TOOL METADATA ###################################

tool_fetch_stock = {
    "type": "function",
    "function": {
        "name": "fetch_stock_with_ema",
        "description": "Fetch daily OHLCV stock data for the last full trading week from Massive API and compute an Exponential Moving Average (EMA) on closing prices",
        "parameters": {
            "type": "object",
            "required": ["tickers"],
            "properties": {
                "tickers": {
                    "type": "string",
                    "description": "Comma-separated stock ticker symbols, e.g. 'AAPL,MSFT,GOOGL'"
                },
                "ema_span": {
                    "type": "number",
                    "description": "The EMA span/period for calculation. Default is 5."
                }
            }
        }
    }
}

# 3. MULTI-AGENT WORKFLOW ###################################

print("=" * 65)
print("📈 MULTI-AGENT STOCK MARKET EMA ANALYZER")
print("=" * 65)
print()

# --- Agent 1: Data Fetcher (with tool) ---
print("=" * 65)
print("🤖 AGENT 1: Data Fetcher — Calling Massive API")
print("=" * 65)
print()

# Instead of relying on the LLM to invoke the tool (which may not pass
# the right tickers), we call the tool directly for reliability.
# This mirrors how 04_multiple_agents_with_function_calling.py handles it.
TICKERS = "AAPL,MSFT,GOOGL,AMZN,NVDA"

result1 = fetch_stock_with_ema(tickers=TICKERS, ema_span=5)

print(f"✅ Fetched data for: {TICKERS}")
print(f"📊 Data preview:")
print(result1[:400] + "..." if len(result1) > 400 else result1)
print()

# --- Agent 2: Market Analyst (no tools, LLM-only) ---
print("=" * 65)
print("🤖 AGENT 2: Market Analyst — Generating Report")
print("=" * 65)
print()

role2 = (
    "You are a stock market analyst. The user will give you JSON data containing "
    "daily OHLCV stock data for the last full trading week with Exponential Moving "
    "Average (EMA) values per ticker. Using ONLY the data provided, write a concise "
    "markdown market report (under 300 words) that includes:\n"
    "- A title: 'Weekly Market Summary' with the date range\n"
    "- For each ticker: the weekly trend (up/down), Friday close, Friday EMA, and total weekly volume\n"
    "- 2-3 bullet points with key observations (biggest weekly mover, highest volume day, EMA crossover signals)\n"
    "- A one-sentence overall market outlook\n"
    "Do NOT invent data. Use only what is provided."
)

result2 = agent_run(role=role2, task=result1, model=MODEL, output="text")

print("📝 LLM Market Report:")
print(result2)
print()

# 4. WORKFLOW SUMMARY ###################################

print("=" * 65)
print("✅ WORKFLOW COMPLETE")
print("=" * 65)
print()
print("Flow: User Request → Agent 1 (Massive API + EMA Tool) → Agent 2 (LLM Market Report)")
print()
print("Tool: fetch_stock_with_ema() — fetches OHLCV data and computes EMA")
print("Agent 1: Calls tool to retrieve and process stock data")
print("Agent 2: Analyzes data and writes a structured market report")

# 5. SAVE REPORT AS MARKDOWN ###################################

report_path = script_dir / "report_market_ema.md"
md_content = f"""# Weekly Market EMA Report

*Generated by Multi-Agent Stock Market EMA Analyzer*
*Data period: last full trading week — tickers: {TICKERS}*

---

{result2}
"""
with open(report_path, "w", encoding="utf-8") as f:
    f.write(md_content)

print()
print(f"📄 Report saved to {report_path}")
