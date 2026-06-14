# Band of Agents Hackathon — Thorough Review and Project Fit

Source reviewed: https://lablab.ai/ai-hackathons/band-of-agents-hackathon  
Date reviewed: 2026-06-14

## 1. Hackathon Summary

**Event:** Band of Agents Hackathon  
**Theme:** Build enterprise multi-agent systems with Band and Codeband  
**Dates:** June 12–19, 2026  
**Format:** Fully online  
**Prize pool:** $10,000+  

The hackathon is focused on practical enterprise workflows where AI agents communicate, coordinate, exchange context, and complete work together. The central expectation is not simply “use agents,” but to build a system where agent-to-agent collaboration is visible, useful, and core to the workflow.

## 2. Core Challenge

The challenge is to build a **cross-framework multi-agent system with Band**.

Minimum requirement:

- At least **3 agents**
- Agents must collaborate **through Band**
- Collaboration must involve meaningful task handoff, shared context, delegation, state coordination, review, or decision-making
- Band must be part of the actual workflow, not just a notification/output layer

This means a standard LangGraph RAG app with internal nodes is **not enough** unless those agents are exposed as Band-connected agents that communicate in a Band room.

## 3. Tracks

### Track 1: Internal Enterprise Workflows

Best for workflows across departments, approvals, handoffs, reporting, support escalation, procurement, HR, finance, or operations.

### Track 2: Multi-Agent Software Development

Best for coding-agent workflows involving planning, implementation, testing, review, documentation, PR preparation, debugging, or release coordination.

### Track 3: Regulated & High-Stakes Workflows

Best for healthcare, finance, legal, insurance, cybersecurity, risk, compliance, or workflows where traceability, careful review, escalation, and audit trails matter.

## 4. Judging Criteria

### Application of Technology

Judges will evaluate how effectively the solution uses Band as the coordination layer between specialized agents. Strong submissions should show:

- Clear task handoffs
- Shared context
- Role specialization
- Task state
- Coordination through Band

### Presentation

The demo must clearly explain:

- The problem
- Agent roles
- How Band coordinates the agents
- How context flows
- Where handoffs happen
- The enterprise value

### Business Value

The project should solve a real enterprise workflow problem by reducing manual coordination, improving decision-making, accelerating execution, or simplifying a complex process.

### Originality

The project should go beyond a chatbot, single-agent assistant, or simple linear automation. It should show what becomes possible when agents can discover, coordinate, divide work, review outputs, escalate issues, or collaborate across frameworks.

## 5. Partner Platforms and Credits

### Band

Participants can use promo code `BANDHACK26` for 100% off Band Pro for 1 month. Band may still require card details during checkout, so cancel before renewal if not continuing.

### AI/ML API

AI/ML API provides model access through a unified API. Hackathon access listed on the event page:

- $10 per person
- Up to 500 participants
- Valid until the hackathon ends
- Redeem through lablab.ai

Suggested use in project:

- Main reasoning model
- Summarization agent
- Extraction agent
- Multimodal or automation-heavy workflows
- Partner prize target: Best Use of AI/ML API

### Featherless AI

Featherless provides serverless inference for open-source models.

Hackathon access listed on the event page:

- $25 per participant
- Up to 1,000 participants
- First-come, first-served
- Valid for 1 month from activation
- Promo code: `BOA26`

Suggested use in project:

- Open-source specialist models
- Low-cost reviewer/judge agents
- Document classifier
- Extraction agent
- Domain-specialized reasoning agent
- Partner prize target: Best Use of Featherless AI

## 6. Submission Requirements

The submission asks for:

- Project title
- Short description
- Long description
- Technology and category tags
- Cover image
- Video presentation
- Slide presentation
- Public GitHub repository
- Demo application platform
- Application URL

Therefore the project should be built with a polished demo in mind from day one.

## 7. Current Submitted Projects Pattern

The submitted examples on the page show a clear pattern: most strong projects are enterprise/high-stakes workflows, not simple assistant apps. Common themes include:

- Compliance orchestration
- Financial crime investigation
- Contract risk review
- Procurement/vendor risk approval
- Incident response
- Medical prior authorization
- Decision desks
- Multi-agent software delivery

