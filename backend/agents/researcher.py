import os
from typing import AsyncGenerator
from langchain_openai import ChatOpenAI
from langchain_core.messages import ToolMessage
from dotenv import load_dotenv

from models.schemas import Subtask
from tools.search_tool import search_web
from tools.scrape_tool import scrape_url
from rag.ingestion import ingest_content
from utils.streaming import sse_event

load_dotenv()

_llm = None

def _get_llm():
    global _llm
    if _llm is None:
        _llm = ChatOpenAI(model="gpt-4.1-mini", temperature=0).bind_tools([search_web, scrape_url])
    return _llm

_SYSTEM = """You are a thorough web research agent. Given a research query:
1. Call search_web once to retrieve results.
2. Evaluate each result's relevance. Call scrape_url on the 3 most informative, distinct URLs — prioritise primary sources, official announcements, expert analyses and recent articles over thin aggregator pages.
3. Stop after scraping. Do not search again."""


async def research_subtask(subtask: Subtask, session_id: str) -> AsyncGenerator[str, None]:
    yield sse_event("agent_start", {"agent": "researcher", "subtask_id": subtask.id, "title": subtask.title})

    messages = [
        {"role": "system", "content": _SYSTEM},
        {"role": "user", "content": f"Research query: {subtask.query}"},
    ]

    total_chunks = 0
    searched = False

    for _ in range(6):
        response = await _get_llm().ainvoke(messages)
        messages.append(response)

        if not response.tool_calls:
            break

        for tc in response.tool_calls:
            yield sse_event("tool_call", {
                "subtask_id": subtask.id,
                "tool": tc["name"],
                "input": str(tc["args"])[:200],
            })

            if tc["name"] == "search_web":
                result = search_web.invoke(tc["args"])
                searched = True
                # if no results, abort early
                if not result or (len(result) == 1 and "error" in result[0]):
                    yield sse_event("tool_result", {"subtask_id": subtask.id, "tool": tc["name"], "summary": "No results found"})
                    messages.append(ToolMessage(content="No results found.", tool_call_id=tc["id"]))
                    break

            elif tc["name"] == "scrape_url":
                result = await scrape_url.ainvoke(tc["args"])
                if isinstance(result, str) and not result.startswith("["):
                    url = tc["args"].get("url", "")
                    chunks = await ingest_content(
                        content=result,
                        session_id=session_id,
                        metadata={"subtask_id": subtask.id, "source_url": url, "title": url},
                    )
                    total_chunks += chunks
            else:
                result = "unknown tool"

            yield sse_event("tool_result", {
                "subtask_id": subtask.id,
                "tool": tc["name"],
                "summary": str(result)[:200],
            })
            messages.append(ToolMessage(content=str(result), tool_call_id=tc["id"]))

    yield sse_event("agent_complete", {
        "agent": "researcher",
        "subtask_id": subtask.id,
        "chunks_ingested": total_chunks,
    })
