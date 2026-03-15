# my_2agent_chain.py
# Simple 2-Agent Chain Workflow
# Danny Atik - SYSEN 5381

# This script demonstrates a 2-agent sequential workflow where:
#   Agent 1 (Data Summarizer): Takes raw data and produces a concise summary
#   Agent 2 (Report Writer):   Takes the summary and produces a formatted executive brief

# 0. SETUP ###################################

import os
from functions import agent_run

# Select model - using 1.7b for better output quality
MODEL = "smollm2:1.7b"

# 1. RAW DATA (simulated) ###################################

# Simulate a raw dataset as text (imagine this came from a CSV or API)
raw_data = """
Product        | Q1 Sales | Q2 Sales | Q3 Sales | Q4 Sales | Region
---------------|----------|----------|----------|----------|--------
Widget A       |   12000  |   15000  |   9000   |   22000  | Northeast
Widget B       |    8000  |    7500  |   8200   |    9000  | Southeast
Widget C       |   25000  |   28000  |   30000  |   35000  | West
Gadget X       |    5000  |    4000  |   3500   |    2000  | Midwest
Gadget Y       |   18000  |   20000  |   22000  |   24000  | Northeast
Service Plan Z |    3000  |    3500  |   4000   |    5500  | National
"""

print("=" * 60)
print("📊 RAW DATA INPUT")
print("=" * 60)
print(raw_data)

# 2. AGENT 1 — Data Summarizer ###################################

print("=" * 60)
print("🤖 AGENT 1: Data Summarizer")
print("=" * 60)

role1 = (
    "You are a data analyst. You receive raw sales data and produce "
    "a concise bullet-point summary that highlights: total revenue per product, "
    "the best and worst performing products, notable trends across quarters, "
    "and any regional patterns. Keep it factual and brief."
)

task1 = f"Please analyze the following quarterly sales data:\n{raw_data}"

# Run Agent 1
result1 = agent_run(role=role1, task=task1, model=MODEL, output="text")

print(result1)
print()

# 3. AGENT 2 — Report Writer ###################################

print("=" * 60)
print("📝 AGENT 2: Executive Report Writer")
print("=" * 60)

role2 = (
    "You are an executive report writer. You receive a data analysis summary "
    "and produce a short, polished executive brief (3-4 paragraphs max). "
    "Use a professional tone. Include a clear recommendation at the end. "
    "Format with a title and sign off as 'Strategic Analytics Team'."
)

task2 = f"Write an executive brief based on this analysis:\n\n{result1}"

# Run Agent 2 — its input is Agent 1's output
result2 = agent_run(role=role2, task=task2, model=MODEL, output="text")

print(result2)

# 4. FINAL OUTPUT ###################################

print()
print("=" * 60)
print("✅ WORKFLOW COMPLETE — Agent chain executed successfully")
print("=" * 60)
print()
print("Agent 1 output was passed as input to Agent 2.")
print("This demonstrates sequential multi-agent orchestration.")
