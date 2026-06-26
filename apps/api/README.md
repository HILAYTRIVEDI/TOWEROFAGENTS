# Tower of Agents — API

The FastAPI backend that powers the Tower of Agents control plane. It orchestrates multi-framework agent meshes, manages the RAG ingestion pipeline, routes LLM calls, and exposes a deterministic workflow execution engine — all behind auditable, human-in-the-loop guardrails.

## Quick Start

### Via Docker (recommended)

From the repository root:

```bash
docker compose up --build
```

The API will be available at:

| Endpoint          | URL                          |
| ----------------- | ---------------------------- |
| Root              | `http://localhost:8000/`     |
| OpenAPI docs      | `http://localhost:8000/docs` |
| Health check      | `http://localhost:8000/health` |

### Standalone (local development)

```bash
cd apps/api
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                    FastAPI (main.py)                 │
│  ┌───────────┐ ┌───────────┐ ┌───────────────────┐  │
│  │  Routes   │ │ Middleware│ │   CORS / Auth     │  │
│  └─────┬─────┘ └───────────┘ └───────────────────┘  │
│        │                                             │
│  ┌─────▼──────────────────────────────────────────┐  │
│  │              Core Business Logic               │  │
│  │  ┌──────────┐ ┌──────────┐ ┌────────────────┐  │  │
│  │  │ Workflows│ │  Agents  │ │   RAG Pipeline │  │  │
│  │  │ executor │ │ registry │ │ parse→chunk→   │  │  │
│  │  │ graph    │ │ hr/sales │ │ embed→retrieve │  │  │
│  │  │ templates│ │ eng/plat │ │                │  │  │
│  │  └────┬─────┘ └────┬─────┘ └───────┬────────┘  │  │
│  └───────┼─────────────┼──────────────┼───────────┘  │
│          │             │              │               │
│  ┌───────▼─────────────▼──────────────▼───────────┐  │
│  │           Integration Boundaries               │  │
│  │  ┌────────┐  ┌──────────┐  ┌────────────────┐  │  │
│  │  │  LLM   │  │   Band   │  │   Supabase     │  │  │
│  │  │ router │  │  client  │  │   DB + Storage  │  │  │
│  │  │ (aiml/ │  │  (sdk/   │  │   + pgvector   │  │  │
│  │  │  mock) │  │   mock)  │  │                │  │  │
│  │  └────────┘  └──────────┘  └────────────────┘  │  │
│  └────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────┘
```

## Module Map

```
apps/api/
├── main.py                 # FastAPI app, middleware, router registration
├── requirements.txt        # Python dependencies
├── Dockerfile              # Python 3.12-slim production image
├── pyproject.toml          # Project metadata
│
├── core/                   # Shared configuration and logging
│   └── config.py           # Pydantic settings from env vars
│
├── routes/                 # HTTP API layer
│   ├── health.py           # GET /health
│   ├── workflows.py        # CRUD + execution: /workflows/*
│   ├── documents.py        # Upload, ingest, delete: /documents/*
│   ├── agents.py           # Agent registry: /agents
│   └── reports.py          # Decision packets: /reports/*
│
├── agents/                 # Specialist agent definitions
│   ├── registry.py         # Central agent catalog
│   ├── base_agent.py       # Abstract agent interface
│   ├── hr/                 # HR Candidate Screening agents
│   ├── sales/              # Sales Lead Qualification agents
│   ├── engineering/        # Engineering Change Review agents
│   └── platform/           # Platform utility agents (RAG, router)
│
├── workflows/              # Workflow execution engine
│   ├── executor.py         # Sequential specialist executor
│   ├── graph.py            # LangGraph state machine (planned)
│   └── templates.py        # Workflow template definitions
│
├── rag/                    # Retrieval-Augmented Generation pipeline
│   ├── parser.py           # PDF/DOCX → plain text extraction
│   ├── chunker.py          # Text → overlapping chunks
│   ├── embeddings.py       # Embed chunks (AIML or mock vectors)
│   ├── ingestion.py        # Orchestrates parse → chunk → embed → store
│   └── retriever.py        # pgvector similarity search
│
├── llm/                    # LLM provider abstraction
│   ├── base.py             # Abstract LLM interface
│   ├── router.py           # Provider routing (aiml/mock/auto)
│   └── aiml_client.py      # AIML API client (OpenAI-compatible)
│
├── band/                   # Band.ai collaboration integration
│   ├── client.py           # Band API client (SDK + mock modes)
│   ├── coordinator.py      # Live Band coordinator agent
│   ├── remote_agents.py    # Multi-role agent supervisor
│   ├── run_audit.py        # Per-specialist audit message posting
│   ├── room_orchestrator.py# Room lifecycle management
│   └── message_sync.py     # Message synchronization
│
├── db/                     # Database access layer
│   ├── supabase_client.py  # Supabase client singleton
│   ├── queries.py          # Typed query functions
│   └── documents.py        # Document + storage operations
│
├── models/                 # Pydantic schemas / data contracts
├── scripts/                # Utility scripts
└── tests/                  # pytest suite
```

