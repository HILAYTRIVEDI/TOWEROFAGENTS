# Agent Design

Every agent implements the same contract:

```text
AgentInput -> AgentFinding
```

An input identifies workflow, organization, task, evidence chunks, artifacts, and optional Band room. A finding includes agent identity, type, severity, content, evidence IDs, confidence, and human-review status.

## Planned Platform Agents

- Workflow Router
- RAG Retriever
- Policy Guardian
- Final Decision Agent

## Planned Specialists

- HR: Resume/JD Matcher, Bias Reviewer, Interview Planner
- Sales: Lead Qualifier
- Engineering: Engineering Reviewer

Agents must persist findings and post concise Band updates when a room exists. Missing evidence must be stated; citations may never be invented. Bootstrap classes expose metadata and fail explicitly if execution is attempted.

