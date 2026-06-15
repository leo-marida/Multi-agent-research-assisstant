import os
from typing import AsyncGenerator
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

from models.schemas import ResearchPlan
from utils.streaming import sse_event

load_dotenv()

_llm = None

def _get_llm():
    global _llm
    if _llm is None:
        _llm = ChatOpenAI(model="gpt-4.1", temperature=0).with_structured_output(ResearchPlan)
    return _llm

_SYSTEM = """You are a senior research strategist. Given a research topic, design exactly 3 comprehensive subtasks that together cover the full breadth of the subject.

Rules:
- Each subtask must target a distinct angle: e.g. (1) current state / specs / features, (2) analysis / comparison / context, (3) implications / outlook / expert views
- Each query must be specific and include "2026" to retrieve up-to-date information
- IDs must be: sub-1, sub-2, sub-3
- Queries should be long-tail and detailed, not generic — assume a well-informed researcher needs depth
Return only valid JSON matching the schema."""


async def plan_research(topic: str) -> AsyncGenerator[str, None]:
    yield sse_event("agent_start", {"agent": "planner", "input": topic})

    plan: ResearchPlan = await _get_llm().ainvoke([
        {"role": "system", "content": _SYSTEM},
        {"role": "user", "content": f"Research topic: {topic}"},
    ])

    yield sse_event("agent_complete", {
        "agent": "planner",
        "subtasks": [s.model_dump() for s in plan.subtasks],
    })


async def get_plan(topic: str) -> ResearchPlan:
    return await _get_llm().ainvoke([
        {"role": "system", "content": _SYSTEM},
        {"role": "user", "content": f"Research topic: {topic}"},
    ])
