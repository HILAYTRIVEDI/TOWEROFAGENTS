# ATower Of Agents Project Memory

Before any work, read `AGENT.md`, then `AGENTS.md`. Both apply to Claude and every delegated subagent. `AGENT.md` defines the shared engineering behavior; `AGENTS.md` defines project architecture and delivery rules.

## Fixed Architecture

The system is Next.js -> FastAPI -> Supabase/LangGraph/Band, with AIML API and Featherless behind one LLM provider interface. Band is the visible collaboration and audit layer, not an optional chat widget. Supabase is the system of record.

## Working Behavior

- Inspect existing files and ownership before editing.
- Prefer small, reviewable changes and commits.
- Never claim a mock is a real integration.
- Never put secrets in code, prompts, fixtures, screenshots, or commits.
- Keep external providers behind typed interfaces with explicit mock or unconfigured states.
- Update docs whenever contracts, architecture, commands, or limitations change.

## Delegation

- Delegate UI work to `frontend-ui-agent`.
- Delegate FastAPI, LangGraph, schemas, routing, and execution to `backend-agent-runtime`.
- Delegate schema, parsing, embeddings, retrieval, and storage to `supabase-rag-agent`.
- Delegate Band rooms, messaging, and audit sync to `band-integration-agent`.
- Use `qa-review-agent` after cross-module changes and before demo integration.

Subagents stay inside their ownership boundaries unless the task explicitly requires a shared contract change.

## Worktrees

Follow `docs/WORKTREE_GUIDE.md`. One branch owns one worktree and one module area. Do not run multiple agents against the same writable worktree. Integrate shared contract changes early and keep `main` runnable.
