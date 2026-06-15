from typing import AsyncGenerator

from models.schemas import Subtask
from utils.cache import retrieve as cache_retrieve
from utils.streaming import sse_event


async def analyse_subtask(subtask: Subtask, session_id: str) -> AsyncGenerator[str, None]:
    yield sse_event("agent_start", {"agent": "analyst", "subtask_id": subtask.id, "title": subtask.title})
    yield sse_event("tool_call", {"subtask_id": subtask.id, "tool": "retrieve_context", "input": subtask.query})

    # Read from in-memory cache populated by researcher (instant, no DB round-trip)
    cached = cache_retrieve(session_id, subtask.id)

    yield sse_event("tool_result", {
        "subtask_id": subtask.id,
        "tool": "retrieve_context",
        "summary": f"Retrieved {len(cached)} sources",
    })

    finding = "\n\n".join(
        f"[Source: {r['url']}]\n{r['content']}" for r in cached
    ) if cached else ""
    sources = list(dict.fromkeys(r["url"] for r in cached if r["url"]))

    yield sse_event("agent_complete", {
        "agent": "analyst",
        "subtask_id": subtask.id,
        "title": subtask.title,
        "finding": finding,
        "sources": sources,
    })
