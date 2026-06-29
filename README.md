<p align="center">
  <strong>🏗 Tower of Agents</strong>
</p>

<p align="center">
  The Unified Governance & Execution Layer for Enterprise AI Agents.
</p>

<p align="center">
  <a href="#quick-start">Quick Start</a> •
  <a href="#architecture">Architecture</a> •
  <a href="#repository-map">Repo Map</a> •
  <a href="#workflows">Workflows</a> •
  <a href="#environment">Environment</a> •
  <a href="#development">Development</a>
</p>

---

## What is Tower of Agents?

Tower of Agents (TOA) is an enterprise control plane for governing autonomous AI agent workforces. Instead of letting agents communicate freely in unconstrained chatrooms — creating compliance black boxes, infinite loops, and data leaks — TOA enforces **deterministic state-machine execution**, **cryptographically auditable decision packets**, and **human-in-the-loop gates** before any high-impact action.

### Core Principles

| Principle                    | Implementation                                                               |
| ---------------------------- | ---------------------------------------------------------------------------- |
| **Deterministic Boundaries** | LangGraph state machines dictate exactly when and who speaks next            |
| **Auditable Decisions**      | Cryptographically isolated audit logs capture raw machine debate             |
| **Pointer-Based RAG**        | Secure metadata pointers link to protected pgvector — no raw data in chat    |
| **Human-Owned Outcomes**     | HITL gates freeze high-impact actions until an operator reviews and approves |

## Quick Start

