# Project Brief

## Product

ATower Of Agents is a CRM/HRMS-like operating system for AI agents. An operator chooses an enterprise workflow, uploads company artifacts, assembles specialist agents in a Band room, and receives an auditable decision packet grounded in retrieved evidence.

## MVP

Deep workflows:

- HR Candidate Screening: upload resume, job description, and hiring policy; index artifacts; run matching, fairness, interview, policy, and final-decision agents; display findings, citations, collaboration messages, and human-review status.
- Vendor Onboarding Review: upload vendor profile, contract, security documentation, and pricing; run procurement, legal, security, finance, compliance, and controller agents; display `report_payload.decision_packet` for human approval.

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
