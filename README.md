# ATower Of Agents

ATower Of Agents is a control tower for enterprise AI-agent workflows. Operators will be able to upload company artifacts, assemble specialist agents in a Band room, retrieve evidence through Supabase RAG, and receive an auditable decision packet.

The repository currently provides the **base setup**: architecture and API contracts, agent instructions, Supabase migrations, mock-safe integration boundaries, a FastAPI shell, and a Next.js dashboard. Product workflow execution is the next development phase.

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

If Docker reports that it cannot connect to the daemon, start Docker Desktop or the Docker Engine service and rerun the command.

## Environment

External integrations are optional during base development. To configure them:

```bash
cp .env.example .env
```

Then add the required Supabase, AIML API, Featherless, or Band credentials and rebuild:

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
FEATHERLESS_API_KEY
FEATHERLESS_DEFAULT_MODEL
FEATHERLESS_BASE_URL
FEATHERLESS_TOOL_MODEL
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
```

Never commit `.env` or real credentials. `SUPABASE_SERVICE_ROLE_KEY` must never be exposed to browser code.

### Live Band coordinator

`BAND_MODE=mock` keeps everything in-process. To make the `@ATower Coordinator`
reply to room mentions, set `BAND_MODE=sdk` plus `BAND_AGENT_ID`, `BAND_API_KEY`,
`FEATHERLESS_API_KEY`, and a tool-capable `FEATHERLESS_TOOL_MODEL`, then add the
remote agent as a participant in the room. `docker compose up --build` starts the
`band-agent` service automatically; tail it with `docker compose logs -f band-agent`.
HR workflow execution is still unimplemented (`/workflows/{id}/run` returns 501) —
the coordinator says so rather than fabricating results. See `docs/BAND_INTEGRATION.md`.

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
      -> AIML API agents
      -> Featherless review agents
```

Band is the visible collaboration layer, Supabase is the system of record, and LangGraph controls workflow execution.

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
- Agent and workflow registries
- Mock Band and LLM adapter boundaries (in-process)
- Live Band coordinator agent (`band-agent`, `BAND_MODE=sdk`) that joins a room and replies to mentions via the Band SDK + Featherless
- Parser, chunker, embedding, and retrieval boundaries
- Supabase schema, pgvector search function, and seed catalog
- Dashboard, workflow, agent, knowledge, and report route shells

Not implemented yet:

- Workflow persistence and execution
- Artifact upload and indexing
- Live Supabase calls, and live AIML/Featherless calls from the API workflow path
- In-process Band posting from the API (`BandSDKClient`); the live path is the standalone `band-agent` coordinator
- HR (and other) workflow execution from the coordinator or the API
- Final decision packet generation

Unfinished product endpoints return `501 Not Implemented` rather than fabricated data.

## Planned MVP

The first complete workflow will be **HR Candidate Screening**:

1. Upload a resume, job description, and hiring policy.
2. Create a Band room with specialist agents.
3. Retrieve workflow-scoped evidence from Supabase.
4. Run fit, fairness, interview, policy, and final-decision reviews.
5. Produce an evidence-backed packet requiring appropriate human review.

Sales Lead Qualification and Engineering Change Review remain shallow breadth templates.
