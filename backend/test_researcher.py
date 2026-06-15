"""Run: python test_researcher.py"""
import asyncio
from models.schemas import Subtask
from agents.researcher import research_subtask
from rag.vectorstore import delete_collection

SESSION = "test-researcher-001"


async def main():
    subtask = Subtask(
        id="sub-1",
        title="pgvector overview",
        query="pgvector PostgreSQL vector similarity search tutorial",
    )

    print(f"Researching: [{subtask.id}] {subtask.title}\n")

    async for event in research_subtask(subtask, SESSION):
        import json
        parsed = {}
        for line in event.strip().split("\n"):
            if line.startswith("event:"):
                parsed["type"] = line.split(":", 1)[1].strip()
            elif line.startswith("data:"):
                parsed["data"] = json.loads(line.split(":", 1)[1].strip())
        if parsed:
            t = parsed.get("type", "")
            d = parsed.get("data", {})
            if t == "agent_start":
                print(f"[START] {d.get('title', '')}")
            elif t == "tool_call":
                print(f"  [TOOL] {d.get('tool')} ← {d.get('input', '')[:80]}")
            elif t == "tool_result":
                print(f"  [RESULT] {d.get('tool')} → {d.get('summary', '')[:80]}")
            elif t == "agent_complete":
                print(f"[DONE] chunks ingested: {d.get('chunks_ingested')}")

    print("\nCleaning up...")
    await delete_collection(SESSION)
    print("Researcher test passed.")


if __name__ == "__main__":
    asyncio.run(main())