## API Routes

### Health

| Method | Path      | Description              |
| ------ | --------- | ------------------------ |
| GET    | `/health` | Service health + version |

### Workflows

| Method | Path                         | Description                                |
| ------ | ---------------------------- | ------------------------------------------ |
| GET    | `/workflows`                 | List workflows for an organization         |
| POST   | `/workflows`                 | Create a new workflow                      |
| GET    | `/workflows/{id}`            | Get workflow details                       |
| PUT    | `/workflows/{id}`            | Update workflow metadata                   |
| DELETE | `/workflows/{id}`            | Delete a workflow and its artifacts         |
| POST   | `/workflows/{id}/run`        | Execute workflow → produce decision packet |
| POST   | `/workflows/{id}/reindex`    | Re-embed all workflow documents            |
| PATCH  | `/workflows/{id}/room`       | Assign a Band room to a workflow           |

### Documents

| Method | Path                         | Description                                |
| ------ | ---------------------------- | ------------------------------------------ |
| POST   | `/documents/upload`          | Upload + ingest a document (PDF/DOCX/TXT)  |
| DELETE | `/documents/{id}`            | Remove document, chunks, and storage file  |

### Agents

| Method | Path      | Description              |
| ------ | --------- | ------------------------ |
| GET    | `/agents` | List all registered agent roles |

### Reports

| Method | Path              | Description                       |
| ------ | ----------------- | --------------------------------- |
| GET    | `/reports/{id}`   | Retrieve a decision packet report |

## RAG Pipeline

The ingestion pipeline follows a deterministic, four-stage flow:

```
Document Upload → Parse → Chunk → Embed → Store (pgvector)
```

1. **Parse** (`rag/parser.py`): Extracts plain text from PDF (pypdf), DOCX (python-docx), or raw text files.
2. **Chunk** (`rag/chunker.py`): Splits text into overlapping chunks with configurable size and overlap.
3. **Embed** (`rag/embeddings.py`): Generates vector embeddings via AIML API or deterministic mock vectors.
4. **Store**: Persists chunks + embeddings into Supabase `document_chunks` table with pgvector indexing.

Retrieval uses cosine similarity search against the pgvector index, scoped to the requesting workflow and shared organization knowledge.

## Agent System

Agents are organized into domain-specific hierarchies:

| Domain        | Roles                                                           |
| ------------- | --------------------------------------------------------------- |
| **HR**        | Resume/JD Matcher, Bias Reviewer, Interview Planner, Policy Guardian, Final Decision |
| **Sales**     | Lead Qualifier                                                  |
| **Engineering** | Engineering Reviewer                                          |
| **Platform**  | Workflow Router, RAG Retriever, Coordinator                     |

Each agent implements `BaseAgent` and is registered in `agents/registry.py`. The workflow executor invokes agents sequentially; LangGraph orchestration is planned.

## Band Integration

Band provides the auditable collaboration layer. Two modes are supported:

| Mode   | Behavior                                                        |
| ------ | --------------------------------------------------------------- |
| `mock` | In-process mock client; audit messages persisted without network calls |
| `sdk`  | Live Band SDK; agents connect as remote participants in rooms   |

The `band-agent` Docker service supervises all 9+ specialist remote agents. Each role operates under its own credential and never impersonates another agent. See `docs/BAND_INTEGRATION.md` for full configuration.

## Environment Variables

See `.env.example` at the repository root for the full list. Key variables:

| Variable                  | Description                              | Default      |
| ------------------------- | ---------------------------------------- | ------------ |
| `SUPABASE_URL`            | Supabase project URL                     | —            |
| `SUPABASE_SERVICE_ROLE_KEY` | Service role key (server-side only)    | —            |
| `LLM_PROVIDER`            | LLM routing: `mock`, `aiml`, or `auto`  | `aiml`       |
| `EMBEDDING_PROVIDER`      | Embedding provider: `mock` or `aiml`     | `mock`       |
| `EMBEDDING_DIMENSIONS`    | Vector dimensions (must match SQL)       | `1536`       |
| `BAND_MODE`               | Band integration: `mock` or `sdk`        | `mock`       |
| `BAND_AGENT_ID`           | Primary coordinator agent UUID           | —            |
| `AIML_API_KEY`            | AIML API key for LLM/embedding calls     | —            |

## Testing

```bash
# From apps/api with virtualenv activated
pytest

# Or from the repository root
pnpm test:api
```

Tests cover agent logic, workflow execution, document handling, retrieval, schema validation, LLM routing, and Band audit behavior.

## Docker

The API runs on `python:3.12-slim` and exposes port `8000`. The production command is:

```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

The `docker-compose.override.yml` adds `--reload` and bind-mounts for local development. Rebuild only when dependencies or Dockerfiles change.
