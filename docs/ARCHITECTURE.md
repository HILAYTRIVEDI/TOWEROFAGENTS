# Architecture

## System Context

```text
Browser
  -> Next.js dashboard
  -> FastAPI REST API
      -> Supabase Postgres, Storage, Auth, pgvector
      -> LangGraph workflow state machine
      -> Band room adapter
      -> LLM router
          -> AIML API
          -> Featherless
```

## Responsibilities

- **Next.js** renders workflows, uploads, findings, agents, and reports. It does not receive service-role credentials.
- **FastAPI** validates requests, applies organization/workflow scope, and owns orchestration.
- **Supabase** persists identities, workflow state, artifacts, chunks, findings, messages, reports, approvals, and metrics.
- **LangGraph** controls deterministic node order and future parallel specialist execution.
- **Band** exposes agent collaboration to operators and provides an auditable conversation stream.
- **LLM Router** selects AIML API, Featherless, or explicit mock behavior by task and configuration.

## Runtime Sequence

```text
create workflow -> upload documents -> index chunks -> create/reuse Band room
-> retrieve context -> execute specialists -> policy gate -> final decision
-> persist report -> publish summary to Band
```

## Key Boundaries

- Route handlers call services; they do not contain provider-specific logic.
- All agents accept `AgentInput` and return `AgentFinding`.
- Band clients implement one interface; mock messages are clearly labeled.
- Retrieval is workflow and organization scoped.
- Embedding dimensions are configured once but must remain aligned with SQL.

## Bootstrap Limitation

Only health, metadata, schemas, adapters, and route-shaped placeholders exist in the base scaffold. LangGraph execution, persistence, uploads, indexing, and live Band/provider clients are next-phase work.

