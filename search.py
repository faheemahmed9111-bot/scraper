"""
Firecrawl Search Module — queries Firecrawl /v2/search to get URLs.
"""

from firecrawl import Firecrawl
from config import FIRECRAWL_API_KEY, MAX_SEARCH_LIMIT


def search_urls(query: str, limit: int = 10, api_key: str = "") -> list[dict]:
    """
    Search for URLs using Firecrawl search endpoint.
    
    Args:
        query: Search query string (supports dork operators like site:, inurl:, intitle:, etc.)
        limit: Number of results to return (max 20)
        api_key: Firecrawl API key (falls back to env var)
    
    Returns:
        List of dicts with keys: url, title, description
    """
    key = api_key or FIRECRAWL_API_KEY
    if not key:
        raise ValueError("FIRECRAWL_API_KEY is not set. Add it to your .env file.")

    limit = min(limit, MAX_SEARCH_LIMIT)

    client = Firecrawl(api_key=key)

    # Only get URLs — no scrapeOptions, Scrapling handles scraping
    try:
        result = client.search(query=query, limit=limit)
    except Exception as e:
        raise Exception(f"Firecrawl search API error: {str(e)}")

    urls = []
    
    # Debug info (will show in terminal where streamlit is running)
    print(f"DEBUG: Search result type: {type(result)}")
    
    # Try to extract web results from the raw result object or dict
    web_results = []
    
    # 1. Try to convert to dict first (handles Pydantic v1 and v2)
    res_dict = {}
    try:
        if hasattr(result, "model_dump"):
            res_dict = result.model_dump()
        elif hasattr(result, "dict"):
            res_dict = result.dict()
        elif isinstance(result, dict):
            res_dict = result
    except Exception:
        pass

    # 2. Look for web results in the dictionary
    if res_dict:
        data = res_dict.get("data")
        if isinstance(data, list):
            web_results = data
        elif isinstance(data, dict):
            web_results = data.get("web", [])
        
        # Some versions might have results directly at top level or under 'results'
        if not web_results:
            web_results = res_dict.get("web") or res_dict.get("results") or []

    # 3. If still nothing, try direct attribute access on the raw object
    if not web_results:
        # Check result.data.web
        data_attr = getattr(result, "data", None)
        if data_attr:
            if isinstance(data_attr, list):
                web_results = data_attr
            else:
                web_results = getattr(data_attr, "web", [])
        
        # Check result.web
        if not web_results:
            web_results = getattr(result, "web", [])

    # 4. Final sanity check: if web_results is not a list, make it empty
    if not isinstance(web_results, list):
        web_results = []

    for item in web_results:
        # Each item could be a dict or an object
        if isinstance(item, dict):
            url = item.get("url") or item.get("link") or ""
            title = item.get("title") or ""
            desc = item.get("description") or item.get("snippet") or ""
        else:
            url = getattr(item, "url", getattr(item, "link", ""))
            title = getattr(item, "title",  "")
            desc = getattr(item, "description", getattr(item, "snippet", ""))
        
        if url:
            urls.append({
                "url": url,
                "title": title,
                "description": desc,
            })

    print(f"DEBUG: Extracted {len(urls)} URLs")
    return urls
