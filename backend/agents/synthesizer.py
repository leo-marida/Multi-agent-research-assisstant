import os
from typing import AsyncGenerator
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

from utils.streaming import sse_event

load_dotenv()

_llm = None

def _get_llm():
    global _llm
    if _llm is None:
        _llm = ChatOpenAI(model="gpt-4.1-mini", temperature=0.3)
    return _llm

_SYSTEM = """You are a research synthesis expert. Given raw source excerpts retrieved from the web, produce a comprehensive, authoritative markdown report.

Format rules (CRITICAL — follow exactly):
- Single blank lines between paragraphs, never double
- Inline citations: [Source Title](url) — always descriptive text, never bare URLs
- Bullet points: tight, no blank lines between items

Structure:
# [Precise, descriptive title for the topic]

## Executive Summary
3-4 sentences covering the most important findings and current state of the topic.

## [Section per subtask — use the subtask title as heading]
3-5 paragraphs per section. Extract and synthesise ALL specific facts, figures, dates, names, and technical details from the source excerpts. Include inline citations. Write with depth — this is for an informed reader who wants complete coverage.

## Key Takeaways
- 5-7 specific, concrete bullet points (not vague generalities)

## References
1. [Title](url)

Write in an authoritative, current tone. Prioritise 2025-2026 information. Include specific details that differentiate this report from a generic overview."""


async def synthesize_report(topic: str, findings: list[dict]) -> AsyncGenerator[str, None]:
    yield sse_event("agent_start", {"agent": "synthesizer", "input": topic})

    findings = [f for f in findings if f.get("finding")]
    if not findings:
        yield sse_event("report_chunk", {"chunk": "# No Results Found\n\nInsufficient sources were found for this topic. Try a different or more specific query."})
        yield sse_event("agent_complete", {"agent": "synthesizer"})
        return

    findings_text = ""
    all_sources = []
    for f in findings:
        findings_text += f"\n\n### {f['title']}\n{f['finding']}\n"
        all_sources.extend(f.get("sources", []))

    sources_text = "\n".join(dict.fromkeys(all_sources))

    prompt = (
        f"Topic: {topic}\n\n"
        f"Source excerpts by subtask:\n{findings_text}\n\n"
        f"All source URLs:\n{sources_text}"
    )

    async for chunk in _get_llm().astream([
        {"role": "system", "content": _SYSTEM},
        {"role": "user", "content": prompt},
    ]):
        if chunk.content:
            yield sse_event("report_chunk", {"chunk": chunk.content})

    yield sse_event("agent_complete", {"agent": "synthesizer"})
