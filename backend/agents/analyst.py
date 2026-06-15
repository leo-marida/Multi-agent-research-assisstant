from typing import AsyncGenerator

from models.schemas import Subtask
from tools.retrieval_tool import retrieve_context
from utils.streaming import sse_event


async def analyse_subtask(subtask: Subtask, session_id: str) -> AsyncGenerator[str, None]:
    yield sse_event("agent_start", {"agent": "analyst", "subtask_id": subtask.id, "title": subtask.title})
    yield sse_event("tool_call", {"subtask_id": subtask.id, "tool": "retrieve_context", "input": subtask.query})

    chunks = await retrieve_context.ainvoke({
        "query": subtask.query,
        "session_id": session_id,
        "k": 6,
    })

    yield sse_event("tool_result", {
        "subtask_id": subtask.id,
        "tool": "retrieve_context",
        "summary": f"Retrieved {len(chunks)} chunks",
    })

    # Format raw chunks directly — synthesizer handles LLM work
    finding = "\n\n".join(
        f"[Source: {c['source_url']}]\n{c['content']}" for c in chunks
    ) if chunks else ""
    sources = list(dict.fromkeys(c["source_url"] for c in chunks if c["source_url"]))

    yield sse_event("agent_complete", {
        "agent": "analyst",
        "subtask_id": subtask.id,
        "title": subtask.title,
        "finding": finding,
        "sources": sources,
    })
