"""Run: python test_analyst.py"""
import asyncio, json
from models.schemas import Subtask
from agents.researcher import research_subtask
from agents.analyst import analyse_subtask
from rag.vectorstore import delete_collection

SESSION = "test-analyst-001"

SUBTASK = Subtask(
    id="sub-1",
    title="pgvector overview",
    query="pgvector PostgreSQL vector similarity search",
)


async def main():
    print("Phase 1: Research (ingesting content)...")
    async for _ in research_subtask(SUBTASK, SESSION):
        pass
    print("  Done ingesting.\n")

    print("Phase 2: Analysis (RAG synthesis)...")
    async for event in analyse_subtask(SUBTASK, SESSION):
        for line in event.strip().split("\n"):
            if line.startswith("event:"):
                etype = line.split(":", 1)[1].strip()
            elif line.startswith("data:"):
                data = json.loads(line.split(":", 1)[1].strip())
                if etype == "agent_start":
                    print(f"[START] analyst on [{data['subtask_id']}]")
                elif etype == "tool_call":
                    print(f"  [TOOL] {data['tool']} ← '{data['input'][:60]}'")
                elif etype == "tool_result":
                    print(f"  [RESULT] {data['summary']}")
                elif etype == "agent_complete":
                    print(f"\n[FINDING]\n{data['finding']}\n")
                    print(f"[SOURCES]")
                    for s in data["sources"]:
                        print(f"  - {s}")

    print("\nCleaning up...")
    await delete_collection(SESSION)
    print("Analyst test passed.")


if __name__ == "__main__":
    asyncio.run(main())
