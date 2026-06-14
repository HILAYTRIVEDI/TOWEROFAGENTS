# Project Brief

## Product

ATower Of Agents is a CRM/HRMS-like operating system for AI agents. An operator chooses an enterprise workflow, uploads company artifacts, assembles specialist agents in a Band room, and receives an auditable decision packet grounded in retrieved evidence.

## MVP

The deep workflow is HR Candidate Screening:

1. Upload resume, job description, and hiring policy.
2. Create a workflow and Band room.
3. Index artifacts in Supabase pgvector.
4. Run matching, fairness, interview, policy, and final-decision agents.
5. Display findings, citations, collaboration messages, and human-review status.

Breadth templates:

- Sales Lead Qualification
- Engineering Change Review

## Bootstrap Scope

This phase establishes repository rules, architecture and API contracts, typed skeletons, migrations, mock-safe integration boundaries, and runnable frontend/backend shells. It excludes product workflow logic and live third-party integrations.

## Success Criteria

- New contributors can install and run both apps from documented commands.
- `GET /health` responds without external credentials.
- Contracts are represented in docs, Pydantic, and TypeScript.
- Database migrations define the required tenant-scoped records and vector search.
- Provider and Band mocks are explicit and replaceable.
- Placeholder UI routes communicate what is and is not implemented.

