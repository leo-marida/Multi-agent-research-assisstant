"""Run: python test_planner.py"""
import asyncio
from agents.planner import get_plan


async def main():
    topic = "The impact of large language models on software engineering"
    print(f"Topic: {topic}\n")
    print("Planning research...")

    plan = await get_plan(topic)

    print(f"Generated {len(plan.subtasks)} subtasks:\n")
    for s in plan.subtasks:
        print(f"  [{s.id}] {s.title}")
        print(f"         Query: {s.query}")
        print()

    print("Planner test passed.")


if __name__ == "__main__":
    asyncio.run(main())
