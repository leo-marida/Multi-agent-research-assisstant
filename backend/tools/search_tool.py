import os
from langchain_core.tools import tool
from langchain_tavily import TavilySearch
from dotenv import load_dotenv

load_dotenv()

_tavily = TavilySearch(max_results=5)


@tool
def search_web(query: str) -> list[dict]:
    """Search the web for information on a topic. Returns a list of results with url, title, and content snippet."""
    try:
        raw = _tavily.invoke(query)
        if isinstance(raw, str):
            return [{"error": raw}]
        results = raw if isinstance(raw, list) else raw.get("results", [])
        return [
            {
                "url": r.get("url", ""),
                "title": r.get("title", ""),
                "content_snippet": r.get("content", ""),
            }
            for r in results
        ]
    except Exception as e:
        return [{"error": f"{type(e).__name__}: {e!r}"}]
