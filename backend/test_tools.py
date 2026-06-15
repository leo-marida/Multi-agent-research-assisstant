"""Run: python test_tools.py"""
import asyncio
from tools.search_tool import search_web
from tools.scrape_tool import scrape_url

SEARCH_QUERY = "LangChain RAG pipeline tutorial"
SCRAPE_URL_OVERRIDE = None  # set to a URL string to scrape a specific page instead


async def main():
    print("=" * 60)
    print(f"1. search_web")
    print(f"   INPUT:  query='{SEARCH_QUERY}'")
    results = search_web.invoke({"query": SEARCH_QUERY})
    if results and "error" in results[0]:
        print(f"   ERROR: {results[0]['error']}")
    else:
        print(f"   OUTPUT: {len(results)} results")
        for i, r in enumerate(results, 1):
            print(f"   [{i}] {r['title'][:65]}")
            print(f"        {r['url']}")
            print(f"        snippet: {r['content_snippet'][:120]}...")

    print()
    print("=" * 60)
    url = SCRAPE_URL_OVERRIDE or (results[0]["url"] if results and "url" in results[0] else None)
    print(f"2. scrape_url")
    if url:
        print(f"   INPUT:  url='{url}'")
        content = await scrape_url.ainvoke({"url": url})
        print(f"   OUTPUT: {len(content)} chars extracted")
        print(f"   Preview:\n   {content[:300]}")
    else:
        print("   Skipped (no URL available)")

    print()
    print("All tool tests passed.")


if __name__ == "__main__":
    asyncio.run(main())
