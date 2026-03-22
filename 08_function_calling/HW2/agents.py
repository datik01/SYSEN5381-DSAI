# agents.py
# HW2: Multi-Agent Orchestration Module
# Danny Atik - SYSEN 5381
#
# This module defines the agent roles, prompts, and orchestration logic
# for the 4-agent investment analysis pipeline. Each agent has a specific
# role and system prompt that controls its behavior.

import json
import re
import time


# ═══════════════════════════════════════════════════════════════
# Agent Role Definitions (System Prompts)
# ═══════════════════════════════════════════════════════════════

# Agent 2: Market Mapper — identifies comparable small-cap tickers
MARKET_MAPPER_PROMPT = (
    "You are a stock market expert specializing in small-cap and micro-cap stocks. "
    "Given a list of startups, identify 3 small-cap or mid-cap publicly-traded "
    "companies that compete in or are comparable to the same markets as these startups.\n\n"
    "IMPORTANT RULES:\n"
    "- Do NOT pick mega-cap stocks like NVDA, GOOGL, MSFT, AMZN, AAPL, META, TSLA\n"
    "- Pick small-cap or mid-cap companies (market cap under $20B) that are closer "
    "comparisons to these startups\n"
    "- Examples of the kind of tickers to pick: BBAI, SOUN, PATH, AI, UPST, BIGC, RKLB, IONQ\n"
    "- They must be real US stock tickers\n"
    "- Pick exactly 3 tickers\n\n"
    "You MUST respond with ONLY a JSON array of ticker symbols, nothing else.\n"
    "Example response: [\"BBAI\", \"SOUN\", \"PATH\"]\n"
)

# Agent 2 (RAG summarizer): Startup Research Analyst
STARTUP_ANALYST_PROMPT = (
    "You are a startup research analyst. The user provides JSON data about "
    "startups. Summarize the landscape in 3-4 bullet points: how many companies, "
    "funding range, key sectors, and standout companies. Be concise. Use only the data provided."
)

# Agent 4: Investment Advisor — synthesizes all data
INVESTMENT_ADVISOR_PROMPT = (
    "You are a senior investment advisor. You receive two data inputs:\n"
    "1) A list of startups in a specific industry from a database\n"
    "2) 3-year quarterly performance data for comparable publicly-traded companies\n\n"
    "Using ONLY the data provided, write an investment analysis (under 400 words) "
    "in markdown format with:\n"
    "- Title: 'Investment Analysis: [Industry] Sector'\n"
    "- Section 1: 'Startup Landscape' — summarize the startups (count, funding "
    "range, stages, key players)\n"
    "- Section 2: 'Public Market Performance' — for each comparable ticker, cite "
    "the total return, annualized return, volatility, 3-year range, and trend from the data\n"
    "- Section 3: 'Market Outlook' — based on public market performance, assess "
    "the market potential for these startups. Are comparable stocks growing? "
    "Is volatility high or low? What does the trend signal?\n"
    "- Section 4: 'Recommendation' — 2-3 actionable sentences synthesizing both "
    "the startup landscape and public market signals\n\n"
    "Do NOT invent data. Cite specific numbers from the inputs."
)

FALLBACK_TICKERS = ["BBAI", "SOUN", "PATH"]


# ═══════════════════════════════════════════════════════════════
# Orchestration Functions
# ═══════════════════════════════════════════════════════════════

def parse_tickers_from_llm(response_text):
    """
    Parse ticker symbols from an LLM response. Handles various formats:
    JSON arrays, JSON objects, or plain text with uppercase tickers.

    Parameters
    ----------
    response_text : str
        Raw text response from the LLM

    Returns
    -------
    list
        List of ticker symbol strings (e.g. ["BBAI", "SOUN", "PATH"])
    """
    comparable_tickers = []

    # Try JSON parse first
    try:
        parsed_response = json.loads(response_text.strip())
        if isinstance(parsed_response, list):
            for item in parsed_response:
                if isinstance(item, str):
                    comparable_tickers.append(item.upper())
                elif isinstance(item, dict):
                    for v in item.values():
                        if isinstance(v, str) and len(v) <= 5:
                            comparable_tickers.append(v.upper())
                            break
        comparable_tickers = comparable_tickers[:3]
    except (json.JSONDecodeError, ValueError):
        pass

    # Fall back to regex extraction
    if len(comparable_tickers) < 2:
        found = re.findall(r'\b([A-Z]{1,5})\b', response_text)
        stop_words = {"THE", "AND", "FOR", "ARE", "BUT", "NOT", "YOU", "ALL",
                      "CAN", "HER", "WAS", "ONE", "OUR", "OUT", "HAS", "JSON",
                      "USD", "ETF", "IPO", "CEO", "API", "LLM", "RAG", "ONLY",
                      "MUST", "FIND", "LIST", "THESE", "THAT", "THIS", "WITH"}
        comparable_tickers = [t for t in found if t not in stop_words][:3]

    # Final fallback
    if not comparable_tickers or len(comparable_tickers) < 2:
        comparable_tickers = FALLBACK_TICKERS

    return comparable_tickers


