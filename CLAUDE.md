# CLAUDE.md — Nexus: Multi-Agent Research Assistant

## Project Overview

Build **Nexus**, a production-grade multi-agent research assistant. The user submits a research topic or question. Nexus autonomously plans a research strategy, dispatches specialized sub-agents to gather and analyze information, stores findings in a vector database, and synthesizes a structured, cited report — all streamed in real time to a clean frontend UI.

This project must demonstrate, in a non-trivial and visible way:
- RAG pipelines (retrieval-augmented generation from a vector store)
- Tool-calling workflows (LLM invoking structured tools)
- Agent orchestration (planner + specialist sub-agents)
- Vector database integration (pgvector via Supabase or local PostgreSQL)
- Production AI application standards (streaming, error handling, logging, environment config)

The end result must be deployable, demo-able in an interview, and linkable on a resume. Prioritize code quality, clean architecture, and real functionality over feature breadth.

---

## Tech Stack

### Backend
- **Python 3.11+**
- **FastAPI** — REST + SSE streaming endpoints
- **LangChain** — agent orchestration, tool-calling, RAG chain
- **OpenAI API** — GPT-4o for planner and synthesis, GPT-4o-mini for sub-agents
- **pgvector + PostgreSQL** — vector store (use Supabase free tier for hosted, or local Docker PostgreSQL with pgvector extension)
- **LangChain Community** — document loaders, text splitters, vectorstore wrappers
- **Tavily API** — web search tool (free tier, better than raw Google scraping)
- **python-dotenv** — environment config
- **Pydantic v2** — request/response models
- **uvicorn** — ASGI server

### Frontend
- **Next.js 14 (App Router)**
- **TypeScript**
- **Tailwind CSS**
- **shadcn/ui** — for components (use `npx shadcn@latest init`)
- **EventSource API** — consume SSE stream from backend
- **ReactMarkdown** — render the final synthesized report

### Dev & Deployment
- **Docker + docker-compose** — containerize backend + PostgreSQL + pgvector
- **Vercel** — deploy frontend
- **Railway or Render** — deploy backend (free tier)
- **.env.local / .env** — never commit secrets

---

## Project Structure

```
nexus/
├── backend/
│   ├── main.py                  # FastAPI app, routes
│   ├── agents/
│   │   ├── planner.py           # Orchestrator agent
│   │   ├── researcher.py        # Web search sub-agent
│   │   ├── analyst.py           # Document analysis sub-agent
│   │   └── synthesizer.py       # Final report generation
│   ├── tools/
│   │   ├── search_tool.py       # Tavily web search tool
│   │   ├── scrape_tool.py       # URL content fetcher
│   │   └── retrieval_tool.py    # Vector DB retrieval tool
│   ├── rag/
│   │   ├── embeddings.py        # OpenAI embeddings setup
│   │   ├── vectorstore.py       # pgvector connection + ops
│   │   └── ingestion.py         # Document chunking + ingestion pipeline
│   ├── models/
│   │   └── schemas.py           # Pydantic request/response models
│   ├── utils/
│   │   ├── logger.py            # Structured logging
│   │   └── streaming.py         # SSE event helpers
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
├── frontend/
│   ├── app/
│   │   ├── page.tsx             # Main research UI
│   │   ├── layout.tsx
│   │   └── api/                 # Next.js API routes if needed
│   ├── components/
│   │   ├── ResearchInput.tsx     # Topic input + submit
│   │   ├── AgentTimeline.tsx     # Live agent activity stream
│   │   ├── ReportViewer.tsx      # Final markdown report
│   │   └── SourceCard.tsx        # Cited source display
│   ├── lib/
│   │   └── stream.ts            # SSE client logic
│   ├── package.json
│   └── .env.local.example
├── docker-compose.yml
└── README.md
```

---

## Core Architecture — How It Works

### Flow

```
User Input (topic)
    ↓
Planner Agent
    → Breaks topic into 3-5 research subtasks
    → Returns structured JSON plan
    ↓
For each subtask (parallel where possible):
    Researcher Agent
        → Calls search_tool (Tavily) → gets URLs + snippets
        → Calls scrape_tool → fetches full page content
        → Chunks + embeds content → stores in pgvector
    ↓
Analyst Agent
        → Calls retrieval_tool → RAG query against vector store
        → Synthesizes findings per subtask
    ↓
Synthesizer Agent
    → Takes all subtask findings
    → Generates final structured report (markdown)
    → Includes citations with source URLs
    ↓
Stream all of the above via SSE to frontend in real time
```

### Streaming Strategy
Every agent step must emit an SSE event so the frontend shows live progress. Event types:
- `agent_start` — which agent is starting, what subtask
- `tool_call` — which tool is being called, with what input
- `tool_result` — summary of tool result
- `agent_complete` — agent done, output summary
- `report_chunk` — streaming tokens of final report
- `error` — structured error with agent context

---

## Backend Implementation Details

### main.py
```python
# Two endpoints:
# POST /api/research  — accepts { topic: str }, returns SSE stream
# GET  /api/health    — health check
# CORS: allow localhost:3000 and production frontend URL
# Use StreamingResponse with media_type="text/event-stream"
```

