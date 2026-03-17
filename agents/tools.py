from langchain_core.tools import tool
import serpapi
import os
import json
from typing import List, Dict, Any

SERPAPI_KEY = os.getenv("SERPAPI_KEY")

@tool
def serp_search(query: str, num_results: int = 12) -> List[Dict[str, Any]]:
   
    """
    Perform a Google search using SerpAPI and return cleaned organic results.
    
    Args:
        query: The search query string
        num_results: Maximum number of results to return (default 12)
    
    Returns:
        List of dictionaries with title, link, snippet, position
    """
   
    if not SERPAPI_KEY:
        return [{"error": "SerpAPI key not set"}]
    
    params = {
        "q": query,
        "api_key": SERPAPI_KEY,
        "num": num_results,
        "tbs": "qdr:m",           # past mounth — "m" for month, etc.
        "hl": "en",
        "gl": "in"
    }

    client = serpapi.Client(api_key=SERPAPI_KEY)
    results = client.search(params)
    organic = results.get("organic_results", [])

    cleaned =[]

    for r in organic[:num_results]:
        cleaned.append({
            "title": r.get("title"),
            "link": r.get("link"),
            "snippet": r.get("snippet"),
            "position": r.get("position")
        })

    return cleaned


# @tool
# def dummy_investor_fallback(sector: str = "", location: str = "India") -> str:
#     """Use only when real search fails — returns tiny hardcoded list for testing."""
#     fallback = [
#         {"name": "Blume Ventures", "focus": "Fintech, Consumer, SaaS", "check_size": "$500k–$2M", "location": "India"},
#         {"name": "3one4 Capital", "focus": "Early-stage tech", "check_size": "$300k–$1.5M", "location": "India"},
#         {"name": "Better Capital", "focus": "Internet-first brands", "check_size": "$100k–$1M", "location": "India"},
#     ]
#     return json.dumps({"investors": fallback[:4], "count": len(fallback), "message": "Fallback data — real search unavailable"})
