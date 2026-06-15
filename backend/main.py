import os
import uuid
import asyncio
import json
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from dotenv import load_dotenv

from models.schemas import ResearchRequest
from agents.planner import get_plan
from agents.researcher import research_subtask
from agents.analyst import analyse_subtask
from agents.synthesizer import synthesize_report
from rag.vectorstore import delete_collection
from utils.streaming import sse_event

load_dotenv()

app = FastAPI(title="Nexus Research API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        os.getenv("FRONTEND_URL", "http://localhost:3000"),
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


async def collect_agent_events(gen) -> tuple[list[str], dict]:
    """Drain an async generator, collect SSE strings and the final agent_complete payload."""
    events = []
    payload = {}
    async for event in gen:
        events.append(event)
        for line in event.strip().split("\n"):
            if line.startswith("data:"):
                try:
                    payload = json.loads(line.split(":", 1)[1].strip())
                except Exception:
                    pass
    return events, payload


async def run_research_pipeline(topic: str):
    session_id = str(uuid.uuid4())
    queue: asyncio.Queue = asyncio.Queue()

    async def enqueue(gen):
        async for event in gen:
            await queue.put(event)

    try:
        # Step 1: Plan
        yield sse_event("agent_start", {"agent": "planner", "input": topic})
        plan = await get_plan(topic)
        yield sse_event("agent_complete", {
            "agent": "planner",
            "subtasks": [s.model_dump() for s in plan.subtasks],
        })

        # Step 2: Research all subtasks in parallel
        research_tasks = [
            asyncio.create_task(enqueue(research_subtask(subtask, session_id)))
            for subtask in plan.subtasks
        ]
        sentinel = object()

        async def drain_queue():
            await asyncio.gather(*research_tasks)
            await queue.put(sentinel)

        drain_task = asyncio.create_task(drain_queue())
        while True:
            item = await queue.get()
            if item is sentinel:
                break
            yield item
        await drain_task

        # Step 3: Analyse all subtasks in parallel
        analyse_queue: asyncio.Queue = asyncio.Queue()

        async def enqueue_analyse(gen):
            async for event in gen:
                await analyse_queue.put(event)

        analyse_tasks = [
            asyncio.create_task(enqueue_analyse(analyse_subtask(subtask, session_id)))
            for subtask in plan.subtasks
        ]

        async def drain_analyse():
            await asyncio.gather(*analyse_tasks)
            await analyse_queue.put(sentinel)

        drain_analyse_task = asyncio.create_task(drain_analyse())

        findings = []
        while True:
            item = await analyse_queue.get()
            if item is sentinel:
                break
            yield item
            for line in item.strip().split("\n"):
                if line.startswith("data:"):
                    try:
                        data = json.loads(line.split(":", 1)[1].strip())
                        if data.get("agent") == "analyst" and data.get("finding"):
                            findings.append({
                                "title": data.get("title", ""),
                                "finding": data.get("finding", ""),
                                "sources": data.get("sources", []),
                            })
                    except Exception:
                        pass
        await drain_analyse_task

        # Step 4: Synthesize
        async for event in synthesize_report(topic, findings):
            yield event

    except Exception as e:
        yield sse_event("error", {"message": str(e), "type": type(e).__name__})
    finally:
        await delete_collection(session_id)
        yield sse_event("done", {"session_id": session_id})


@app.post("/api/research")
async def research(request: ResearchRequest):
    return StreamingResponse(
        run_research_pipeline(request.topic),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@app.get("/api/health")
async def health():
    return {"status": "ok"}


@app.get("/api/sse-test")
async def sse_test():
    async def _gen():
        for i in range(3):
            yield sse_event("ping", {"i": i})
    return StreamingResponse(_gen(), media_type="text/event-stream")
