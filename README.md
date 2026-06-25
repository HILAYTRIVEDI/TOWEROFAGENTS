# ATower Of Agents

ATower Of Agents is a control tower for enterprise AI-agent workflows. Operators will be able to upload company artifacts, assemble specialist agents in a Band room, retrieve evidence through Supabase RAG, and receive an auditable decision packet.

The repository provides the architecture and API contracts, agent instructions, Supabase migrations, mock-safe integration boundaries, a FastAPI backend, and a Next.js dashboard. The **HR Candidate Screening** workflow now runs end to end: documents are ingested into pgvector, specialist agents execute against retrieved evidence, Band audit messages are posted or explicitly mocked, and an auditable decision packet is persisted and rendered. The main remaining gaps are real Band room provisioning, LangGraph orchestration, production auth/RLS, and fully configured real embeddings.

## Quick Start

The recommended setup requires only Docker Desktop or Docker Engine with Compose:

```bash
docker compose up --build
```

Open:

- Dashboard: `http://localhost:3000/dashboard`
- API documentation: `http://localhost:8000/docs`
- API health: `http://localhost:8000/health`

No credentials are needed for the base setup. LLM, embedding, and Band integrations default to explicit mock mode.

Stop the services with:

```bash
docker compose down
```

### Docker Lifecycle Commands

```bash
# Start or rebuild the application
docker compose up --build

# Watch service logs
docker compose logs -f

# Show container status
docker compose ps

# Stop containers without removing them
docker compose stop

# Stop and remove containers and the Compose network
docker compose down

# Fully destroy containers, volumes, local images, and orphaned services
docker compose down --volumes --rmi local --remove-orphans

# Force a clean service recreation
docker compose up --build --force-recreate
```

Local Docker runs use `docker-compose.override.yml` automatically. It bind-mounts
`apps/web` and `apps/api`, runs Next.js in dev mode, and starts FastAPI with
`--reload`, so frontend and API source changes should appear without rebuilding.
Rebuild only when dependencies, Dockerfiles, or build-time environment values
change.

If Docker reports that it cannot connect to the daemon, start Docker Desktop or the Docker Engine service and rerun the command.

## Environment

External integrations are optional during base development. To configure them:

```bash
cp .env.example .env
```

Then add the required Supabase, AIML API, or Band credentials and rebuild:

```bash
docker compose up --build
```

Important variables include:

```text
SUPABASE_URL
SUPABASE_ANON_KEY
SUPABASE_SERVICE_ROLE_KEY
AIML_API_KEY
AIML_DEFAULT_MODEL
LLM_PROVIDER
EMBEDDING_PROVIDER
EMBEDDING_MODEL
EMBEDDING_DIMENSIONS
BAND_MODE
BAND_API_KEY
BAND_AGENT_ID
BAND_DEFAULT_ROOM_ID
THENVOI_WS_URL
THENVOI_REST_URL
NEXT_PUBLIC_API_BASE_URL
NEXT_PUBLIC_DEFAULT_ORG_ID
```

Never commit `.env` or real credentials. `SUPABASE_SERVICE_ROLE_KEY` must never be exposed to browser code.
`NEXT_PUBLIC_DEFAULT_ORG_ID` selects the temporary organization scope used by
the dashboard until Supabase authentication supplies it from the signed-in user.

### Live Band agents

`BAND_MODE=mock` keeps everything in-process and records explicit mock audit
messages. To make the `@ATower Coordinator` reply to room mentions, set
`BAND_MODE=sdk` plus `BAND_AGENT_ID`, `BAND_API_KEY`, and `LLM_PROVIDER=aiml`
with `AIML_API_KEY`/`AIML_DEFAULT_MODEL`, then add the remote agent as a
participant in the room.
`docker compose up --build` starts the
`band-agent` service automatically; tail it with `docker compose logs -f band-agent`.
HR workflow execution runs through `/workflows/{id}/run`; the coordinator must
not claim a run happened unless that API path completed. See `docs/BAND_INTEGRATION.md`.

Workflow runs also use `band/run_audit.py` to post one message per executed
specialist when a workflow room or `BAND_DEFAULT_ROOM_ID` is present. In
`BAND_MODE=sdk`, each specialist posts with its own remote-agent credential. In
mock mode, the audit messages are persisted with `mode=mock` and no network call.

The same `band-agent` service supervises all registered specialist roles:

```text
Workflow Router        RAG Retriever          Policy Guardian
Final Decision         Resume/JD Matcher      Bias/Safety Reviewer
Interview Planner      Lead Qualifier         Engineering Reviewer
```

Create each one as a separate **Remote Agent** in Band, then put its UUID and API
key in the matching `BAND_<ROLE>_AGENT_ID` and `BAND_<ROLE>_API_KEY` variables
listed in `.env.example`. Add each agent to the room where it should operate.
Roles without credentials are skipped; one agent never impersonates another.
Band sends a message to a remote agent only when that participant is explicitly
mentioned.

## Local Development

Docker is the default onboarding path. For direct local development, install:

- Node.js 20 or 22
- pnpm 9
- Python 3.11+

Install dependencies:

```bash
pnpm install

python -m venv .venv
source .venv/bin/activate
pip install -r apps/api/requirements.txt
```

