import asyncio
import os
from typing import AsyncGenerator
from tavily import TavilyClient
from dotenv import load_dotenv

from models.schemas import Subtask
from rag.ingestion import ingest_content
from utils.streaming import sse_event

load_dotenv()

_tavily = None


def _get_tavily() -> TavilyClient:
    global _tavily
    if _tavily is None:
        _tavily = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
    return _tavily


async def research_subtask(subtask: Subtask, session_id: str) -> AsyncGenerator[str, None]:
    yield sse_event("agent_start", {"agent": "researcher", "subtask_id": subtask.id, "title": subtask.title})

    yield sse_event("tool_call", {
        "subtask_id": subtask.id,
        "tool": "search_web",
        "input": subtask.query[:200],
    })

    try:
        raw = await asyncio.to_thread(
            _get_tavily().search,
            subtask.query,
            include_raw_content=True,
            max_results=5,
        )
        results = raw.get("results", [])
    except Exception as e:
        results = []
        yield sse_event("error", {"subtask_id": subtask.id, "message": f"Search failed: {e}"})

    yield sse_event("tool_result", {
        "subtask_id": subtask.id,
        "tool": "search_web",
        "summary": f"Found {len(results)} results",
    })

    total_chunks = 0
    for r in results:
        content = r.get("raw_content") or r.get("content", "")
        url = r.get("url", "")
        title = r.get("title", url)

        if not content or len(content.strip()) < 100:
            continue

        yield sse_event("tool_call", {
            "subtask_id": subtask.id,
            "tool": "scrape_url",
            "input": url[:200],
        })

        try:
            content = content.replace("\x00", "")
            chunks = await ingest_content(
                content=content[:8000],
                session_id=session_id,
                metadata={"subtask_id": subtask.id, "source_url": url, "title": title},
            )
            total_chunks += chunks
        except Exception:
            chunks = 0

        yield sse_event("tool_result", {
            "subtask_id": subtask.id,
            "tool": "scrape_url",
            "summary": f"Ingested {chunks} chunks from {url[:80]}",
        })

    yield sse_event("agent_complete", {
        "agent": "researcher",
        "subtask_id": subtask.id,
        "chunks_ingested": total_chunks,
    })
