# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

智学助手 (ZhiXue Assistant) — a multi-agent AI tutoring system for personalized higher education learning. Built for the "软件杯" competition. The system uses 13 specialized AI agents orchestrated through a central dispatcher to handle chat, resource generation, learning path planning, evaluation, and student profiling.

## Commands

### Backend
```bash
cd backend
pip install -r requirements.txt          # Install dependencies
python main.py                           # Start server (http://localhost:8001, hot-reload)
python -m pytest tests/ -v               # Run all tests
python -m pytest tests/test_workflow.py   # Run single test file
```

### Frontend
```bash
python -m http.server 8080               # Serve static files from project root
```

No build step — vanilla JS/CSS loaded directly via `<script>` and `<link>` tags in `index.html`.

### Environment
Copy `backend/.env.example` to `backend/.env` and set `LLM_API_KEY`, `LLM_MODEL`, `LLM_HOST`. All config is in `backend/config.py` (`Settings` class, loaded via `python-dotenv`).

## Architecture

### Backend (FastAPI + Python)

**Core framework** (`backend/core/`):
- `BaseAgent` — abstract base class. Subclass it and implement `process()`. Use `@register_agent("capability")` decorator for auto-registration.
- `AgentRegistry` — singleton mapping capability strings to agent classes.
- `Orchestrator` — central dispatcher. Routes requests by `capability` field. Supports streaming (`dispatch`) and sync (`dispatch_sync`).
- `StreamBus` — async event bus (`asyncio.Queue`). 14 event types serialize to SSE for frontend. Events: SESSION, CONTENT, THINKING, STAGE_START/END, TOOL_CALL/RESULT, SOURCES, PROGRESS, RESULT, ERROR, DONE, AGENT_START/END.
- `UnifiedContext` — dataclass carrying request context (user, history, profile, mastery, config, shared state).
- `WorkflowEngine` — state-machine with nodes, edges, conditional routing. Max 50 steps safety limit.

**Agents** (`backend/agents/`): 13 agents registered by capability — `chat`, `generate`, `resource_orchestrator`, `profile`, `profile_build`, `diagnostic`, `resource_plan`, `path_plan`, `evaluate`, `safety`, plus resource sub-agents (`gen_lecture`, `gen_quiz`, `gen_mindmap`, `gen_code_lab`, `gen_reading`, `gen_animation`, `gen_ppt`).

**Services** (`backend/services/`): Business logic layer — LLM client (OpenAI SDK), RAG (BM25 + ChromaDB vector search + RRF fusion), SQLite database (raw `sqlite3`, WAL mode, no ORM), mastery tracking (Ebbinghaus forgetting curve), spaced repetition (SM-2), knowledge graph (NetworkX DAG), session management, question generation, confidence scoring.

**API** (`backend/api/`): 7 routers — `chat` (SSE streaming + sync), `profile`, `resources` (streaming generation), `evaluation`, `path`, `learning_path`, `knowledge`. Plus `schemas.py` for shared Pydantic models.

**Prompts** (`backend/prompts/`): LLM prompt templates organized by agent module, in Chinese. Loaded by `PromptManager` service.

### Frontend (Vanilla JS SPA)

Hash-based routing in `js/app.js` — `App` object with `register()` / `route()`. Six modules in `js/modules/`: dashboard, profile, resources, path, evaluation, tutor. Each module exports `render()` (returns HTML string) and `bind(container)` (attaches event listeners). Modules are lazily rendered and cached.

API layer in `js/api.js` — `Api` object with `fetch`-based methods. SSE streaming via `ReadableStream` reader for chat and resource generation. Request cancellation via `AbortController` map. 30s timeout for REST, 120s for streaming.

Global state in `AppState` (API base URL, user ID, course ID) persisted to `localStorage`.

Design system: OKLCH color space CSS custom properties ("Ink and Amber" theme). Documented in `DESIGN.md`.

### Frontend-Backend Communication

- **SSE Streaming** for long operations: `POST /api/chat`, `POST /api/resources/generate`, `POST /api/profile/build`. Events are `data: {json}\n\n` lines.
- **JSON REST** for everything else.
- CORS whitelist: localhost:3000, 5173, 8080 (configurable via `FRONTEND_ORIGIN` env var).

## Key Patterns

- **Agent registration**: Decorate agent class with `@register_agent("capability_name")`. The orchestrator auto-discovers agents via lazy `importlib.import_module()`.
- **LLM calls**: Use `self.call_llm()`, `self.call_llm_json()`, or `self.stream_llm()` from `BaseAgent`. Prompts loaded via `self.load_prompt("prompt_name", {variables})`.
- **Database**: Raw `sqlite3` with WAL mode. Service at `services/database.py`. No ORM — write SQL directly.
- **RAG pipeline**: `services/rag_service.py` — BM25 keyword search + ChromaDB vector search + Reciprocal Rank Fusion. 5-min TTL cache. Knowledge base versioning with rollback.
- **Frontend modules**: Register via `App.register("name", module)`. Module must have `title`, `render()`, and `bind(container)`.

## Concurrency

Backend is async (FastAPI + asyncio). Agents use `async def process()`. SSE events flow through `StreamBus` async queues. Frontend uses `AbortController` to cancel in-flight requests on module switch.