Run the API and frontend in separate terminals:

```bash
pnpm dev:api
pnpm dev
```

## Checks

```bash
pnpm test:api
pnpm typecheck
pnpm lint
pnpm build
docker compose config --quiet
```

## Architecture

```text
Next.js dashboard
  -> FastAPI backend
    -> Supabase Auth, Postgres, Storage, and pgvector
    -> LangGraph workflow runtime
    -> Band collaboration and audit rooms
      -> AIML API agents, with explicit mock fallback
```

Band is the visible collaboration layer, Supabase is the system of record, and LangGraph is the planned workflow runtime. The current HR run path uses a sequential specialist executor.

## Repository Map

```text
apps/web          Next.js dashboard and frontend contracts
apps/api          FastAPI, agents, workflows, RAG, Band, and LLM boundaries
supabase          PostgreSQL/pgvector migrations and seed records
docs              Architecture, contracts, ownership, and demo planning
.claude/agents    Project-specific Claude subagent manifests
docker-compose.yml One-command local service orchestration
```

## Agent Instructions

Every human or coding agent working in this repository must read, in order:

1. `AGENT.md`
2. `AGENTS.md`
3. The relevant documents and module-specific instructions

`AGENT.md` applies to all agents and subagents. `AGENTS.md` defines architecture, ownership, security, testing, and delivery rules.

## Current Scope

Available now:

- Dockerized Next.js and FastAPI services
- API health endpoint and OpenAPI documentation
- Typed backend and frontend contracts
- Agent and workflow registries, including HR, Sales, Engineering, and platform agents
- Mock Band, mock LLM, AIML LLM, and embedding adapter boundaries
- Live Band SDK supervisor for the coordinator and nine specialist roles
- Parser, chunker, embedding, and retrieval boundaries
- Supabase schema, pgvector search function, and seed catalog
- Dashboard, workflow, agent, knowledge-base, docs, and report routes
- Document upload from the workflow detail page to a private Supabase Storage
  bucket, followed by ingestion into pgvector (status advances
  `uploaded` → `parsing` → `indexed`, or `failed` on error)
- Organization-shared Knowledge uploads and deletes; shared chunks are stored
  with `workflow_id = null` and are retrieved alongside workflow-specific chunks
- Document ingestion pipeline: parse → chunk → embed → persist scoped chunks
  (`rag/ingestion.py`), with shared knowledge-base chunks stored NULL-scoped
- Workflow CRUD, workflow-specific document upload, workflow re-indexing, and
  workflow Band room assignment
- HR workflow execution and persistence: `POST /workflows/{id}/run` runs the
  specialist agents against retrieved evidence and saves an evidence-backed
  decision packet (recommendation, strengths, gaps, interview questions, and a
  plain-text policy note) to Supabase
- Workflow run Band audit: when a room/default room is configured, specialist
  findings are posted to Band in SDK mode or persisted as explicit mock messages
  in mock mode; the report payload records message counts and modes
- Report retrieval by workflow or report ID, with the report UI showing the
  decision packet, human-review banner, evidence IDs, and Band audit summary
- Focused backend tests for agents, workflow execution, document handling,
  retrieval, schemas, LLM routing, and Band audit behavior

Not implemented yet:

- Automatic real Band room creation and participant management from the API
- HR workflow execution from the coordinator itself; workflow runs happen through the API
- LangGraph runtime execution; `workflows/graph.py` still documents planned node order and raises `NotImplementedError`
- Production auth-derived organization scoping and hardened RLS; the dashboard still uses `NEXT_PUBLIC_DEFAULT_ORG_ID`
- Fully configured real embeddings in all environments; mock embeddings are deterministic but not meaningful
- Featherless routing; the current deployment disables Featherless and expects AIML for real LLM calls
- Sales Lead Qualification and Engineering Change Review execution beyond shallow templates
- Formal approval/decision action flow; all AI decisions still require human review

Unfinished product paths must fail honestly rather than fabricate data.

## MVP Workflow

The first complete workflow is **HR Candidate Screening**:

1. Upload a resume, job description, and hiring policy.
2. Attach an existing Band room, create a mock room, or rely on `BAND_DEFAULT_ROOM_ID`.
3. Retrieve workflow-scoped and organization-shared evidence from Supabase.
4. Run fit, fairness, interview, policy, and final-decision reviews.
5. Persist specialist Band audit messages when a room is configured.
6. Produce an evidence-backed packet requiring human review.

Sales Lead Qualification and Engineering Change Review remain shallow breadth templates.

## Remaining Work

Highest-priority gaps:

- Apply any pending Supabase migrations, especially organization document support, to live environments.
- Configure a real embedding provider and keep `EMBEDDING_DIMENSIONS` aligned with the SQL vector dimension.
- Replace the sequential workflow executor with real LangGraph orchestration.
- Add API-driven real Band room creation and participant management.
- Move organization scope from temporary environment configuration to Supabase Auth/RLS.
- Add the formal human approval step before any high-impact HR decision can be acted on.
- Polish the Knowledge UI with search/filter/sort metadata if the demo needs larger document sets.

Out of scope for this bootstrap remains full RBAC, billing, production queues,
OAuth integrations, Slack/Teams, vendor crawling, complex analytics, perfect
parsing, and a general approval engine.
