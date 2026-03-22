# lab_rag.py
# Custom RAG Query Workflow — Tech Startup Analyzer
# Danny Atik - SYSEN 5381 Lab
#
# This script demonstrates Retrieval-Augmented Generation (RAG) using a CSV
# of tech startups. A search function retrieves matching companies, and the
# results are passed to a local LLM (via Ollama) to generate analysis.
#
# Data source: startups.csv — 100 fictional tech startups with Name, Industry,
#   Founded, Employees, Revenue, Funding, Stage, HQ, and Description.
#
# Search function: Filters rows where Name, Industry, or Description contain
#   the query (case-insensitive), returning results as JSON.
#
# System prompt: Instructs the LLM to act as a startup analyst, producing a
#   structured markdown report comparing companies on key business metrics.

# 0. SETUP ###################################

## 0.1 Load Packages #################################

import sys
import os
import runpy
import pandas as pd
import json

## 0.2 Working Directory #################################

# Get the directory of the current script
script_dir = os.path.dirname(os.path.abspath(__file__))
# Set working directory to the parent (07_rag) so shared files resolve
parent_dir = os.path.join(script_dir, "..")
os.chdir(parent_dir)

## 0.3 Start Ollama Server (source 01_ollama.py) #################################

# Execute 01_ollama.py to configure environment variables and start ollama serve
ollama_script_path = os.path.join(os.getcwd(), "01_ollama.py")
_ = runpy.run_path(ollama_script_path)

## 0.4 Load Functions #################################

# Add parent directory to path so we can import functions.py
sys.path.insert(0, os.getcwd())
from functions import agent_run

## 0.5 Configuration #################################

MODEL = "smollm2:1.7b"       # small local model
PORT = 11434                  # default Ollama port
OLLAMA_HOST = f"http://localhost:{PORT}"
DOCUMENT = os.path.join(script_dir, "startups.csv")  # path to our CSV data

# 1. SEARCH FUNCTION ###################################

def search(query, document):
    """
    Search the startup CSV for rows matching the query.

    Searches across Name, Industry, and Description columns
    (case-insensitive). Returns matching rows as a JSON string.

    Parameters
    ----------
    query : str
        The search term to look for
    document : str
        Path to the CSV file

    Returns
    -------
    str
        JSON string of matching rows
    """
    df = pd.read_csv(document)

    # Build a mask across multiple columns
    mask = (
        df["Name"].str.contains(query, case=False, na=False)
        | df["Industry"].str.contains(query, case=False, na=False)
        | df["Description"].str.contains(query, case=False, na=False)
    )
    filtered = df[mask]

    result_dict = filtered.to_dict(orient="records")
    return json.dumps(result_dict, indent=2)


# 2. TEST SEARCH FUNCTION ###################################

print("=" * 65)
print("🔍 TESTING SEARCH FUNCTION")
print("=" * 65)
print()

test_result = search("AI", DOCUMENT)
print(f"Query: 'AI'")
print(f"Preview of results:")
print(test_result[:300] + "..." if len(test_result) > 300 else test_result)
print()

# 3. RAG WORKFLOW — QUERY 1: Industry Comparison ###################################

print("=" * 65)
print("📊 RAG QUERY 1: Industry Comparison — 'cybersecurity'")
print("=" * 65)
print()

input_query1 = "cybersecurity"

# Task 1: Retrieve relevant startups
result1 = search(input_query1, DOCUMENT)
print(f"🔎 Search returned {len(json.loads(result1))} result(s)")
print()

# Task 2: LLM generates analysis from the retrieved data
role1 = (
    "You are a startup investment analyst. The user will give you JSON data "
    "about tech startups. Using ONLY the data provided, produce a short markdown "
    "report (under 200 words) that includes:\n"
    "- A title\n"
    "- A brief overview of the company or companies found\n"
    "- Key metrics: revenue, funding, employee count, and funding stage\n"
    "- A one-sentence investment outlook\n"
    "Do not invent information beyond what is in the data."
)

result1_llm = agent_run(role=role1, task=result1, model=MODEL, output="text")

print("📝 LLM Analysis:")
print(result1_llm)
print()

# 4. RAG WORKFLOW — QUERY 2: Company Profile ###################################

print("=" * 65)
print("📊 RAG QUERY 2: Company Profile — 'QuantumLeap'")
print("=" * 65)
print()

input_query2 = "QuantumLeap"

# Task 1: Retrieve the company data
result2 = search(input_query2, DOCUMENT)
print(f"🔎 Search returned {len(json.loads(result2))} result(s)")
print()

# Task 2: LLM generates a company profile
role2 = (
    "You are a tech journalist writing startup profiles. The user will give you "
    "JSON data about a startup. Using ONLY the data provided, write a short "
    "markdown company profile (under 150 words) with:\n"
    "- Company name as heading\n"
    "- A catchy tagline\n"
    "- Key facts: industry, HQ, founding year, team size\n"
    "- What the company does\n"
    "- Notable stats (revenue, funding, stage)\n"
    "Do not invent information beyond what is in the data."
)

result2_llm = agent_run(role=role2, task=result2, model=MODEL, output="text")

print("📝 LLM Company Profile:")
print(result2_llm)
print()

# 5. WORKFLOW SUMMARY ###################################

print("=" * 65)
print("✅ RAG WORKFLOW COMPLETE")
print("=" * 65)
print()
print("Flow: User Query → CSV Search → JSON Results → LLM Analysis")
print()
print("Data source: startups.csv (100 tech startups with business metrics)")
print("Search function: Filters Name, Industry, Description (case-insensitive)")
print("System prompt: Instructs LLM to analyze retrieved data as a startup analyst")
