# ATower Of Agents: Agent Instructions

## Mandatory Reading Order

Every human or coding agent working in this repository must read and follow:

1. `AGENT.md` for the project's minimal, efficient engineering behavior.
2. This `AGENTS.md` file for architecture, ownership, security, and delivery rules.
3. The relevant documents and module-local instructions for the assigned task.

`AGENT.md` applies to all agents and subagents. Where instructions overlap, follow the stricter requirement.

## Purpose

ATower Of Agents is a CRM/HRMS-style control tower for enterprise AI-agent workflows. The MVP proves one deep workflow, HR Candidate Screening, while exposing lighter Sales Lead Qualification, Engineering Change Review, and Vendor Onboarding Procurement Review templates.

This bootstrap intentionally provides contracts and replaceable integration boundaries. Do not present mocks or placeholders as production integrations.

## Architecture

```text
Next.js dashboard
  -> FastAPI API
    -> Supabase Auth/Postgres/Storage/pgvector
    -> LangGraph workflow runtime
    -> Band collaboration/audit rooms
      -> AIML API for routing and synthesis
      -> Featherless for verification and second opinions
```

Band messages are part of the workflow audit record. Agent findings must be persisted and, when a room exists, posted to Band.

## Ownership

| Area | Owner | Paths |
|---|---|---|
| Orchestration | Tech lead | `apps/api/agents`, `apps/api/workflows`, `apps/api/band`, `apps/api/llm`, orchestration docs |
| Frontend | Product engineer | `apps/web`, frontend contract and demo sections |
| Data/RAG | Backend/data engineer | `supabase`, `apps/api/db`, `apps/api/rag`, document route, data docs |

Do not edit another owner's area without coordination. Shared contracts require updates to backend schemas, frontend types, and `docs/API_CONTRACTS.md`.

## Commands

```bash
docker compose up --build

pnpm install
pnpm dev
pnpm lint
pnpm typecheck
pnpm build

python -m venv .venv
source .venv/bin/activate
pip install -r apps/api/requirements.txt
pnpm dev:api
pnpm test:api
```

Frontend runs at `http://localhost:3000`; API runs at `http://localhost:8000`.
Docker Compose is the default one-command setup for new contributors.

## Environment

- Copy `.env.example` to `.env`; never commit `.env` or credentials.
- Only variables prefixed with `NEXT_PUBLIC_` may be exposed to browser code.
- Server-side Supabase writes use the service role key. Never expose it to Next.js client components.
- `EMBEDDING_DIMENSIONS` must match the SQL vector dimension and embedding model.
- Missing external credentials must select explicit mock/unconfigured behavior, never fabricated success.

## Tests And Lint

- Add focused tests for non-trivial behavior.
- Backend: `pnpm test:api`
- Frontend type check: `pnpm typecheck`
- Full build: `pnpm build`
- Before merge, run the checks for every affected module.

## PR And Merge Rules

- Keep `main` runnable and commits small.
- PRs must state: What changed, How to test, Affected modules, Known limitations.
- Never commit secrets, generated dependency folders, or local environment files.
- API changes update Pydantic schemas, TypeScript types, and API contract docs.
- Database changes update migrations, schema docs, and seed data when relevant.

## Worktrees

- Use one branch and worktree per owner; see `docs/WORKTREE_GUIDE.md`.
- Do not share `node_modules`, virtual environments, or mutable build output between worktrees.
- Rebase or merge `main` before integration and resolve shared contract conflicts deliberately.

## Security

- Validate all API and upload inputs at trust boundaries.
- Enforce organization/workflow scoping in every data query.
- Treat resumes, policies, CRM notes, and code as confidential.
- Do not log document contents, credentials, access tokens, or full model prompts containing private data.
- Agent outputs are advisory. High-impact decisions require human review.
- Never invent evidence IDs or citations.

## Do Not Build Yet

- Full RBAC, billing, production queues, OAuth integrations, Slack/Teams, vendor crawling, complex analytics, perfect parsing, or a general approval engine.
- Do not implement product workflow logic during bootstrap unless explicitly requested.

# Lazy Senior Developer Mode

You are a lazy senior developer. Lazy means efficient, not careless. The best code is the code never written.

Before writing any code, stop at the first rung that holds:

Does this need to be built at all? (YAGNI)
Does the standard library already do this? Use it.
Does a native platform feature cover it? Use it.
Does an already-installed dependency solve it? Use it.
Can this be one line? Make it one line.
Only then: write the minimum code that works.
Rules:

No abstractions that weren't explicitly requested.
No new dependency if it can be avoided.
No boilerplate nobody asked for.
Deletion over addition. Boring over clever. Fewest files possible.
Question complex requests: "Do you actually need X, or does Y cover it?"
Pick the edge-case-correct option when two stdlib approaches are the same size, lazy means less code, not the flimsier algorithm.
Mark intentional simplifications with a ponytail: comment. If the shortcut has a known ceiling (global lock, O(n²) scan, naive heuristic), the comment names the ceiling and the upgrade path.
Not lazy about: input validation at trust boundaries, error handling that prevents data loss, security, accessibility, anything explicitly requested. Non-trivial logic leaves ONE runnable check behind, the smallest thing that fails if the logic breaks (an assert-based demo/self-check or one small test file; no frameworks, no fixtures). Trivial one-liners need no test.