Your project should position itself in this same class: serious enterprise workflow, auditable, agent collaboration visible, and Band deeply integrated.

## 8. Best Project Direction for Your Goal

Your earlier goal: create a multi-agent architecture system with LangGraph and QA/RAG, using AIML API and Featherless models.

For this hackathon, the strongest version would be:

# “Enterprise Evidence QA War Room”

A Band-coordinated multi-agent QA/RAG system for enterprise documents where several specialist agents debate, verify, and approve answers before delivering an audit-ready final response.

## Recommended Track

Track 3: Regulated & High-Stakes Workflows

This is stronger than a generic RAG demo because QA/RAG can be framed as a high-stakes evidence-verification workflow for compliance, legal, financial, or internal policy decisions.

## 9. Proposed Agent Architecture

Minimum 3 agents, but use 5 for a stronger demo:

### 1. Intake / Coordinator Agent

Responsibilities:

- Receives the user question
- Creates the Band room workflow
- Mentions the right agents
- Tracks task state
- Decides whether escalation is needed
- Produces final response only after review

Band usage:

- Uses `@Retriever`, `@Verifier`, `@RiskReviewer`, and `@AnswerComposer`
- Posts workflow state events
- Requests rework when evidence is weak

### 2. Retriever Agent

Responsibilities:

- Queries vector DB
- Runs hybrid retrieval
- Performs metadata filtering
- Returns top chunks with citations, source names, page numbers, timestamps, and confidence

Model provider:

- AIML API for reasoning/summarization
- Embedding model from AIML API or Featherless, depending availability

Band usage:

- Sends retrieved evidence into Band room
- Posts retrieval metadata as structured events

### 3. Evidence Verifier / Judge Agent

Responsibilities:

- Checks whether retrieved evidence actually supports the claim
- Detects unsupported answer spans
- Scores faithfulness, context relevance, and citation quality
- Requests more retrieval if needed

Model provider:

- Featherless open-source model for independent verification

Band usage:

- Reviews Retriever’s evidence inside Band
- Sends verdict to Coordinator and AnswerComposer

### 4. Risk / Compliance Reviewer Agent

Responsibilities:

- Checks if the answer contains policy risk, legal risk, hallucination risk, privacy risk, or missing caveats
- Decides whether human approval is required
- Adds escalation labels

Model provider:

- Featherless specialized or smaller model
- AIML API for stronger reasoning if needed

Band usage:

- Posts risk report as an event
- Mentions Coordinator if escalation is required

### 5. Answer Composer Agent

Responsibilities:

- Produces final answer
- Uses only approved evidence
- Includes citations
- Includes uncertainty where evidence is weak
- Avoids unsupported claims

Model provider:

- AIML API high-quality chat model

Band usage:

- Waits for Verifier and RiskReviewer before answering
- Posts final answer back into the Band room

## 10. LangGraph + Band Design

Important: LangGraph alone should not hide the collaboration. Use LangGraph inside each agent where helpful, but let Band be the visible coordination layer.

Recommended structure:

- Each specialist agent is a separate Band external agent.
- Each agent may internally use LangGraph for its local logic.
- The agents communicate through Band rooms using @mentions.
- Band room becomes the audit trail.
- LangGraph handles local state transitions.
- Band handles cross-agent communication, visibility, routing, and handoff.

Bad design:

- One LangGraph graph with 5 internal nodes
- Final output posted to Band
- Band only used as UI

Good design:

- Coordinator asks Retriever in Band
- Retriever posts evidence in Band
- Verifier challenges evidence in Band
- RiskReviewer flags issues in Band
- Composer creates final answer after visible approval in Band

## 11. Demo Flow

Use one enterprise scenario, for example:

### Scenario: Vendor Contract / Compliance QA

User asks:

“Can we approve this vendor under our internal procurement and data privacy policy?”

Workflow:

