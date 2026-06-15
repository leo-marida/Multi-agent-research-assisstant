"""
In-memory research cache scoped by session and subtask.
Researcher stores results here; analyst reads from here.
This avoids a pgvector round-trip on the hot path.
"""
from typing import TypedDict

_cache: dict[str, list[dict]] = {}


class ResultItem(TypedDict):
    url: str
    title: str
    content: str


def store(session_id: str, subtask_id: str, results: list[ResultItem]) -> None:
    _cache[f"{session_id}:{subtask_id}"] = results


def retrieve(session_id: str, subtask_id: str) -> list[ResultItem]:
    return _cache.pop(f"{session_id}:{subtask_id}", [])
