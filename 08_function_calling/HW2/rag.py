# rag.py
# HW2: Retrieval-Augmented Generation (RAG) Implementation
# Danny Atik - SYSEN 5381
#
# This module implements RAG search functionality using a CSV data source
# of tech startups. The search function filters rows by matching a query
# against multiple text columns, returning results as JSON for LLM context.

import json
import pandas as pd


def search_startups(query, csv_path):
    """
    Search the startup CSV for rows matching query across Name, Industry,
    and Description columns (case-insensitive).

    This is the RAG retrieval step: given a user query, find relevant
    documents (startup records) to augment the LLM's generation.

    Parameters
    ----------
    query : str
        Search term (e.g. "AI", "fintech", "cybersecurity")
    csv_path : str
        Path to the startups CSV file

    Returns
    -------
    str
        JSON string of matching startup records
    """
    df = pd.read_csv(str(csv_path))
    mask = (
        df["Name"].str.contains(query, case=False, na=False)
        | df["Industry"].str.contains(query, case=False, na=False)
        | df["Description"].str.contains(query, case=False, na=False)
    )
    filtered = df[mask]
    return json.dumps(filtered.to_dict(orient="records"), indent=2)


# Tool metadata for LLM function calling
tool_search_startups = {
    "type": "function",
    "function": {
        "name": "search_startups",
        "description": (
            "Search the startup database for companies matching a keyword "
            "in name, industry, or description"
        ),
        "parameters": {
            "type": "object",
            "required": ["query"],
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search keyword (e.g. 'AI', 'fintech', 'cybersecurity')"
                }
            }
        }
    }
}