1. Coordinator receives the question.
2. Coordinator mentions Retriever.
3. Retriever fetches relevant clauses from policy, vendor questionnaire, contract, and data processing terms.
4. Retriever posts chunks with citations.
5. Coordinator mentions Verifier.
6. Verifier checks if evidence supports approval/rejection.
7. RiskReviewer checks privacy/compliance risks.
8. If risk is high, Coordinator asks for human approval.
9. AnswerComposer drafts final decision packet:
   - Decision: approve / reject / needs review
   - Evidence
   - Risks
   - Missing documents
   - Recommended next actions
   - Audit trail summary

## 12. Why This Fits Judging Criteria

### Application of Technology

Strong fit because Band is used as the real coordination layer. The agents hand off tasks, share context, review outputs, and route decisions through Band.

### Presentation

Strong fit because the Band room visually shows the workflow. Judges can see who did what, when, and why.

### Business Value

Strong fit because enterprise QA over compliance/policy/vendor documents is a real business problem with high cost of errors.

### Originality

Stronger than chatbot RAG because it adds adversarial verification, risk review, multi-model checks, and human escalation.

## 13. What to Avoid

Avoid building:

- A normal chatbot over PDFs
- A single LangGraph workflow with hidden nodes
- A demo where Band only receives the final answer
- A toy use case with no enterprise value
- A workflow with no visible handoff
- A project without an audit trail
- A project that uses AIML API / Featherless only superficially

## 14. MVP Scope for One-Day Build

Build only what directly helps judging.

### Must Build

- Band-connected Coordinator, Retriever, Verifier, and Composer agents
- One document ingestion pipeline
- Vector search
- Citation-bearing RAG
- Judge/verifier scoring
- Final audit-ready answer
- Simple UI or CLI trigger
- Public GitHub repo
- Short demo video

### Should Build

- Risk reviewer agent
- Human-in-the-loop approval flag
- Agent event logs
- JSON state object for each task

### Skip

- User auth
- Complex dashboards
- Multi-tenant architecture
- Large-scale ingestion
- Payment/billing
- Fully production deployment
- Heavy analytics

## 15. Recommended Tech Stack

Frontend:

- Next.js or Streamlit
- Use the fastest one for demo

Backend:

- Python FastAPI
- LangGraph for local agent workflows
- Band SDK with LangGraph adapter
- Async workers for each agent

Retrieval:

- PostgreSQL + pgvector, or Chroma for fastest MVP
- Hybrid retrieval if time allows
- Store metadata: source, document_type, page, chunk_id, section_title, timestamp, hash

Models:

- AIML API: main reasoning, final answer, summarization
- Featherless: verifier, risk reviewer, classifier, open-source model comparison

Observability:

- Band room messages/events
- Local logs
- Optional LangSmith if already familiar, but not mandatory

Deployment:

- Vercel for frontend
- Render / Railway / Fly.io / your VPS for backend
- Supabase for pgvector if using managed Postgres
- Docker Compose for reproducibility

## 16. Strong Submission Positioning

Project title ideas:

- EvidenceOps: Band-Coordinated Enterprise QA
- TrustRoom AI: Multi-Agent Evidence Review for Enterprise QA
- AuditRAG War Room
- PolicyDesk: Multi-Agent Compliance QA
- VeritasMesh: Agentic Evidence QA

Best tagline:

“A Band-powered enterprise QA war room where retrieval, verification, risk review, and final answer generation happen through visible multi-agent collaboration.”

## 17. One-Sentence Pitch

“TrustRoom AI turns high-stakes enterprise document QA into a Band-coordinated agent room where a retriever, verifier, risk reviewer, and answer composer collaborate across AIML API and Featherless models to produce cited, auditable, human-reviewable answers.”

## 18. Final Recommendation

Your earlier LangGraph + QA/RAG idea is valid, but only if you reposition it as an enterprise workflow and make Band central. Do not pitch it as “RAG chatbot.” Pitch it as “multi-agent evidence review and decision workflow.”

The winning angle is:

- Band = visible coordination and audit layer
- LangGraph = internal local reasoning engine for each specialist
- AIML API = strong reasoning and final answer generation
- Featherless = open-source independent reviewer/verifier agents
- RAG = evidence grounding
- Judge = hallucination and support verification
- Human escalation = enterprise trust