### agents/planner.py
```python
# Use ChatOpenAI(model="gpt-4o") with structured output (Pydantic)
# System prompt: You are a research planning expert. Break the user's topic
# into 3-5 focused research subtasks. Return JSON: { subtasks: [{ id, title, query }] }
# Use LangChain's with_structured_output() for reliable JSON
# Emit agent_start and agent_complete SSE events
```

### agents/researcher.py
```python
# Use ChatOpenAI(model="gpt-4o-mini") with tool-calling
# Bind tools: [search_tool, scrape_tool]
# Let the agent decide when to search and when to scrape
# After gathering content, chunk with RecursiveCharacterTextSplitter
# Embed with OpenAIEmbeddings and upsert to pgvector
# Tag each chunk with metadata: { subtask_id, source_url, title }
# Emit tool_call and tool_result SSE events for each tool invocation
```

### agents/analyst.py
```python
# Use ChatOpenAI(model="gpt-4o-mini") with retrieval_tool
# RAG: retrieve top-k chunks for the subtask query from pgvector
# Synthesize a 200-300 word finding with source citations
# Return: { subtask_id, finding, sources: [{ url, title }] }
```

### agents/synthesizer.py
```python
# Use ChatOpenAI(model="gpt-4o") — full model for final output quality
# Input: all analyst findings + sources
# Output: structured markdown report with:
#   - Executive Summary
#   - Section per subtask
#   - Key Takeaways
#   - References list
# Stream the output token by token using astream()
# Emit each chunk as report_chunk SSE event
```

### tools/search_tool.py
```python
# Use TavilySearchResults from langchain_community.tools
# max_results=5, include_raw_content=False
# Wrap as a LangChain @tool with clear docstring
# Return list of { url, title, content_snippet }
```

### tools/scrape_tool.py
```python
# Use AsyncWebCrawler or httpx + BeautifulSoup
# Extract main content only (strip nav, footer, ads)
# Limit to 8000 chars to avoid token overflow
# Handle errors gracefully — return empty string, log warning
```

### tools/retrieval_tool.py
```python
# Wrap pgvector similarity search as a LangChain @tool
# Input: { query: str, subtask_id: str, k: int = 6 }
# Returns top-k chunks with metadata
# Use MMR (maximal marginal relevance) to reduce redundancy
```

### rag/vectorstore.py
```python
# Use PGVector from langchain_community.vectorstores
# CONNECTION_STRING from env: postgresql+psycopg2://user:pass@host/db
# Collection name: "nexus_research_{session_id}" — scope per research session
# Clean up collection after session completes (optional, configurable)
```

### utils/streaming.py
```python
# Helper to format SSE events
# def sse_event(event_type: str, data: dict) -> str:
#     return f"event: {event_type}\ndata: {json.dumps(data)}\n\n"
# Use this consistently across all agents
```

---

## Frontend Implementation Details

### app/page.tsx
- Clean centered layout: Nexus logo/title, subtitle, input area, research button
- State: `isResearching`, `agentEvents[]`, `report`
- On submit: open EventSource to `/api/research`, parse events, update state
- Show `AgentTimeline` while researching, `ReportViewer` when report arrives

### components/AgentTimeline.tsx
- Scrollable feed of agent activity events
- Each event type has a distinct icon and color:
  - `agent_start` → blue, brain icon
  - `tool_call` → amber, wrench icon  
  - `tool_result` → green, check icon
  - `agent_complete` → purple, flag icon
  - `error` → red, alert icon
- Animate new events in with a subtle slide-in
- This is the "wow" component — make it look great

### components/ReportViewer.tsx
- Render final markdown with ReactMarkdown + remark-gfm
- Show sources as cards below the report
- Add a "Copy" button and a "New Research" button
- Subtle fade-in animation when report appears

### lib/stream.ts
```typescript
// openResearchStream(topic: string, callbacks: {
//   onAgentEvent: (event: AgentEvent) => void,
//   onReportChunk: (chunk: string) => void,
//   onComplete: () => void,
//   onError: (err: Error) => void
// }): () => void  ← returns cleanup function
// Use EventSource, parse event.type and JSON.parse(event.data)
```

---

## Environment Variables

### backend/.env.example
```
OPENAI_API_KEY=sk-...
TAVILY_API_KEY=tvly-...
DATABASE_URL=postgresql+psycopg2://postgres:password@localhost:5432/nexus
FRONTEND_URL=http://localhost:3000
```