def run_pipeline(industry_query, agent_run_fn, search_fn,
                 fetch_fn, compute_fn, latest_fn,
                 api_key, csv_path, model="smollm2:1.7b"):
    """
    Execute the 4-agent investment analysis pipeline.

    Agent 1 (RAG): Search startups by industry
    Agent 2 (LLM): Identify comparable small-cap tickers
    Agent 3 (Tool): Fetch data → compute metrics → get latest price
    Agent 4 (LLM): Generate investment analysis

    Parameters
    ----------
    industry_query : str
        Industry keyword to search (e.g. "AI")
    agent_run_fn : callable
        The agent_run function from functions.py
    search_fn : callable
        search_startups() from rag.py
    fetch_fn : callable
        fetch_stock_data() from tools.py
    compute_fn : callable
        compute_performance_metrics() from tools.py
    latest_fn : callable
        get_latest_price() from tools.py
    api_key : str
        Massive API key
    csv_path : str
        Path to startups CSV
    model : str
        Ollama model name

    Returns
    -------
    dict
        Results from all agents
    """

    # ── Agent 1: Research Analyst (RAG) ───────────────────────

    print("=" * 70)
    print(f"🤖 AGENT 1: Research Analyst — RAG Startup Search for '{industry_query}'")
    print("=" * 70)
    print()

    startup_json = search_fn(industry_query, csv_path)
    startups = json.loads(startup_json)
    print(f"✅ Found {len(startups)} startups matching '{industry_query}'")

    for s in startups[:6]:
        stage = s.get("Stage", "?")
        funding = s.get("Funding_M", "?")
        print(f"   • {s.get('Name', '?')} ({s.get('Industry', '?')}) — {stage}, ${funding}M funding")
    if len(startups) > 6:
        print(f"   ... and {len(startups) - 6} more")
    print()

    # ── Agent 2: Market Mapper (LLM) ─────────────────────────

    print("=" * 70)
    print("🤖 AGENT 2: Market Mapper — Finding Comparable Small-Cap Tickers")
    print("=" * 70)
    print()

    startup_summary = []
    for s in startups[:10]:
        startup_summary.append(
            f"- {s.get('Name')}: {s.get('Industry')}, {s.get('Description', '')[:80]}"
        )
    startup_text = "\n".join(startup_summary)

    ticker_response = agent_run_fn(
        role=MARKET_MAPPER_PROMPT,
        task=f"Find 3 comparable public tickers for these startups:\n{startup_text}",
        model=model, output="text"
    )

    comparable_tickers = parse_tickers_from_llm(ticker_response)
    print(f"✅ Comparable public companies: {', '.join(comparable_tickers)}")
    print(f"   (LLM raw: {ticker_response.strip()[:100]})")
    print()

    # ── Agent 3: Data Engineer (3 Tools) ─────────────────────

    print("=" * 70)
    print("🤖 AGENT 3: Data Engineer — Using Tools to Analyze Market Data")
    print("=" * 70)
    print()

    performance_data = []
    latest_prices = []

    for i, ticker in enumerate(comparable_tickers):
        # Tool 1: Fetch raw quarterly data
        print(f"   📡 [{ticker}] Tool 1: fetch_stock_data...", end=" ", flush=True)
        raw_data = fetch_fn(ticker, api_key)
        raw_dict = json.loads(raw_data)
        bars_count = raw_dict.get("bars_count", 0)
        print(f"{bars_count} quarterly bars")

        # Tool 2: Compute performance metrics
        print(f"   📊 [{ticker}] Tool 2: compute_performance_metrics...", end=" ", flush=True)
        metrics = compute_fn(raw_data)
        metrics_dict = json.loads(metrics)
        performance_data.append(metrics_dict)

        if "error" not in metrics_dict:
            ret = metrics_dict.get("total_return_pct", "?")
            vol = metrics_dict.get("annualized_volatility_pct", "?")
            trend = metrics_dict.get("trend", "?")
            print(f"Return: {ret}% | Vol: {vol}% | {trend}")
        else:
            print(f"Error: {metrics_dict.get('error')}")

        # Tool 3: Get latest price
        print(f"   💲 [{ticker}] Tool 3: get_latest_price...", end=" ", flush=True)
        latest = latest_fn(ticker, api_key)
        latest_dict = json.loads(latest)
        latest_prices.append(latest_dict)

        if "error" not in latest_dict:
            close = latest_dict.get("previous_close", "?")
            rng = latest_dict.get("daily_range_pct", "?")
            print(f"Close: ${close} | Day range: {rng}%")
        else:
            print(f"Error: {latest_dict.get('error')}")

        # Rate limit between tickers
        if i < len(comparable_tickers) - 1:
            print("   ⏳ Waiting for rate limit...")
            time.sleep(20)

    performance_json = json.dumps(performance_data, indent=2, default=str)
    latest_json = json.dumps(latest_prices, indent=2, default=str)
    print()

    # ── Agent 4: Investment Advisor (LLM Synthesis) ──────────

    print("=" * 70)
    print("🤖 AGENT 4: Investment Advisor — Generating Investment Analysis")
    print("=" * 70)
    print()

    combined_input = (
        f"=== STARTUP DATABASE RESULTS ({industry_query}) ===\n"
        f"{startup_json[:3000]}\n\n"
        f"=== PUBLIC MARKET COMPARABLE PERFORMANCE (3 YEARS, QUARTERLY) ===\n"
        f"{performance_json}\n\n"
        f"=== LATEST TRADING DAY PRICES ===\n"
        f"{latest_json}"
    )

    analysis = agent_run_fn(
        role=INVESTMENT_ADVISOR_PROMPT,
        task=combined_input, model=model, output="text"
    )

    print("📝 Investment Analysis:")
    print(analysis)
    print()

    return {
        "industry": industry_query,
        "startups": startups,
        "startup_json": startup_json,
        "comparable_tickers": comparable_tickers,
        "performance_data": performance_data,
        "latest_prices": latest_prices,
        "performance_json": performance_json,
        "analysis": analysis,
    }

