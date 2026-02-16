# lab_massive.py
# AI-Powered Data Reporter (LAB)

# Fetches stock data from Massive API, formats it, and uses Ollama Cloud
# to generate a short market report. Demonstrates API + data processing + AI pipeline.

# 0. Setup #################################

import json
import os
import time
from pathlib import Path

import requests
from dotenv import load_dotenv

# Load .env from this folder or project root
_script_dir = Path(__file__).resolve().parent
load_dotenv(_script_dir / ".env")
load_dotenv(_script_dir.parent / ".env")

OLLAMA_API_KEY = os.getenv("OLLAMA_API_KEY")
MASSIVE_API_KEY = os.getenv("MASSIVE_API_KEY")

if not OLLAMA_API_KEY:
    raise ValueError("OLLAMA_API_KEY not found in .env. Please set it up first.")
if not MASSIVE_API_KEY:
    raise ValueError("MASSIVE_API_KEY not found in .env. Please set it up first.")

# 1. Data Pipeline (Task 1) #################################

# Use Massive API (free tier: previous day bar) to get OHLC data for reporting
from massive import RESTClient

massive_client = RESTClient(api_key=MASSIVE_API_KEY)

# Fetch previous close for a few tickers so the report has enough to summarize
# Free plan: 5 API calls per minute — space requests to avoid rate limit
TICKERS = ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA"]
data_for_report = []

for i, ticker in enumerate(TICKERS):
    agg = massive_client.get_previous_close_agg(ticker=ticker)
    # API returns { ticker, results: [{ o, h, l, c, v, t, ... }] }; client may expose as attributes
    results = getattr(agg, "results", None) or (agg.get("results") if isinstance(agg, dict) else None)
    if results and (isinstance(results, list) and len(results) > 0):
        bar = results[0]
        o = getattr(bar, "o", None) or (bar.get("o") if isinstance(bar, dict) else None)
        h = getattr(bar, "h", None) or (bar.get("h") if isinstance(bar, dict) else None)
        l_ = getattr(bar, "l", None) or (bar.get("l") if isinstance(bar, dict) else None)
        c = getattr(bar, "c", None) or (bar.get("c") if isinstance(bar, dict) else None)
        v = getattr(bar, "v", None) or (bar.get("v") if isinstance(bar, dict) else None)
        data_for_report.append({"ticker": ticker, "open": o, "high": h, "low": l_, "close": c, "volume": v})
    else:
        data_for_report.append({"ticker": ticker, "raw": str(agg)})
    # Stay under 5 requests/min: wait 13s between calls (5 calls in ~1 min)
    if i < len(TICKERS) - 1:
        time.sleep(13)

# Format for AI: structured text so the model can summarize clearly
processed_text = json.dumps(data_for_report, indent=2, default=str)

# 2. AI Prompt (Task 2) #################################

# Prompt asks for a brief report with specific format (bullets, 2–3 insights)
REPORT_PROMPT = f"""You are a market data analyst. Below is previous trading day OHLC data from the Massive API for {", ".join(TICKERS)}.

Data (JSON):
{processed_text}

Write a short market report (2–3 sentences or 3 bullet points) that:
1. Summarizes the previous close levels for these tickers.
2. Notes any notable spread between high and low or volume.
3. Keeps the tone factual and concise.

Do not make up numbers; use only the data provided."""

# 3. Call Ollama Cloud (Task 2) #################################

OLLAMA_CHAT_URL = "https://ollama.com/api/chat"

body = {
    "model": "gpt-oss:20b-cloud",
    "messages": [{"role": "user", "content": REPORT_PROMPT}],
    "stream": False,
}

headers = {
    "Authorization": f"Bearer {OLLAMA_API_KEY}",
    "Content-Type": "application/json",
}

response = requests.post(OLLAMA_CHAT_URL, headers=headers, json=body, timeout=60)
response.raise_for_status()

result = response.json()
report = result.get("message", {}).get("content", "")

# 4. Output (Task 3) #################################

print("\n" + "=" * 60)
print("AI-GENERATED MARKET REPORT (Massive + Ollama Cloud)")
print("=" * 60)
print(report)
print("=" * 60 + "\n")

# Save report as Markdown for readable formatting and GitHub/screenshot
out_path = _script_dir / "report_lab_massive.md"
md_content = f"""# Market Report (Massive + Ollama Cloud)

*Previous trading day summary for {", ".join(TICKERS)}*

---

{report}
"""
with open(out_path, "w", encoding="utf-8") as f:
    f.write(md_content)
print(f"Report saved to {out_path}")
