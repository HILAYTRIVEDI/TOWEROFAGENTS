# Worktree Guide

## Create Worktrees

```bash
git checkout main
git pull
mkdir -p ../worktrees

git worktree add ../worktrees/agentops-lead -b feat/orchestration

git worktree add ../worktrees/agentops-web -b feat/frontend-dashboard

git worktree add ../worktrees/agentops-data -b feat/supabase-rag

git worktree list
```

## Ownership

| Branch | Owner | Allowed areas |
|---|---|---|
| `feat/orchestration` | Tech Lead | `apps/api/agents`, `apps/api/workflows`, `apps/api/band`, `apps/api/llm`, architecture docs |
| `feat/frontend-dashboard` | Frontend | `apps/web`, UI docs, API client |
| `feat/supabase-rag` | Data/RAG | `supabase/migrations`, `apps/api/rag`, `apps/api/db`, seed scripts |

Install dependencies independently in each worktree. Do not point multiple active agents at the same writable worktree.

## Sync

Commit or stash owned changes, then rebase or merge current `main`. Coordinate before resolving contract files edited by multiple owners.

## Cleanup

```bash
git worktree remove ../worktrees/agentops-web
git worktree prune
```