The only prerequisite is [Docker Desktop](https://www.docker.com/products/docker-desktop/) or Docker Engine with Compose:

```bash
# Clone the enterprise control plane sandbox
git clone <your-repo-url>/tower-of-agents
cd tower-of-agents

# Start the core orchestrator, dashboard, and database infrastructure
docker compose up --build
```

Once healthy, open:

| Service           | URL                            |
| ----------------- | ------------------------------ |
| Dashboard         | `http://localhost:3000`        |
| Landing Page      | `http://localhost:3000`        |
| API Docs (Swagger)| `http://localhost:8000/docs`   |
| API Health        | `http://localhost:8000/health` |

No credentials needed for the base setup. LLM, embedding, and Band integrations default to explicit mock mode.

```bash
# Stop all services
docker compose down

# Full teardown (volumes, images, orphans)
docker compose down --volumes --rmi local --remove-orphans
```

### Docker Lifecycle

```bash
docker compose up --build              # Start or rebuild
docker compose logs -f                 # Stream all logs
docker compose logs -f web             # Stream frontend logs only
docker compose logs -f api             # Stream API logs only
docker compose logs -f band-agent      # Stream Band agent logs
docker compose ps                      # Container status
docker compose stop                    # Stop without removing
docker compose up --build --force-recreate  # Clean recreation
```

Local Docker runs use `docker-compose.override.yml` automatically — it bind-mounts source directories and enables hot reload for both frontend and API.

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                     Next.js Dashboard                        │
│            Landing Page • Workflow UI • Reports              │
└────────────────────────────┬─────────────────────────────────┘
                             │ API (fetch)
┌────────────────────────────▼─────────────────────────────────┐
│                 FastAPI / LangGraph Conductor                 │
│     Routes • Workflow Executor • Agent Registry • RAG        │
└────┬───────────────────────┬──────────────────────────┬──────┘
     │ Secure RPC Proxy      │ Supabase Client           │ LLM Router
     ▼                       ▼                           ▼
┌────────────────┐  ┌─────────────────────┐  ┌──────────────────┐
│ Multi-Framework│  │  Supabase Vault     │  │   AIML API       │
│  Agent Mesh    │  │  PostgreSQL         │  │   (OpenAI-compat) │
│                │  │  pgvector           │  │   Mock fallback   │
│ LangChain      │  │  Storage buckets    │  │                  │
│ AutoGen        │  │  Auth & RLS         │  │                  │
│ CrewAI Nodes   │  │                     │  │                  │
│ Band SDK       │  │                     │  │                  │
└────────────────┘  └─────────────────────┘  └──────────────────┘
```

### Service Containers

| Container      | Image         | Port   | Purpose                                    |
| -------------- | ------------- | ------ | ------------------------------------------ |
| `web`          | `tower-web`   | `3000` | Next.js dashboard and landing page         |
| `api`          | `tower-api`   | `8000` | FastAPI control plane and workflow engine   |
| `band-agent`   | `tower-api`   | —      | Multi-role Band remote agent supervisor    |

## Repository Map

```
tower-of-agents/
│
├── apps/
│   ├── api/                    # FastAPI backend (see apps/api/README.md)
│   │   ├── agents/             #   Specialist agent definitions (HR, Sales, Eng)
│   │   ├── band/               #   Band.ai collaboration integration
│   │   ├── core/               #   Configuration and logging
│   │   ├── db/                 #   Supabase queries and document storage
│   │   ├── llm/                #   LLM provider abstraction (AIML/mock)
│   │   ├── models/             #   Pydantic schemas and data contracts
│   │   ├── rag/                #   RAG pipeline: parse → chunk → embed → retrieve
│   │   ├── routes/             #   HTTP API endpoints
│   │   ├── workflows/          #   Execution engine and templates
│   │   ├── tests/              #   pytest test suite
│   │   └── main.py             #   FastAPI application entry point
│   │
│   └── web/                    # Next.js frontend (see apps/web/README.md)
│       ├── app/                #   App Router pages and layouts
│       │   ├── page.tsx        #     Enterprise governance landing page
│       │   ├── globals.css     #     Complete design system
│       │   └── (app)/          #     Dashboard, workflows, agents, reports
│       ├── components/         #   Shared React components
│       └── lib/                #   API client utilities
│
├── supabase/                   # PostgreSQL/pgvector migrations and seeds
├── docs/                       # Architecture, contracts, and integration guides
│
├── docker-compose.yml          # Production service definitions
├── docker-compose.override.yml # Local dev overrides (hot reload)
├── .env.example                # Environment variable template
├── pnpm-workspace.yaml         # Monorepo workspace config
└── package.json                # Root scripts (dev, build, test, lint)
```

## Workflows

### HR Candidate Screening (Production)

The first fully operational workflow:

1. **Ingest** — Upload resume, job description, and hiring policy
2. **Parse & Embed** — Documents are parsed, chunked, and embedded into pgvector
3. **Retrieve** — Similarity search pulls relevant evidence chunks
4. **Execute** — 9 specialist agents run sequentially against evidence:
   - Resume/JD Matcher → Bias Reviewer → Interview Planner → Policy Guardian → Gap Analyst → RAG Retriever → Coordinator → Final Decision → Synthesizer
5. **Audit** — Each specialist posts audit messages to Band (SDK or mock mode)
6. **Decide** — Human-in-the-loop gate freezes the decision packet for operator review

**Decision Packet Output:**

```json
{
  "recommendation": "ADVANCE_TO_INTERVIEW",
  "confidence": 0.87,
  "strengths": ["5yr distributed systems experience"],
  "gaps": ["No healthcare domain exposure"],
  "interview_questions": ["Describe your approach to..."],
  "policy_note": "Passes DEI bias review — no disqualifying flags",
  "audit_hash": "sha256:9f86d0..."
}
```

### Vendor Onboarding Review (Production)

Runs a prospective vendor through procurement, legal, security, finance, compliance, and controller review. Use the `vendor-onboarding-review` template with vendor profile, contract, security documentation, and pricing artifacts.

The controller produces a reusable decision packet at `report_payload.decision_packet` for human approval. The packet includes the recommendation, executive summary, specialist findings, evidence chunk IDs, risks, missing information, disagreements, next actions, and audit trail. Recommendation parsing reads the controller finding's `RECOMMENDATION:` line and falls back to `needs_review` when the controller is absent, mock-backed, or does not emit a parseable value.

`DecisionPacket` and `build_decision_packet(...)` are workflow-agnostic primitives for future enterprise approval workflows; they are keyed on ordered findings and controller-style final decisions, not vendor-specific code.

### Sales Lead Qualification (Template)

Scores account fit, buying signals, objections, and suggested next steps for sales operators.

### Engineering Change Reviews (Template)

Cross-checks codebase pull requests against security protocols, internal dependency trees, and structural guidelines.

## Environment

```bash
cp .env.example .env
# Fill in required values, then:
docker compose up --build
```

### Key Variables

| Variable                    | Description                                     | Default      |
| --------------------------- | ----------------------------------------------- | ------------ |
| `SUPABASE_URL`              | Supabase project URL                            | —            |
| `SUPABASE_ANON_KEY`         | Supabase anonymous key                          | —            |
| `SUPABASE_SERVICE_ROLE_KEY` | Service role key (server-side only, **secret**)  | —            |
| `LLM_PROVIDER`              | `mock`, `aiml`, or `auto`                       | `aiml`       |
| `EMBEDDING_PROVIDER`        | `mock` or `aiml`                                | `mock`       |
| `EMBEDDING_DIMENSIONS`      | Vector dimensions (must match SQL schema)       | `1536`       |
| `BAND_MODE`                 | `mock` (in-process) or `sdk` (live agents)      | `mock`       |
| `BAND_AGENT_ID`             | Primary coordinator agent UUID                  | —            |
| `BAND_API_KEY`              | Band API key for coordinator                    | —            |
| `AIML_API_KEY`              | AIML API key for LLM/embedding                  | —            |
| `NEXT_PUBLIC_API_BASE_URL`  | Frontend → API URL (build-time)                 | `http://localhost:8000` |
| `NEXT_PUBLIC_DEFAULT_ORG_ID`| Temporary org scope (pre-auth)                  | —            |

> **Security:** Never commit `.env`. `SUPABASE_SERVICE_ROLE_KEY` must never be exposed to browser code.

### Live Band Agents

Set `BAND_MODE=sdk` to connect live agents. Each specialist role requires its own Band Remote Agent UUID and API key:

```
Workflow Router    •  RAG Retriever       •  Policy Guardian
Final Decision     •  Resume/JD Matcher   •  Bias/Safety Reviewer
Interview Planner  •  Lead Qualifier      •  Engineering Reviewer
```

Create each as a **Remote Agent** in Band, add credentials to `.env`, and add agents as participants in the target room. Roles without credentials are silently skipped. See `docs/BAND_INTEGRATION.md` for details.

## Development

### Prerequisites (local, non-Docker)

- Node.js 20 or 22
- pnpm 9
- Python 3.11+

### Install

```bash
# Frontend
pnpm install

# Backend
python -m venv .venv
source .venv/bin/activate
pip install -r apps/api/requirements.txt
```

### Run

```bash
# API (terminal 1)
pnpm dev:api

# Frontend (terminal 2)
pnpm dev
```

### Verify

```bash
pnpm test:api          # Backend pytest suite
pnpm typecheck         # TypeScript type checking
pnpm lint              # ESLint
pnpm build             # Production build
docker compose config --quiet  # Validate compose file
```

## Current Status

### ✅ Implemented

- Dockerized Next.js + FastAPI + Band agent services
- Enterprise governance landing page (dark mode, animated, interactive)
- Full dashboard with workflow CRUD, document upload, and execution
- HR Candidate Screening end-to-end: ingest → retrieve → execute → audit → decide
- RAG pipeline: parse (PDF/DOCX/TXT) → chunk → embed → pgvector retrieval
- Mock + AIML LLM routing with explicit fallbacks
- Mock + SDK Band integration with per-specialist audit messages
- Agent registry with 9 HR, Sales, Engineering, and Platform roles
- Organization-shared Knowledge Base with cross-workflow retrieval
- Decision packet reports with human-review required banners
- Focused backend tests for all core modules

### 🚧 Planned

- LangGraph runtime orchestration (replacing sequential executor)
- Production auth-derived organization scoping (replacing env-based org ID)
- Automatic Band room creation and participant management
- Real embedding provider configuration in all environments
- Sales Lead Qualification and Engineering Change Review execution
- Formal human approval action flow (currently advisory-only)

## License

MIT — see [LICENSE](LICENSE) for details.
