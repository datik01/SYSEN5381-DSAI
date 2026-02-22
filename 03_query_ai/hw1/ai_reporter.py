# ai_reporter.py
# AI-Powered Report Generator (Ollama Cloud)
# Pairs with LAB 3 (AI reporter). Generates short market summaries from Massive data.

# Accepts structured OHLC data (list of dicts from api_query) and calls Ollama Cloud
# to produce a brief factual report. Used by the Streamlit app and runnable standalone.

# 0. Setup #################################

import json
import os
from pathlib import Path
from typing import Union

import requests
from dotenv import load_dotenv

# Load .env from hw1 or 03_query_ai
_script_dir = Path(__file__).resolve().parent
load_dotenv(_script_dir / ".env")
load_dotenv(_script_dir.parent / ".env")

OLLAMA_CHAT_URL = "https://ollama.com/api/chat"


def _get_ollama_key() -> str:
    """Require OLLAMA_API_KEY only when generating a report."""
    key = os.getenv("OLLAMA_API_KEY")
    if not key:
        raise ValueError(
            "OLLAMA_API_KEY not found in .env. Add OLLAMA_API_KEY=your_key to "
            "03_query_ai/hw1/.env or 03_query_ai/.env (Ollama Cloud key)."
        )
    return key


def generate_report(data: Union[list, dict], tickers_label: str = "") -> str:
    """
    Generate a short market report from OHLC data using Ollama Cloud.
    data: list of dicts with keys ticker, open, high, low, close, volume (or single dict).
    tickers_label: optional comma-separated ticker names for the prompt.
    Returns the report text from the model.
    """
    if isinstance(data, dict):
        data = [data]
    if not data:
        return "No data provided to generate a report."

    # Build label from data if not provided
    if not tickers_label:
        tickers_label = ", ".join(d.get("ticker", "?") for d in data)

    processed_text = json.dumps(data, indent=2, default=str)

    prompt = f"""You are a professional Technical Analyst. Below is recent trading data for {tickers_label}, which includes technical indicators (20-day SMA, 9-day EMA, and 14-day RSI).

Data (JSON):
{processed_text}

Analyze the data and provide a highly scannable, actionable Technical Analysis report.
Structure your report EXACTLY like this:

📈 Trend: (State if the current trend is Bullish, Bearish, or Neutral based on the moving averages and price action)
🎯 Key Levels: (Identify one potential support and one potential resistance level based on recent highs/lows)
📊 Momentum: (Assess the momentum based on RSI and volume - state if overbought/oversold)
💡 Trading Bias: (Provide a one-sentence actionable bias or takeaway)

CRITICAL FORMATTING INSTRUCTIONS:
- Do NOT use markdown formatting like asterisks (** or *) for bolding or italics.
- Present plain text sentences only.
- Do not make up numbers; use only the data provided."""

    body = {
        "model": "gpt-oss:20b-cloud",
        "messages": [{"role": "user", "content": prompt}],
        "stream": False,
    }
    api_key = _get_ollama_key()
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    response = requests.post(OLLAMA_CHAT_URL, headers=headers, json=body, timeout=60)
    response.raise_for_status()

    result = response.json()
    report = result.get("message", {}).get("content", "")
    return report.strip() if report else "No report generated."


# Script entry: fetch one ticker via api_query and generate report #################################

if __name__ == "__main__":
    # Avoid circular import by importing here when run as script
    from api_query import get_stock_data

    print("--- AI Reporter (Ollama Cloud) ---")
    data = get_stock_data("AAPL")
    report = generate_report(data)
    print(report)
    print("---")
