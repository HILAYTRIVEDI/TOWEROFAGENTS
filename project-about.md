# ATower Of Agents (TOA): Project Overview

## What It Is

**Tower of Agents (TOA)** is a CRM/HRMS-style control tower that serves as the unified governance and execution layer for enterprise AI-agent workflows. 

Instead of letting autonomous agents communicate freely in unconstrained chatrooms — which creates compliance black boxes, infinite loops, and data leaks — TOA provides an enterprise control plane. It enforces deterministic state-machine execution, cryptographically auditable decision packets, and human-in-the-loop (HITL) gates before any high-impact action can occur.

The end goal of TOA is to be the **Governance and Execution Layer of the Enterprise**, ensuring that AI agents can be deployed effectively, securely, and transparently across critical business functions.

## Core Principles

To achieve this goal, TOA relies on four core principles:

1. **Deterministic Boundaries:** LangGraph state machines dictate exactly when and who speaks next, preventing unbounded agent loops.
2. **Auditable Decisions:** Cryptographically isolated audit logs capture raw machine debate in Band rooms.
3. **Pointer-Based RAG:** Secure metadata pointers link to protected vector databases (pgvector) so raw sensitive data is not needlessly exposed in chat contexts.
4. **Human-Owned Outcomes:** High-impact actions are frozen by HITL gates until a human operator reviews the advisory findings and approves the final decision.

## How It Works

TOA is built on a modern, decoupled architecture:

```text
Next.js dashboard (Landing Page, Workflow UI, Reports)
  -> FastAPI API (Routes, Executor, Agent Registry, RAG)
    -> Supabase (Auth, Postgres, Storage, pgvector)
    -> LangGraph workflow runtime (Orchestration & State)
    -> Band collaboration/audit rooms (Agent-to-agent coordination)
      -> AIML API (OpenAI-compatible models for generation)
      -> Featherless (Verification and open-weight models)
```

### The Execution Flow

1. **Ingestion & Retrieval:** Users upload required evidence (e.g., resumes, job descriptions). Documents are parsed, chunked, and embedded into pgvector. Similarity searches pull relevant evidence chunks for the agents.
2. **Execution via LangGraph:** A deterministic graph runs specialized agents sequentially against the evidence. For example, the HR workflow uses a Coordinator, RAG Retriever, Resume/JD Matcher, Bias Reviewer, Interview Planner, Policy Guardian, and Final Decision maker.
3. **Band Integration for Audit:** The execution process posts conversational audits into Band rooms. Each specialist agent posts its findings and @mentions the next agent. Operators can view the machine debate in a dedicated session for each workflow.
4. **Human Review (HITL):** Agent outputs are strictly advisory. After execution, the workflow enters an "awaiting_review" state. A human operator reviews the decision packet (recommendations, strengths, gaps, policy notes) and either approves or rejects the action.

## Workflows

TOA is designed to handle multiple enterprise scenarios. The primary implementations include:

- **HR Candidate Screening (Flagship MVP):** Collects a candidate's resume, job description, and corporate hiring policy. Specialists evaluate the match, audit for bias, generate interview questions, and summarize findings for HR review.
- **Sales Lead Qualification (Template):** Uses supplied ICP (Ideal Customer Profile), CRM notes, and sales context to evaluate lead fit and recommend next steps without inventing prospect facts.
- **Engineering Change Review (Template):** Analyzes design notes, code changes, and test evidence to flag implementation risks, identify missing test coverage, and highlight integration concerns.

## Summary

By combining a robust API, state-machine execution via LangGraph, secure data storage with Supabase, and transparent collaboration via Band, **Tower of Agents** successfully packages AI agents into a safe, auditable, and governable product that enterprises can trust for real-world execution.
