import os
from typing import AsyncGenerator
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

from models.schemas import Subtask
from tools.retrieval_tool import retrieve_context
from utils.streaming import sse_event

load_dotenv()

_llm = ChatOpenAI(model="gpt-4.1-mini", temperature=0)

_SYSTEM = """You are a senior research analyst. Given retrieved document chunks, write a thorough, detailed finding of 400-600 words.

Requirements:
- Extract ALL relevant facts, statistics, dates, names, and technical details from the sources
- Organise logically: context → key findings → supporting details → implications
- Cite source URLs inline using [text](url) format wherever you reference specific claims
- Include specific numbers, model names, prices, dates — concrete details matter
- Do not pad with filler; every sentence must add information
- End with a 'Sources:' line listing the URLs you cited

Write as if briefing an expert who wants maximum density of information."""


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

    if not chunks:
        yield sse_event("agent_complete", {
            "agent": "analyst",
            "subtask_id": subtask.id,
            "title": subtask.title,
            "finding": "",
            "sources": [],
        })
        return

    context = "\n\n".join(
        f"[Source: {c['source_url']}]\n{c['content']}" for c in chunks
    )

    response = await _llm.ainvoke([
        {"role": "system", "content": _SYSTEM},
        {"role": "user", "content": f"Research query: {subtask.query}\n\nRetrieved context:\n{context}"},
    ])

    finding = response.content
    sources = list({c["source_url"] for c in chunks if c["source_url"]})

    yield sse_event("agent_complete", {
        "agent": "analyst",
        "subtask_id": subtask.id,
        "title": subtask.title,
        "finding": finding,
        "sources": sources,
    })