### frontend/.env.local.example
```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## Docker Setup

### docker-compose.yml
```yaml
# Services:
# - postgres: postgres:16 with pgvector extension
#   - Run: CREATE EXTENSION IF NOT EXISTS vector; on init
#   - Port 5432
# - backend: build from ./backend
#   - Port 8000
#   - depends_on: postgres
#   - env_file: ./backend/.env
# - (frontend runs separately via `npm run dev` or Vercel)
```

### backend/Dockerfile
```dockerfile
# FROM python:3.11-slim
# WORKDIR /app
# COPY requirements.txt .
# RUN pip install --no-cache-dir -r requirements.txt
# COPY . .
# CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## requirements.txt (backend)
```
fastapi==0.111.0
uvicorn[standard]==0.29.0
langchain==0.2.0
langchain-openai==0.1.0
langchain-community==0.2.0
langchain-postgres==0.0.6
openai==1.30.0
tavily-python==0.3.3
pgvector==0.2.5
psycopg2-binary==2.9.9
pydantic==2.7.0
python-dotenv==1.0.1
httpx==0.27.0
beautifulsoup4==4.12.3
```

---

## Critical Implementation Rules

1. **Never block the event loop.** All agent operations must be async. Use `await` throughout. LangChain async methods: `ainvoke()`, `astream()`, `abatch()`.

2. **Always emit SSE events before and after every tool call.** The frontend timeline is the showcase — if tool calls are silent, the demo looks broken.

3. **Scope vector store per session.** Use a `session_id` (UUID) to namespace pgvector collections. This prevents research sessions from bleeding into each other and makes cleanup trivial.

4. **Handle tool errors gracefully.** If Tavily returns nothing or scraping fails, the agent must continue with what it has — never crash the whole pipeline. Log the error, emit an SSE error event, move on.

5. **Chunk size matters.** Use `chunk_size=800, chunk_overlap=100` for `RecursiveCharacterTextSplitter`. Too large = poor retrieval precision. Too small = lost context.

6. **MMR over similarity search.** Use `as_retriever(search_type="mmr")` to avoid retrieving 6 near-identical chunks. Diversity in retrieved context = better synthesis.

7. **Stream the final report token by token.** Use `synthesizer.astream()` and emit each token as a `report_chunk` SSE event. This is the most impressive visible feature of the whole system.

8. **CORS must be configured correctly.** FastAPI CORS middleware must allow the frontend origin and expose the `Content-Type` header for SSE to work in browsers.

9. **Pydantic v2 syntax.** Use `model_config = ConfigDict(...)` not the old `class Config`. LangChain is compatible with Pydantic v2 — don't mix versions.

10. **README must be excellent.** Include: what it does, architecture diagram (ASCII is fine), setup instructions, demo GIF or screenshot, and a "How it demonstrates X" section calling out RAG, tool-calling, agent orchestration, vector DB, and production patterns explicitly. Recruiters read READMEs.

---

## Build Order

Follow this sequence exactly. Do not jump ahead.

1. `docker-compose up -d` — get PostgreSQL + pgvector running
2. `rag/vectorstore.py` — test connection, create extension, verify embeddings work
3. `tools/search_tool.py` + `tools/scrape_tool.py` — test in isolation
4. `tools/retrieval_tool.py` — test RAG retrieval end to end
5. `agents/planner.py` — test structured output, verify JSON plan
6. `agents/researcher.py` — test tool-calling loop, verify chunks land in pgvector
7. `agents/analyst.py` — test RAG retrieval per subtask
8. `agents/synthesizer.py` — test streaming output
9. `utils/streaming.py` + `main.py` — wire SSE endpoint, test with curl
10. Frontend `lib/stream.ts` — connect to SSE, log events to console
11. Frontend `AgentTimeline.tsx` — render live events
12. Frontend `ReportViewer.tsx` — render final report
13. End-to-end test with 3 different topics
14. Docker build + deploy backend to Railway
15. Deploy frontend to Vercel
16. Record demo, write README

---

## Resume Bullet Points (add these once built)

```
Nexus — Multi-Agent Research Assistant
Python, LangChain, OpenAI, FastAPI, pgvector, Next.js, TypeScript

• Architected a multi-agent RAG system where a GPT-4o planner agent orchestrates
  specialized sub-agents across web search, document analysis, and knowledge retrieval,
  producing cited research reports streamed in real time via SSE.
• Implemented tool-calling workflows using LangChain's agent executor with custom
  Tavily search and web scraping tools, enabling autonomous information gathering
  across 3-5 parallel research subtasks per query.
• Built a pgvector-backed RAG pipeline with session-scoped collections, MMR retrieval,
  and OpenAI embeddings, achieving relevant chunk retrieval across dynamically ingested
  web content within a single research session.
• Deployed backend on Railway and frontend on Vercel with Docker-containerized
  PostgreSQL/pgvector, full async FastAPI architecture, and structured SSE event
  streaming for live agent transparency in the UI.
```

---

## What This Project Proves to a Recruiter

| Claim on Resume | Where It's Proved in Nexus |
|---|---|
| RAG Pipelines | Researcher agent ingests + embeds web content; Analyst agent retrieves via MMR |
| Tool-calling workflows | Researcher agent binds and invokes search + scrape tools via LangChain |
| Agent orchestration | Planner → Researcher → Analyst → Synthesizer pipeline with SSE event bus |
| Vector database integration | pgvector collection per session, upsert + similarity search + MMR |
| Production AI applications | FastAPI, async throughout, Docker, deployed, error handling, streaming |
