# Nexus — Multi-Agent Research Assistant

![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688?logo=fastapi)
![LangChain](https://img.shields.io/badge/LangChain-0.2-1C3C3C)
![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4.1-412991?logo=openai)
![pgvector](https://img.shields.io/badge/pgvector-PostgreSQL-336791?logo=postgresql)
![Next.js](https://img.shields.io/badge/Next.js-14-black?logo=next.js)
![TypeScript](https://img.shields.io/badge/TypeScript-5-3178C6?logo=typescript)

> A production-grade AI research assistant. Submit a topic — Nexus autonomously plans a research strategy, dispatches parallel web-search agents, stores findings in a vector database, retrieves them with MMR, and streams a cited, structured report back to you in real time.

---

## Architecture

```
User Input (research topic)
        │
        ▼
┌───────────────────┐
│   Planner Agent   │  GPT-4.1 · structured output
│                   │  → 3 focused research subtasks
└────────┬──────────┘
         │ parallel asyncio tasks
   ┌─────┼─────┐
   ▼     ▼     ▼
 ┌───┐ ┌───┐ ┌───┐   Researcher Agents (GPT-4.1-mini)
 │ R1│ │ R2│ │ R3│   tool-calling: search_web → scrape_url
 └─┬─┘ └─┬─┘ └─┬─┘   chunk + embed → upsert to pgvector
   └─────┼─────┘
         │
         ▼
  ┌────────────────┐
  │ pgvector store │  OpenAI text-embedding-3-small
  │  (per session) │  MMR retrieval (diversity-aware)
  └───────┬────────┘
          │ retrieve top-k chunks per subtask
   ┌──────┼──────┐
   ▼      ▼      ▼
 ┌───┐  ┌───┐  ┌───┐  Analyst Agents (GPT-4.1-mini)
 │ A1│  │ A2│  │ A3│  RAG synthesis per subtask
 └─┬─┘  └─┬─┘  └─┬─┘  400–600 word cited findings
   └───────┼───────┘
           │ all findings
           ▼
  ┌──────────────────┐
  │ Synthesizer Agent│  GPT-4.1 · token-by-token streaming
  │                  │  → structured markdown report
  └──────────────────┘
           │
           ▼ SSE stream (every agent step, every token)
  ┌──────────────────┐
  │  Next.js Frontend│  ProgressTracker · AgentTimeline · ReportViewer
  └──────────────────┘
```

Every agent step emits an SSE event — the frontend shows live progress, elapsed time per step, and streams the final report token by token.

---

## What This Proves

| Claim on Resume | Where it's demonstrated in Nexus |
|---|---|
| **RAG pipelines** | Researcher agents chunk + embed web content; Analyst agents retrieve via MMR from session-scoped pgvector collections |
| **Tool-calling workflows** | Researcher agents bind `search_web` + `scrape_url` tools via LangChain; the LLM autonomously decides when and what to call |
| **Agent orchestration** | Planner → parallel Researchers → parallel Analysts → Synthesizer pipeline coordinated via `asyncio.Queue` |
| **Vector database integration** | pgvector with OpenAI embeddings, per-session collection namespacing, MMR retrieval, automatic cleanup |
| **Production AI applications** | FastAPI, full async, Docker, deployed to Railway + Vercel, structured SSE streaming, error handling, environment config |

---

## Tech Stack

### Backend
- **FastAPI** — async REST + SSE streaming
- **LangChain** — agent orchestration, tool-calling, RAG chains
- **OpenAI GPT-4.1** — planner and synthesizer (quality)
- **OpenAI GPT-4.1-mini** — researcher and analyst (speed + cost)
- **OpenAI text-embedding-3-small** — document embeddings
- **pgvector** — vector similarity search on PostgreSQL
- **Tavily** — real-time web search API
- **asyncpg + SQLAlchemy** — async database layer
- **httpx + BeautifulSoup** — async web scraping

### Frontend
- **Next.js 14** (App Router) + **TypeScript**
- **Tailwind CSS v4** + **shadcn/ui**
- **ReactMarkdown** + **remark-gfm**
- **Fetch API + ReadableStream** — manual SSE parsing with timestamps

---

## Local Development

### Prerequisites
- Python 3.11
- Node.js 18+
- Docker Desktop
- OpenAI API key
- Tavily API key — [get one free](https://tavily.com)

### 1. Clone

```bash
git clone https://github.com/your-username/nexus.git
cd nexus
```

### 2. Start the database

```bash
docker-compose up -d postgres
```

This starts PostgreSQL 16 with the pgvector extension pre-installed.

### 3. Backend

```bash
cd backend
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt

cp .env.example .env
# Edit .env and add your OPENAI_API_KEY and TAVILY_API_KEY
```

Start the API server:
```bash
uvicorn main:app --reload --port 8000
```

Verify it's running:
```bash
curl http://127.0.0.1:8000/api/health
# {"status":"ok"}
```

### 4. Frontend

```bash
cd frontend
npm install
cp .env.local.example .env.local
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

> **Note:** Tavily requires a non-restricted IP. If you get 403 errors, try a VPN.

---

## Production Deployment

### Step 1 — Database: Supabase (free)

1. Create a project at [supabase.com](https://supabase.com)
2. Go to **SQL Editor** and run:
   ```sql
   CREATE EXTENSION IF NOT EXISTS vector;
   ```
3. Go to **Project Settings → Database** and copy the connection string.

Your URLs will look like:
```
DATABASE_URL=postgresql+psycopg://postgres:[PASSWORD]@db.[REF].supabase.co:5432/postgres
DATABASE_URL_ASYNC=postgresql+asyncpg://postgres:[PASSWORD]@db.[REF].supabase.co:5432/postgres?ssl=require
```

### Step 2 — Backend: Railway

1. Push your code to GitHub.
2. Go to [railway.app](https://railway.app) → **New Project → Deploy from GitHub repo**.
3. Select your repo. Set the **Root Directory** to `/backend`.
4. Railway auto-detects the `Dockerfile`.
5. Add environment variables in the Railway dashboard:

| Variable | Value |
|---|---|
| `OPENAI_API_KEY` | `sk-proj-...` |
| `TAVILY_API_KEY` | `tvly-dev-...` |
| `DATABASE_URL` | Your Supabase psycopg URL |
| `DATABASE_URL_ASYNC` | Your Supabase asyncpg URL (with `?ssl=require`) |
| `FRONTEND_URL` | Your Vercel URL (add after Step 3) |

6. Deploy. Copy the Railway public URL (e.g. `https://nexus-backend.up.railway.app`).

### Step 3 — Frontend: Vercel

```bash
cd frontend
npx vercel --prod
```

When prompted, add the environment variable:
```
NEXT_PUBLIC_API_URL=https://nexus-backend.up.railway.app
```

After deploy, copy the Vercel URL and update `FRONTEND_URL` in Railway to match.

---

## Project Structure

```
nexus/
├── backend/
│   ├── main.py                  # FastAPI app, SSE endpoint
│   ├── agents/
│   │   ├── planner.py           # GPT-4.1 research strategy planner
│   │   ├── researcher.py        # GPT-4.1-mini web search + scrape agent
│   │   ├── analyst.py           # GPT-4.1-mini RAG synthesis agent
│   │   └── synthesizer.py       # GPT-4.1 streaming report writer
│   ├── tools/
│   │   ├── search_tool.py       # Tavily web search (LangChain @tool)
│   │   ├── scrape_tool.py       # Async URL scraper (httpx + BS4)
│   │   └── retrieval_tool.py    # pgvector MMR retrieval (LangChain @tool)
│   ├── rag/
│   │   ├── vectorstore.py       # PGVector setup, async engine, MMR retriever
│   │   └── ingestion.py         # RecursiveCharacterTextSplitter + embed + upsert
│   ├── models/schemas.py        # Pydantic v2 request/response models
│   ├── utils/streaming.py       # SSE event formatter
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
├── frontend/
│   ├── app/
│   │   ├── page.tsx             # Main UI — idle / researching / done phases
│   │   └── layout.tsx           # Theme init (flash-free dark mode)
│   ├── components/
│   │   ├── ProgressTracker.tsx  # Live step tracker with elapsed timers
│   │   ├── AgentTimeline.tsx    # Real-time agent event feed
│   │   ├── ReportViewer.tsx     # Markdown report + source cards + export
│   │   ├── ResearchInput.tsx    # Query input with example chips
│   │   ├── ThemeToggle.tsx      # Light/dark mode toggle
│   │   └── ui/                  # shadcn/ui components
│   ├── lib/
│   │   └── stream.ts            # SSE client (fetch + ReadableStream)
│   └── .env.local.example
├── docker/
│   └── init.sql                 # CREATE EXTENSION IF NOT EXISTS vector
├── docker-compose.yml           # Local dev: postgres + backend
└── README.md
```

---

## Key Implementation Details

**Parallel research pipeline** — researchers and analysts run as concurrent `asyncio` tasks, drained via a shared `Queue`. This cuts research time to the duration of the slowest single subtask rather than the sum of all subtasks.

**Session-scoped vector store** — each research run creates its own pgvector collection (`nexus_{session_id}`), preventing context bleed between queries. The collection is deleted when the session ends.

**MMR retrieval** — `search_type="mmr"` with `fetch_k = k × 3` ensures retrieved chunks are diverse, not just the highest-scoring near-duplicates.

**SSE event timestamps** — every `AgentEvent` carries `receivedAt: Date.now()`. The ProgressTracker derives step state from the event log via `useMemo` (not separate state), guaranteeing the UI is always in sync with actual elapsed time.

**Flash-free theming** — an inline `<script>` in `layout.tsx` reads `localStorage` and sets the `dark` class before React hydrates, eliminating the light-flash-on-dark-mode problem.

---

## Resume Bullets

```
Nexus — Multi-Agent Research Assistant                    github.com/your-username/nexus
Python · LangChain · OpenAI · FastAPI · pgvector · Next.js · TypeScript · Docker

• Architected a multi-agent RAG system where a GPT-4.1 planner orchestrates parallel
  web-search and analysis agents, producing cited research reports streamed token-by-token
  via Server-Sent Events to a real-time Next.js dashboard.

• Implemented autonomous tool-calling workflows using LangChain bind_tools with custom
  Tavily search and async web-scraping tools; the researcher agent selects sources,
  scrapes content, and ingests 400–600 document chunks per research session.

• Built a session-scoped pgvector RAG pipeline with OpenAI embeddings, MMR retrieval,
  and automatic collection cleanup — ensuring each research query operates on a fresh,
  isolated vector namespace with no cross-session contamination.

• Deployed on Railway (Docker/FastAPI backend) + Vercel (Next.js frontend) + Supabase
  (managed pgvector), with full async FastAPI architecture, structured SSE event streaming,
  per-agent elapsed-time tracking, and light/dark mode UI.
```
