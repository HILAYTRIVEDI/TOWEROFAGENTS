# Vendor Onboarding / Procurement Review Workflow Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a Vendor Onboarding / Procurement Review workflow that runs six role-based specialist agents (Procurement, Legal, Security, Finance, Compliance, Controller) over vendor documents and emits a structured, evidence-backed decision packet for human approval — entirely additively, leaving the existing HR workflow untouched and reusable as a template for future enterprise workflows.

**Architecture:** This is a new template wired through the *existing* LangGraph linear-chain runtime. Five specialist agents follow the `ResumeJDMatcherAgent` pattern (LLM call → typed `AgentFinding`, mock discipline preserved). A new `VendorControllerAgent` consumes prior findings (via a generalized `consumes_prior_findings` flag) and emits a `final_decision`-typed finding using vendor vocabulary. A pure, reusable `build_decision_packet(...)` function assembles a generic `DecisionPacket` from the ordered findings; the report node attaches it to `report.report_payload["decision_packet"]` and the executor merges it into the persisted `payload` dict (the value that reaches the `report_payload` DB column). HR's `make_report_node` logic stays byte-for-byte intact.

**Tech Stack:** Python 3.12+ (Pydantic v2, `StrEnum`, `X | None`), FastAPI, LangGraph `StateGraph`, Supabase (Postgres/pgvector, seed SQL), pytest; Next.js 14 (App Router, TypeScript strict) for the dashboard.

## Global Constraints

- Do not remove or alter the existing HR (`hr-candidate-screening`) workflow behavior. *(spec)*
- Do not add unrelated features. *(spec)*
- Do not introduce unnecessary/new dependencies — use only what is already in the repo. *(spec)*
- Keep this workflow reusable as a template for future enterprise workflows — the decision packet builder and controller plumbing must be generic, not vendor-specific. *(spec)*
- Make the smallest clean changes needed; production-oriented and readable. *(spec)*
- Never claim a mock is a real integration: when `result.provider == "mock"`, prefix content with `"[PLACEHOLDER — mock provider was used, no external model was called] "`, prefix title with `"[Mock] "`, set `confidence=0.0`, severity `"info"`. *(CLAUDE.md / AGENTS.md)*
- Never invent evidence IDs or citations — evidence IDs come only from `agent_input.context_chunks[].id`. *(AGENTS.md)*
- Never put secrets in code, prompts, fixtures, seeds, or commits. *(CLAUDE.md)*
- Keep external providers behind the typed `ChatProvider` interface with explicit mock/unconfigured states. *(CLAUDE.md)*
- Agent outputs are advisory; the decision packet always sets `human_approval_required = True` in the MVP. *(AGENTS.md)*
- TypeScript strict mode; no `any` without documented justification. *(AGENT.md)*

---

## File Structure

**New files:**
- `apps/api/agents/vendor/__init__.py` — package marker for vendor specialist agents.
- `apps/api/agents/vendor/procurement_agent.py` — `ProcurementAgent` (business need, pricing, procurement policy).
- `apps/api/agents/vendor/legal_agent.py` — `LegalAgent` (contract risks and terms).
- `apps/api/agents/vendor/security_agent.py` — `SecurityAgent` (data/security risks, missing security docs).
- `apps/api/agents/vendor/finance_agent.py` — `FinanceAgent` (budget and cost concerns).
- `apps/api/agents/vendor/compliance_agent.py` — `ComplianceAgent` (policy and regulatory fit).
- `apps/api/agents/vendor/vendor_controller.py` — `VendorControllerAgent` (final recommendation; consumes prior findings; vendor vocabulary).
- `apps/api/workflows/decision_packet.py` — generic `DecisionPacket` builder: `build_decision_packet(...)`.
- `apps/api/tests/test_vendor_agents.py` — specialist + controller agent behavior tests.
- `apps/api/tests/test_decision_packet.py` — decision-packet builder tests.
- `apps/api/tests/test_vendor_workflow.py` — end-to-end executor test for the vendor template.

**Modified files:**
- `apps/api/agents/base_agent.py` — add `consumes_prior_findings: bool = False` class attribute.
- `apps/api/agents/registry.py` — import + register the six new agents.
- `apps/api/workflows/templates.py` — add the `vendor-onboarding-review` template entry.
- `apps/api/workflows/agent_nodes.py` — generalize prior-findings plumbing to any `consumes_prior_findings` agent; build + attach the decision packet in the report node.
- `apps/api/workflows/executor.py` — merge the decision packet from the report into the returned `payload`.
- `apps/api/models/schemas.py` — add `DecisionPacket` (+ supporting models) Pydantic model.
- `apps/api/routes/workflows.py` — add vendor doc-type targeted-context queries.
- `supabase/seed.sql` — seed the six vendor agents, the vendor template, and sample vendor documents.
- `apps/web/components/workflow-create-form.tsx` — add the vendor template option + artifact list.
- `apps/web/lib/types.ts` — extend `DocumentType` and add a `DecisionPacket` payload type.
- `apps/web/components/report-review-panel.tsx` — render the decision packet when present (additive, HR path unaffected).

---

## Task 1: Generalize prior-findings plumbing (`consumes_prior_findings`)

> ✅ **COMPLETE** (commit `fc2a1bc`) — 2/2 vendor workflow tests pass, 5/5 HR regression tests pass.
> Implementation note: the flag is read via `getattr(agent, "consumes_prior_findings", False)` on the **instantiated agent** (not the class as Step 4's snippet showed). Semantically identical in production (instance lookup falls back to the class attribute) and correct under the test's lambda-factory monkeypatch, where a class-level `getattr` would always return `False`. The `_FINAL_DECISION_SLUG` disjunct is preserved unchanged.

**Files:**
- Modify: `apps/api/agents/base_agent.py`
- Modify: `apps/api/workflows/agent_nodes.py` (the `make_agent_node` prior-findings branch)
- Test: `apps/api/tests/test_vendor_workflow.py`

**Interfaces:**
- Produces: `BaseAgent.consumes_prior_findings: bool` (class attribute, default `False`). When `True`, `make_agent_node` populates `AgentInput.prior_findings` with `list(state["agent_findings"])` before calling `agent.run(...)`.
- Consumes: existing `make_agent_node(slug, router)` and `AgentInput.prior_findings` from `models/schemas.py`.

- [x] **Step 1: Write the failing test**

Add to `apps/api/tests/test_vendor_workflow.py`:

```python
import asyncio

from agents.base_agent import BaseAgent
from models.schemas import AgentFinding, AgentInput


class _PriorFindingsSpy(BaseAgent):
    slug = "prior-findings-spy"
    name = "Prior Findings Spy"
    category = "platform"
    description = "Test agent that records the prior_findings it received."
    instructions = "noop"
    consumes_prior_findings = True

    def __init__(self, chat_provider=None) -> None:
        super().__init__(chat_provider)
        self.seen_prior: list[dict] = []

    async def run(self, agent_input: AgentInput) -> AgentFinding:
        self.seen_prior = list(agent_input.prior_findings)
        return AgentFinding(
            agent_name=self.name,
            finding_type="final_decision",
            severity="info",
            title="spy",
            content="spy",
        )


def test_base_agent_defaults_to_not_consuming_prior_findings():
    assert BaseAgent.consumes_prior_findings is False


def test_node_passes_prior_findings_to_consuming_agent(monkeypatch):
    from workflows import agent_nodes

    spy = _PriorFindingsSpy()
    monkeypatch.setitem(agent_nodes.AGENT_CLASS_BY_SLUG, spy.slug, lambda chat_provider=None: spy)

    node = agent_nodes.make_agent_node(spy.slug, router=None)
    state = {
        "workflow_id": "w1",
        "org_id": "o1",
        "user_request": "review",
        "artifacts": [],
        "retrieved_context": [],
        "band_room_id": None,
        "agent_findings": [
            {
                "agent_name": "Procurement Agent",
                "finding_type": "procurement_review",
                "severity": "info",
                "title": "prior",
                "content": "prior body",
                "evidence_chunk_ids": [],
                "confidence": 0.5,
                "requires_human_review": True,
            }
        ],
    }
    asyncio.run(node(state))
    assert spy.seen_prior and spy.seen_prior[0]["title"] == "prior"
```

> Note: confirm during implementation that `make_agent_node` reads `AGENT_CLASS_BY_SLUG` as a module-level reference (so `monkeypatch.setitem` is observed). If it imports the dict locally inside the closure, patch the same name the closure resolves.

- [x] **Step 2: Run test to verify it fails**

Run: `cd apps/api && python -m pytest tests/test_vendor_workflow.py -v`
Expected: FAIL — `AttributeError: type object 'BaseAgent' has no attribute 'consumes_prior_findings'` (and the node test fails because prior findings are only passed for `final-decision`).

- [x] **Step 3: Add the class attribute to `BaseAgent`**

In `apps/api/agents/base_agent.py`, add to the `BaseAgent` class body alongside the other class attributes:

```python
class BaseAgent(ABC):
    slug: str
    name: str
    category: str
    description: str
    instructions: str
    # When True, the workflow node fills AgentInput.prior_findings with the
    # accumulated findings so controller-style agents can synthesize them.
    consumes_prior_findings: bool = False
```

- [x] **Step 4: Generalize the node's prior-findings branch**

In `apps/api/workflows/agent_nodes.py`, replace the slug-equality check that gates prior-findings population. The existing code passes `prior_findings` only when `slug == _FINAL_DECISION_SLUG`. Change it to consult the agent class:

```python
agent_cls = AGENT_CLASS_BY_SLUG[slug]
consumes_prior = getattr(agent_cls, "consumes_prior_findings", False) or slug == _FINAL_DECISION_SLUG
prior_findings = list(state["agent_findings"]) if consumes_prior else []
```

Keep the `slug == _FINAL_DECISION_SLUG` disjunct so the existing HR `final-decision` agent keeps receiving prior findings even though it does not yet set the flag. (Optionally also set `consumes_prior_findings = True` on `FinalDecisionAgent` and drop the disjunct — only do this if it does not change HR behavior; the safe default for this plan is to keep the disjunct.)

- [x] **Step 5: Run tests to verify they pass**

Run: `cd apps/api && python -m pytest tests/test_vendor_workflow.py -v`
Expected: PASS (both tests).

Also run the existing suite to confirm no HR regression:
Run: `cd apps/api && python -m pytest tests/test_final_decision.py -v`
Expected: PASS.

- [x] **Step 6: Commit**

```bash
git add apps/api/agents/base_agent.py apps/api/workflows/agent_nodes.py apps/api/tests/test_vendor_workflow.py
git commit -m "feat(agents): generalize prior-findings plumbing via consumes_prior_findings flag"
```

---

## Task 2: Vendor specialist agents (Procurement, Legal, Security, Finance, Compliance)

**Files:**
- Create: `apps/api/agents/vendor/__init__.py`
- Create: `apps/api/agents/vendor/procurement_agent.py`
- Create: `apps/api/agents/vendor/legal_agent.py`
- Create: `apps/api/agents/vendor/security_agent.py`
- Create: `apps/api/agents/vendor/finance_agent.py`
- Create: `apps/api/agents/vendor/compliance_agent.py`
- Test: `apps/api/tests/test_vendor_agents.py`

**Interfaces:**
- Produces five classes (`ProcurementAgent`, `LegalAgent`, `SecurityAgent`, `FinanceAgent`, `ComplianceAgent`), each subclassing `BaseAgent` with `category = "vendor"`, distinct `slug`, and `run(agent_input) -> AgentFinding`. Slugs: `procurement-review`, `legal-review`, `security-review`, `finance-review`, `compliance-review`. Each emits a `finding_type` of `procurement_review` / `legal_review` / `security_review` / `finance_review` / `compliance_review` respectively.
- Consumes: `agents.base_agent.BaseAgent`, `models.schemas.AgentInput`/`AgentFinding`, `self._chat_provider.complete(...)` returning an object with `.provider` (str) and `.content` (str).

- [x] **Step 1: Write the failing test**

Create `apps/api/tests/test_vendor_agents.py`:

```python
import asyncio

import pytest

from agents.vendor.compliance_agent import ComplianceAgent
from agents.vendor.finance_agent import FinanceAgent
from agents.vendor.legal_agent import LegalAgent
from agents.vendor.procurement_agent import ProcurementAgent
from agents.vendor.security_agent import SecurityAgent
from models.schemas import AgentInput

SPECIALISTS = [
    (ProcurementAgent, "procurement-review", "procurement_review"),
    (LegalAgent, "legal-review", "legal_review"),
    (SecurityAgent, "security-review", "security_review"),
    (FinanceAgent, "finance-review", "finance_review"),
    (ComplianceAgent, "compliance-review", "compliance_review"),
]


class _FakeProvider:
    def __init__(self, provider_name: str, content: str) -> None:
        self.provider = provider_name
        self._content = content
        self.calls: list[list[dict]] = []

    async def complete(self, messages):
        self.calls.append(messages)

        class _Result:
            provider = self.provider
            content = self._content

        return _Result()


def _make_input(**kwargs):
    defaults = dict(
        workflow_id="w1",
        org_id="o1",
        task="Review vendor Acme Corp for onboarding.",
        context_chunks=[
            {
                "id": "11111111-1111-1111-1111-111111111111",
                "content": "Vendor master service agreement, net-60 payment terms.",
                "metadata": {"doc_type": "contract", "filename": "msa.pdf"},
            }
        ],
        artifacts=[{"filename": "msa.pdf", "doc_type": "contract"}],
    )
    defaults.update(kwargs)
    return AgentInput(**defaults)


@pytest.mark.parametrize("agent_cls,slug,finding_type", SPECIALISTS)
def test_specialist_metadata(agent_cls, slug, finding_type):
    agent = agent_cls()
    assert agent.slug == slug
    assert agent.category == "vendor"
    assert agent.consumes_prior_findings is False


@pytest.mark.parametrize("agent_cls,slug,finding_type", SPECIALISTS)
def test_no_provider_raises(agent_cls, slug, finding_type):
    agent = agent_cls(chat_provider=None)
    with pytest.raises(RuntimeError, match="chat_provider"):
        asyncio.run(agent.run(_make_input()))


@pytest.mark.parametrize("agent_cls,slug,finding_type", SPECIALISTS)
def test_non_mock_provider_returns_finding(agent_cls, slug, finding_type):
    provider = _FakeProvider("aimlapi", "Specialist analysis body.")
    agent = agent_cls(chat_provider=provider)
    finding = asyncio.run(agent.run(_make_input()))
    assert finding.finding_type == finding_type
    assert finding.evidence_chunk_ids == ["11111111-1111-1111-1111-111111111111"]
    assert finding.requires_human_review is True
    assert "[PLACEHOLDER" not in finding.content


@pytest.mark.parametrize("agent_cls,slug,finding_type", SPECIALISTS)
def test_mock_provider_annotates_and_requires_review(agent_cls, slug, finding_type):
    provider = _FakeProvider("mock", "ignored mock body")
    agent = agent_cls(chat_provider=provider)
    finding = asyncio.run(agent.run(_make_input()))
    assert finding.content.startswith("[PLACEHOLDER")
    assert finding.title.startswith("[Mock]")
    assert finding.confidence == 0.0


@pytest.mark.parametrize("agent_cls,slug,finding_type", SPECIALISTS)
def test_evidence_ids_from_context_chunks_only(agent_cls, slug, finding_type):
    provider = _FakeProvider("aimlapi", "body")
    agent = agent_cls(chat_provider=provider)
    finding = asyncio.run(agent.run(_make_input(context_chunks=[])))
    assert finding.evidence_chunk_ids == []
```

- [x] **Step 2: Run test to verify it fails**

Run: `cd apps/api && python -m pytest tests/test_vendor_agents.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'agents.vendor'`.

- [x] **Step 3: Create the package marker**

Create `apps/api/agents/vendor/__init__.py`:

```python
```

(Empty file.)

- [x] **Step 4: Implement the specialist agents**

These five files share one structure — the same body as `agents/hr/resume_jd_matcher.py`, differing only in `slug`, `name`, `description`, `instructions`, and `finding_type`. Create each file with the full code below (repeated per file with its own values — do not abbreviate).

`apps/api/agents/vendor/procurement_agent.py`:

```python
from agents.base_agent import BaseAgent
from models.schemas import AgentFinding, AgentInput

_MOCK_PREFIX = "[PLACEHOLDER — mock provider was used, no external model was called] "

_INSTRUCTIONS = (
    "You are the Procurement Agent in an enterprise vendor-onboarding review. "
    "Assess the business need for this vendor, whether pricing is reasonable and "
    "competitive, and whether the engagement follows procurement policy. "
    "Cite only the supplied document excerpts. Be specific about gaps."
)


class ProcurementAgent(BaseAgent):
    slug = "procurement-review"
    name = "Procurement Agent"
    category = "vendor"
    description = "Reviews business need, pricing, and procurement policy fit."
    instructions = _INSTRUCTIONS

    async def run(self, agent_input: AgentInput) -> AgentFinding:
        if self._chat_provider is None:
            raise RuntimeError("ProcurementAgent requires a chat_provider")

        chunk_lines: list[str] = []
        evidence_ids: list[str] = []
        for chunk in agent_input.context_chunks:
            chunk_id = chunk.get("id")
            if chunk_id is None:
                continue
            evidence_ids.append(str(chunk_id))
            metadata = chunk.get("metadata") or {}
            doc_type = metadata.get("doc_type", "document")
            filename = metadata.get("filename", "unknown")
            content = str(chunk.get("content", ""))[:200]
            chunk_lines.append(f"[{chunk_id}] ({doc_type} · {filename}) {content}")

        artifact_names = ", ".join(
            str(a.get("filename", "unknown")) for a in agent_input.artifacts
        ) or "none"

        system_msg = (
            self.instructions
            + "\n\nSTRICT GUARDRAILS:\n"
            "- Cite only the bracketed chunk IDs provided. Never invent citations.\n"
            "- If evidence is missing, say so explicitly under a 'Missing information' note.\n"
            "- Keep the analysis advisory; a human makes the final decision."
        )
        user_msg = (
            f"TASK: {agent_input.task}\n"
            f"ARTIFACTS: {artifact_names}\n"
            f"DOCUMENT EXCERPTS:\n" + ("\n".join(chunk_lines) or "none") + "\n\n"
            "Provide your procurement assessment."
        )

        result = await self._chat_provider.complete(
            [{"role": "system", "content": system_msg}, {"role": "user", "content": user_msg}]
        )
        is_mock = result.provider == "mock"

        content = result.content
        title = "Procurement assessment"
        if is_mock:
            content = _MOCK_PREFIX + content
            title = "[Mock] " + title

        return AgentFinding(
            agent_name=self.name,
            finding_type="procurement_review",
            severity="info",
            title=title,
            content=content,
            evidence_chunk_ids=evidence_ids,
            confidence=0.0 if is_mock else 0.5,
            requires_human_review=True,
        )
```

`apps/api/agents/vendor/legal_agent.py` — identical structure with these values:
- `slug = "legal-review"`, `name = "Legal Agent"`, `category = "vendor"`
- `description = "Reviews contract risks and terms."`
- `_INSTRUCTIONS = "You are the Legal Agent in an enterprise vendor-onboarding review. Identify contract risks, unfavorable terms, liability, indemnity, termination, and IP clauses. Cite only the supplied document excerpts. Flag missing contract language explicitly."`
- `title = "Legal risk assessment"`, `finding_type="legal_review"`
- `RuntimeError("LegalAgent requires a chat_provider")`

`apps/api/agents/vendor/security_agent.py`:
- `slug = "security-review"`, `name = "Security Agent"`, `category = "vendor"`
- `description = "Reviews data/security risks and missing security documentation."`
- `_INSTRUCTIONS = "You are the Security Agent in an enterprise vendor-onboarding review. Assess data-handling and security risk, certifications (e.g. SOC 2, ISO 27001), data residency, and explicitly list any missing security documentation. Cite only the supplied document excerpts."`
- `title = "Security risk assessment"`, `finding_type="security_review"`
- `RuntimeError("SecurityAgent requires a chat_provider")`

`apps/api/agents/vendor/finance_agent.py`:
- `slug = "finance-review"`, `name = "Finance Agent"`, `category = "vendor"`
- `description = "Reviews budget and cost concerns."`
- `_INSTRUCTIONS = "You are the Finance Agent in an enterprise vendor-onboarding review. Assess total cost, budget fit, payment terms, and hidden or recurring costs. Cite only the supplied document excerpts. Flag missing financial information explicitly."`
- `title = "Financial assessment"`, `finding_type="finance_review"`
- `RuntimeError("FinanceAgent requires a chat_provider")`

`apps/api/agents/vendor/compliance_agent.py`:
- `slug = "compliance-review"`, `name = "Compliance Agent"`, `category = "vendor"`
- `description = "Reviews policy and regulatory fit."`
- `_INSTRUCTIONS = "You are the Compliance Agent in an enterprise vendor-onboarding review. Assess regulatory and internal-policy fit (e.g. GDPR, HIPAA, anti-bribery) and explicitly list compliance gaps. Cite only the supplied document excerpts."`
- `title = "Compliance assessment"`, `finding_type="compliance_review"`
- `RuntimeError("ComplianceAgent requires a chat_provider")`

- [x] **Step 5: Run tests to verify they pass**

Run: `cd apps/api && python -m pytest tests/test_vendor_agents.py -v`
Expected: PASS (all parametrized cases).

- [x] **Step 6: Commit**

```bash
git add apps/api/agents/vendor/ apps/api/tests/test_vendor_agents.py
git commit -m "feat(agents): add vendor specialist agents (procurement/legal/security/finance/compliance)"
```

> ✅ **COMPLETE** — 25/25 vendor specialist agent tests pass.
> Implementation note: test commands used `python3` because `python` is not available on this machine's PATH. The initial red check failed as expected with `ModuleNotFoundError: No module named 'agents.vendor'`; final green check was `cd apps/api && python3 -m pytest tests/test_vendor_agents.py -v`.

---

## Task 3: Vendor Controller agent

**Files:**
- Create: `apps/api/agents/vendor/vendor_controller.py`
- Test: `apps/api/tests/test_vendor_agents.py` (append a controller section)

**Interfaces:**
- Produces: `VendorControllerAgent(BaseAgent)` — `slug = "vendor-controller"`, `category = "vendor"`, `consumes_prior_findings = True`, `run(agent_input) -> AgentFinding` with `finding_type = "final_decision"`. Its content begins with a `RECOMMENDATION:` line whose value is one of `approve`, `reject`, `conditional_approval`, `needs_review` (vendor vocabulary, distinct from HR's advance/decline). It renders `agent_input.prior_findings` into the prompt.
- Consumes: `AgentInput.prior_findings` (populated by Task 1's plumbing).

- [x] **Step 1: Write the failing test**

Append to `apps/api/tests/test_vendor_agents.py`:

```python
from agents.vendor.vendor_controller import VendorControllerAgent


def _prior_finding(name, body):
    return {
        "agent_name": name,
        "finding_type": "procurement_review",
        "severity": "info",
        "title": f"{name} title",
        "content": body,
        "evidence_chunk_ids": [],
        "confidence": 0.5,
        "requires_human_review": True,
    }


def test_controller_metadata():
    agent = VendorControllerAgent()
    assert agent.slug == "vendor-controller"
    assert agent.category == "vendor"
    assert agent.consumes_prior_findings is True


def test_controller_renders_prior_findings_into_prompt():
    provider = _FakeProvider("aimlapi", "RECOMMENDATION: conditional_approval\nSUMMARY: ok")
    agent = VendorControllerAgent(chat_provider=provider)
    agent_input = _make_input(
        prior_findings=[_prior_finding("Security Agent", "Missing SOC 2 report.")]
    )
    finding = asyncio.run(agent.run(agent_input))
    assert finding.finding_type == "final_decision"
    # prior findings reach the model
    user_msg = provider.calls[0][1]["content"]
    assert "Security Agent" in user_msg
    assert "Missing SOC 2 report." in user_msg


def test_controller_mock_annotates():
    provider = _FakeProvider("mock", "RECOMMENDATION: approve")
    agent = VendorControllerAgent(chat_provider=provider)
    finding = asyncio.run(agent.run(_make_input(prior_findings=[])))
    assert finding.content.startswith("[PLACEHOLDER")
    assert finding.title.startswith("[Mock]")
    assert finding.confidence == 0.0
```

- [x] **Step 2: Run test to verify it fails**

Run: `cd apps/api && python -m pytest tests/test_vendor_agents.py -k controller -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'agents.vendor.vendor_controller'`.

- [x] **Step 3: Implement the controller**

Create `apps/api/agents/vendor/vendor_controller.py`:

```python
from agents.base_agent import BaseAgent
from models.schemas import AgentFinding, AgentInput

_MOCK_PREFIX = "[PLACEHOLDER — mock provider was used, no external model was called] "

_INSTRUCTIONS = (
    "You are the Controller Agent in an enterprise vendor-onboarding review. "
    "Synthesize the specialist findings into one final recommendation for a human "
    "approver. Weigh procurement, legal, security, finance, and compliance input. "
    "Surface disagreements between specialists rather than hiding them."
)


class VendorControllerAgent(BaseAgent):
    slug = "vendor-controller"
    name = "Controller Agent"
    category = "vendor"
    description = "Synthesizes specialist findings into a final vendor recommendation."
    instructions = _INSTRUCTIONS
    consumes_prior_findings = True

    async def run(self, agent_input: AgentInput) -> AgentFinding:
        if self._chat_provider is None:
            raise RuntimeError("VendorControllerAgent requires a chat_provider")

        prior_lines: list[str] = []
        evidence_ids: list[str] = []
        for finding in agent_input.prior_findings:
            name = finding.get("agent_name", "Specialist")
            title = finding.get("title", "")
            body = str(finding.get("content", ""))[:400]
            prior_lines.append(f"- {name}: {title}\n  {body}")
            for cid in finding.get("evidence_chunk_ids", []) or []:
                if cid not in evidence_ids:
                    evidence_ids.append(str(cid))
        prior_block = "\n".join(prior_lines) or "No specialist findings were produced."

        system_msg = (
            self.instructions
            + "\n\nSTRICT GUARDRAILS:\n"
            "- Begin your answer with a line 'RECOMMENDATION: <value>' where <value> is "
            "exactly one of: approve, reject, conditional_approval, needs_review.\n"
            "- Then provide SUMMARY, KEY RISKS, DISAGREEMENTS, MISSING INFORMATION, and "
            "NEXT ACTIONS sections.\n"
            "- Do not invent evidence. The recommendation is advisory; a human approves."
        )
        user_msg = (
            f"TASK: {agent_input.task}\n\n"
            f"SPECIALIST FINDINGS:\n{prior_block}\n\n"
            "Produce the final vendor recommendation."
        )

        result = await self._chat_provider.complete(
            [{"role": "system", "content": system_msg}, {"role": "user", "content": user_msg}]
        )
        is_mock = result.provider == "mock"

        content = result.content
        title = "Vendor onboarding recommendation"
        if is_mock:
            content = _MOCK_PREFIX + content
            title = "[Mock] " + title

        return AgentFinding(
            agent_name=self.name,
            finding_type="final_decision",
            severity="info",
            title=title,
            content=content,
            evidence_chunk_ids=evidence_ids,
            confidence=0.0 if is_mock else 0.8,
            requires_human_review=True,
        )
```

- [x] **Step 4: Run tests to verify they pass**

Run: `cd apps/api && python -m pytest tests/test_vendor_agents.py -k controller -v`
Expected: PASS.

- [x] **Step 5: Commit**

```bash
git add apps/api/agents/vendor/vendor_controller.py apps/api/tests/test_vendor_agents.py
git commit -m "feat(agents): add vendor controller agent with approve/reject/conditional/needs_review vocabulary"
```

> ✅ **COMPLETE** — 3/3 controller tests pass, 28/28 vendor agent tests pass.
> Implementation note: test commands used `python3` because `python` is not available on this machine's PATH. The initial red check failed as expected with `ModuleNotFoundError: No module named 'agents.vendor.vendor_controller'`; final green checks were `cd apps/api && python3 -m pytest tests/test_vendor_agents.py -k controller -v` and `cd apps/api && python3 -m pytest tests/test_vendor_agents.py -v`.

---

## Task 4: `DecisionPacket` schema + `build_decision_packet` builder

**Files:**
- Modify: `apps/api/models/schemas.py`
- Create: `apps/api/workflows/decision_packet.py`
- Test: `apps/api/tests/test_decision_packet.py`

**Interfaces:**
- Produces (schemas.py):
  - `class DecisionPacketFinding(BaseModel)`: `agent_name: str`, `finding_type: str`, `severity: str`, `title: str`, `content: str`, `evidence_chunk_ids: list[str] = []`, `confidence: float = 0.0`.
  - `class DecisionPacket(BaseModel)`: `recommendation: str`, `executive_summary: str`, `evidence_chunk_ids: list[str] = []`, `agent_findings: list[DecisionPacketFinding] = []`, `risks: list[str] = []`, `missing_information: list[str] = []`, `disagreements: list[str] = []`, `next_actions: list[str] = []`, `human_approval_required: bool = True`, `audit_trail: dict[str, Any] = {}`.
- Produces (decision_packet.py): `build_decision_packet(*, ordered_findings: list[tuple[str, AgentFinding]], controller_finding_type: str = "final_decision", audit_trail: dict[str, Any]) -> DecisionPacket`. Generic over any workflow — it does not hardcode vendor slugs. Recommendation parsing reads the first `RECOMMENDATION:` line of the controller finding's content; if none is found or the controller finding is mock/absent, recommendation falls back to `"needs_review"`.
- Consumes: `models.schemas.AgentFinding`, `DecisionPacket`, `DecisionPacketFinding`.

- [ ] **Step 1: Write the failing test**

Create `apps/api/tests/test_decision_packet.py`:

```python
from models.schemas import AgentFinding
from workflows.decision_packet import build_decision_packet


def _finding(**kwargs):
    base = dict(
        agent_name="Procurement Agent",
        finding_type="procurement_review",
        severity="info",
        title="Procurement assessment",
        content="Business need is clear.",
        evidence_chunk_ids=["11111111-1111-1111-1111-111111111111"],
        confidence=0.5,
        requires_human_review=True,
    )
    base.update(kwargs)
    return AgentFinding(**base)


def _controller(content, confidence=0.8):
    return _finding(
        agent_name="Controller Agent",
        finding_type="final_decision",
        title="Vendor onboarding recommendation",
        content=content,
        confidence=confidence,
        evidence_chunk_ids=[],
    )


def test_recommendation_parsed_from_controller():
    ordered = [
        ("procurement-review", _finding()),
        (
            "vendor-controller",
            _controller("RECOMMENDATION: conditional_approval\nSUMMARY: mostly fine"),
        ),
    ]
    packet = build_decision_packet(ordered_findings=ordered, audit_trail={"workflow_id": "w1"})
    assert packet.recommendation == "conditional_approval"
    assert packet.human_approval_required is True
    assert packet.audit_trail["workflow_id"] == "w1"


def test_executive_summary_uses_controller_body():
    ordered = [("vendor-controller", _controller("RECOMMENDATION: approve\nSUMMARY: green light"))]
    packet = build_decision_packet(ordered_findings=ordered, audit_trail={})
    assert "green light" in packet.executive_summary or "approve" in packet.executive_summary.lower()


def test_evidence_is_deduplicated_union_of_findings():
    ordered = [
        ("procurement-review", _finding(evidence_chunk_ids=["a", "b"])),
        ("legal-review", _finding(evidence_chunk_ids=["b", "c"])),
        ("vendor-controller", _controller("RECOMMENDATION: approve")),
    ]
    packet = build_decision_packet(ordered_findings=ordered, audit_trail={})
    assert packet.evidence_chunk_ids == ["a", "b", "c"]


def test_risks_collect_warning_and_error_findings():
    ordered = [
        ("security-review", _finding(severity="warning", title="Missing SOC 2")),
        ("finance-review", _finding(severity="error", title="Over budget")),
        ("procurement-review", _finding(severity="info", title="Need is clear")),
        ("vendor-controller", _controller("RECOMMENDATION: needs_review")),
    ]
    packet = build_decision_packet(ordered_findings=ordered, audit_trail={})
    assert "Missing SOC 2" in packet.risks
    assert "Over budget" in packet.risks
    assert "Need is clear" not in packet.risks


def test_missing_controller_defaults_to_needs_review():
    ordered = [("procurement-review", _finding())]
    packet = build_decision_packet(ordered_findings=ordered, audit_trail={})
    assert packet.recommendation == "needs_review"


def test_mock_controller_defaults_to_needs_review():
    ordered = [
        (
            "vendor-controller",
            _controller("[PLACEHOLDER …] RECOMMENDATION: approve", confidence=0.0),
        )
    ]
    packet = build_decision_packet(ordered_findings=ordered, audit_trail={})
    assert packet.recommendation == "needs_review"


def test_agent_findings_mirror_inputs():
    ordered = [
        ("procurement-review", _finding()),
        ("vendor-controller", _controller("RECOMMENDATION: approve")),
    ]
    packet = build_decision_packet(ordered_findings=ordered, audit_trail={})
    assert [f.agent_name for f in packet.agent_findings] == ["Procurement Agent", "Controller Agent"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd apps/api && python -m pytest tests/test_decision_packet.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'workflows.decision_packet'`.

- [ ] **Step 3: Add the schemas**

In `apps/api/models/schemas.py`, add after `AgentFinding` (keeping `Any` already imported at top):

```python
class DecisionPacketFinding(BaseModel):
    agent_name: str
    finding_type: str
    severity: str
    title: str
    content: str
    evidence_chunk_ids: list[str] = Field(default_factory=list)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)


class DecisionPacket(BaseModel):
    """Generic, reusable decision packet for any enterprise review workflow."""

    recommendation: str
    executive_summary: str
    evidence_chunk_ids: list[str] = Field(default_factory=list)
    agent_findings: list[DecisionPacketFinding] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    missing_information: list[str] = Field(default_factory=list)
    disagreements: list[str] = Field(default_factory=list)
    next_actions: list[str] = Field(default_factory=list)
    human_approval_required: bool = True
    audit_trail: dict[str, Any] = Field(default_factory=dict)
```

- [ ] **Step 4: Implement the builder**

Create `apps/api/workflows/decision_packet.py`:

```python
"""Generic decision-packet assembly, reusable across enterprise workflows.

Reads the ordered agent findings from a workflow run and produces a structured
DecisionPacket. It is deliberately workflow-agnostic: it keys on finding_type
and severity, never on vendor-specific slugs.
"""
from __future__ import annotations

import re
from typing import Any

from models.schemas import AgentFinding, DecisionPacket, DecisionPacketFinding

_VALID_RECOMMENDATIONS = {"approve", "reject", "conditional_approval", "needs_review"}
_RECOMMENDATION_RE = re.compile(r"RECOMMENDATION:\s*([a-z_]+)", re.IGNORECASE)
_RISK_SEVERITIES = {"warning", "error"}
_SECTION_RE = "{label}:\\s*(.+?)(?:\\n[A-Z][A-Z ]+:|\\Z)"


def _parse_recommendation(content: str) -> str | None:
    match = _RECOMMENDATION_RE.search(content)
    if not match:
        return None
    value = match.group(1).strip().lower()
    return value if value in _VALID_RECOMMENDATIONS else None


def _parse_list_section(content: str, label: str) -> list[str]:
    match = re.search(_SECTION_RE.format(label=re.escape(label)), content, re.DOTALL | re.IGNORECASE)
    if not match:
        return []
    block = match.group(1).strip()
    items = [re.sub(r"^[-*\d.\s]+", "", line).strip() for line in block.splitlines()]
    return [item for item in items if item]


def build_decision_packet(
    *,
    ordered_findings: list[tuple[str, AgentFinding]],
    controller_finding_type: str = "final_decision",
    audit_trail: dict[str, Any],
) -> DecisionPacket:
    controller: AgentFinding | None = None
    for _slug, finding in ordered_findings:
        if finding.finding_type == controller_finding_type:
            controller = finding  # last controller-typed finding wins

    # Recommendation: only trust a non-mock controller (confidence > 0.0).
    recommendation = "needs_review"
    executive_summary = "No controller recommendation was produced; human review required."
    risks: list[str] = []
    missing_information: list[str] = []
    disagreements: list[str] = []
    next_actions: list[str] = []
    if controller is not None and controller.confidence > 0.0:
        parsed = _parse_recommendation(controller.content)
        recommendation = parsed or "needs_review"
        executive_summary = controller.content
        risks = _parse_list_section(controller.content, "KEY RISKS")
        missing_information = _parse_list_section(controller.content, "MISSING INFORMATION")
        disagreements = _parse_list_section(controller.content, "DISAGREEMENTS")
        next_actions = _parse_list_section(controller.content, "NEXT ACTIONS")

    # Always fold specialist warning/error titles into risks (deduplicated, ordered).
    for _slug, finding in ordered_findings:
        if finding.finding_type == controller_finding_type:
            continue
        if finding.severity in _RISK_SEVERITIES and finding.title not in risks:
            risks.append(finding.title)

    # Evidence: ordered union across all findings.
    evidence_ids: list[str] = []
    for _slug, finding in ordered_findings:
        for cid in finding.evidence_chunk_ids:
            if cid not in evidence_ids:
                evidence_ids.append(cid)

    packet_findings = [
        DecisionPacketFinding(
            agent_name=f.agent_name,
            finding_type=f.finding_type,
            severity=f.severity,
            title=f.title,
            content=f.content,
            evidence_chunk_ids=list(f.evidence_chunk_ids),
            confidence=f.confidence,
        )
        for _slug, f in ordered_findings
    ]

    return DecisionPacket(
        recommendation=recommendation,
        executive_summary=executive_summary,
        evidence_chunk_ids=evidence_ids,
        agent_findings=packet_findings,
        risks=risks,
        missing_information=missing_information,
        disagreements=disagreements,
        next_actions=next_actions,
        human_approval_required=True,
        audit_trail=audit_trail,
    )
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd apps/api && python -m pytest tests/test_decision_packet.py -v`
Expected: PASS (all cases).

- [ ] **Step 6: Commit**

```bash
git add apps/api/models/schemas.py apps/api/workflows/decision_packet.py apps/api/tests/test_decision_packet.py
git commit -m "feat(workflows): add generic DecisionPacket schema and builder"
```

---

## Task 5: Attach the decision packet in the report node + persist via executor

**Files:**
- Modify: `apps/api/workflows/agent_nodes.py` (the report node `make_report_node`)
- Modify: `apps/api/workflows/executor.py` (merge packet into returned `payload`)
- Test: `apps/api/tests/test_vendor_workflow.py` (append)

**Interfaces:**
- The report node, after building `WorkflowReportRead`, computes `build_decision_packet(ordered_findings=..., audit_trail=...)` and stores it under `report.report_payload["decision_packet"]` (a JSON dict). The audit trail includes `workflow_id`, `template_slug`, `agents_ran`, `agents_skipped`, `any_mock`, and `generated_at` (ISO string).
- The executor reads `report.report_payload.get("decision_packet")` from the validated report and, when present, sets `payload["decision_packet"] = <that dict>` so it persists in the `report_payload` DB column. HR runs (no controller / no decision packet desired) are unaffected because the packet is built for every run but only carries a real recommendation when a controller finding exists; storing it is harmless and additive. **To honor "do not change HR behavior", gate packet construction on the presence of a controller-typed finding** — see Step 3.

- [ ] **Step 1: Write the failing test**

Append to `apps/api/tests/test_vendor_workflow.py`:

```python
from workflows.executor import WorkflowExecutor


def _vendor_state():
    return {
        "workflow_id": "11111111-1111-1111-1111-111111111111",
        "org_id": "22222222-2222-2222-2222-222222222222",
        "user_request": "Onboard vendor Acme Corp.",
        "template_slug": "vendor-onboarding-review",
        "band_room_id": None,
        "artifacts": [{"filename": "msa.pdf", "doc_type": "contract"}],
        "selected_agents": [
            "procurement-review",
            "legal-review",
            "security-review",
            "finance-review",
            "compliance-review",
            "vendor-controller",
        ],
        "retrieved_context": [
            {
                "id": "33333333-3333-3333-3333-333333333333",
                "content": "Net-60 payment terms, no SOC 2 attached.",
                "metadata": {"doc_type": "contract", "filename": "msa.pdf"},
            }
        ],
        "agent_findings": [],
    }


def test_vendor_run_produces_decision_packet_in_payload():
    # settings=None => executor uses mock provider; packet recommendation is needs_review.
    executor = WorkflowExecutor(settings=None)
    result = asyncio.run(executor.run(_vendor_state()))
    packet = result["payload"].get("decision_packet")
    assert packet is not None
    assert packet["recommendation"] == "needs_review"  # mock controller => needs_review
    assert packet["human_approval_required"] is True
    assert len(packet["agent_findings"]) == 6
    assert packet["audit_trail"]["template_slug"] == "vendor-onboarding-review"
```

> Note: this test exercises the real LangGraph graph with the mock provider. It requires `langgraph` to be installed (already a project dependency). If the agents are not yet registered (Task 6), the executor will raise `KeyError` on the slug — run this test *after* Task 6, or temporarily register via monkeypatch. Recommended: keep this test in the file but mark it to run green only once Task 6 lands. To avoid an ordering trap, this step's "verify fail" is about the packet plumbing, not registration.

- [ ] **Step 2: Run test to verify it fails**

Run: `cd apps/api && python -m pytest tests/test_vendor_workflow.py -k decision_packet -v`
Expected: FAIL — `KeyError: 'decision_packet'` (payload has no such key yet), or `KeyError` on the agent slug if Task 6 has not run. Either failure confirms the feature is absent.

- [ ] **Step 3: Build + attach the packet in the report node**

In `apps/api/workflows/agent_nodes.py`:

Add imports at the top (next to existing imports):

```python
from datetime import datetime, timezone

from workflows.decision_packet import build_decision_packet
```

Inside `make_report_node`'s inner function, after `report` (the `WorkflowReportRead`) is constructed but before returning, insert:

```python
        ordered = list(zip(state["ran_slugs"], findings, strict=False))
        has_controller = any(f.finding_type == _FINAL_DECISION_TYPE for _s, f in ordered)
        if has_controller:
            audit_trail = {
                "workflow_id": state["workflow_id"],
                "template_slug": state.get("template_slug"),
                "agents_ran": list(state["ran_slugs"]),
                "agents_skipped": list(state["skipped_slugs"]),
                "any_mock": any(f.confidence == 0.0 for f in findings),
                "generated_at": datetime.now(timezone.utc).isoformat(),
            }
            packet = build_decision_packet(ordered_findings=ordered, audit_trail=audit_trail)
            report.report_payload["decision_packet"] = packet.model_dump(mode="json")
```

Add a module constant near the other finding-type constants:

```python
_FINAL_DECISION_TYPE = "final_decision"
```

> The existing HR `final-decision` agent also emits `finding_type="final_decision"`, so HR runs will *also* get a packet. That is acceptable and additive (the HR UI ignores it), but if strict "no HR change" is required, key `has_controller` on the controller *slug* set instead: `any(s == "vendor-controller" for s, _f in ordered)`. **Choose the slug-based gate to fully isolate HR.** Use:
>
> ```python
> has_controller = any(slug == "vendor-controller" for slug, _f in ordered)
> ```

Confirm the variable holding the findings list inside `make_report_node` is named `findings` and that `state["ran_slugs"]` is in scope (it is, per the existing node). If the report node reconstructs findings under a different name, align to it.

- [ ] **Step 4: Merge the packet into the executor payload**

In `apps/api/workflows/executor.py`, after `report = WorkflowReportRead.model_validate(...)` and before building the return dict, add:

```python
        decision_packet = report.report_payload.get("decision_packet")
```

Then in the returned `"payload"` dict, append (after `"any_mock": any_mock,`):

```python
                **({"decision_packet": decision_packet} if decision_packet else {}),
```

- [ ] **Step 5: Run tests to verify they pass**

(Run after Task 6 registration is in place.)
Run: `cd apps/api && python -m pytest tests/test_vendor_workflow.py -v`
Expected: PASS.

Regression:
Run: `cd apps/api && python -m pytest tests/ -v`
Expected: PASS (HR tests unchanged; HR payload has no `decision_packet` key because no `vendor-controller` slug ran).

- [ ] **Step 6: Commit**

```bash
git add apps/api/workflows/agent_nodes.py apps/api/workflows/executor.py apps/api/tests/test_vendor_workflow.py
git commit -m "feat(workflows): attach decision packet to report payload for controller-gated runs"
```

---

## Task 6: Register agents + add the vendor template

**Files:**
- Modify: `apps/api/agents/registry.py`
- Modify: `apps/api/workflows/templates.py`
- Test: `apps/api/tests/test_vendor_workflow.py` (append)

**Interfaces:**
- Produces: `AGENT_CLASS_BY_SLUG` gains keys `procurement-review`, `legal-review`, `security-review`, `finance-review`, `compliance-review`, `vendor-controller`. `WORKFLOW_TEMPLATES` gains `vendor-onboarding-review` with `agent_slugs = ["workflow-router", "rag-retriever", "procurement-review", "legal-review", "security-review", "finance-review", "compliance-review", "vendor-controller"]` and `required_artifacts = ["vendor_profile", "contract", "security_documentation", "pricing"]`.
- Consumes: `get_template` (already in templates.py), the agent classes from Tasks 2–3.

- [ ] **Step 1: Write the failing test**

Append to `apps/api/tests/test_vendor_workflow.py`:

```python
def test_vendor_agents_registered():
    from agents.registry import AGENT_CLASS_BY_SLUG

    for slug in (
        "procurement-review",
        "legal-review",
        "security-review",
        "finance-review",
        "compliance-review",
        "vendor-controller",
    ):
        assert slug in AGENT_CLASS_BY_SLUG


def test_vendor_template_registered():
    from workflows.templates import get_template

    template = get_template("vendor-onboarding-review")
    assert template.agent_slugs[0] == "workflow-router"
    assert "vendor-controller" in template.agent_slugs
    assert "contract" in template.required_artifacts
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd apps/api && python -m pytest tests/test_vendor_workflow.py -k registered -v`
Expected: FAIL — `AssertionError` (slugs not in registry / `ValueError: Unknown workflow template`).

- [ ] **Step 3: Register the agents**

In `apps/api/agents/registry.py`, add imports (keep alphabetical grouping with existing imports):

```python
from agents.vendor.compliance_agent import ComplianceAgent
from agents.vendor.finance_agent import FinanceAgent
from agents.vendor.legal_agent import LegalAgent
from agents.vendor.procurement_agent import ProcurementAgent
from agents.vendor.security_agent import SecurityAgent
from agents.vendor.vendor_controller import VendorControllerAgent
```

Append the six classes to the `AGENT_TYPES` tuple:

```python
AGENT_TYPES = (
    WorkflowRouterAgent,
    RAGRetrieverAgent,
    PolicyGuardianAgent,
    FinalDecisionAgent,
    ResumeJDMatcherAgent,
    BiasReviewerAgent,
    InterviewPlannerAgent,
    LeadQualifierAgent,
    EngineeringReviewerAgent,
    ProcurementAgent,
    LegalAgent,
    SecurityAgent,
    FinanceAgent,
    ComplianceAgent,
    VendorControllerAgent,
)
```

- [ ] **Step 4: Add the template**

In `apps/api/workflows/templates.py`, add inside `WORKFLOW_TEMPLATES`:

```python
    "vendor-onboarding-review": WorkflowTemplateRead(
        slug="vendor-onboarding-review",
        name="Vendor Onboarding Review",
        depth="deep",
        agent_slugs=[
            "workflow-router",
            "rag-retriever",
            "procurement-review",
            "legal-review",
            "security-review",
            "finance-review",
            "compliance-review",
            "vendor-controller",
        ],
        required_artifacts=[
            "vendor_profile",
            "contract",
            "security_documentation",
            "pricing",
        ],
    ),
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd apps/api && python -m pytest tests/test_vendor_workflow.py -v`
Expected: PASS (registration tests + the Task 5 decision-packet test now that slugs resolve).

- [ ] **Step 6: Commit**

```bash
git add apps/api/agents/registry.py apps/api/workflows/templates.py apps/api/tests/test_vendor_workflow.py
git commit -m "feat(workflows): register vendor agents and add vendor-onboarding-review template"
```

---

## Task 7: Vendor targeted-context retrieval queries

**Files:**
- Modify: `apps/api/routes/workflows.py` (the `_TARGETED_CONTEXT_QUERIES` map + `_retrieve_workflow_context`)
- Test: `apps/api/tests/test_vendor_workflow.py` (append) — only if `_retrieve_workflow_context` is unit-testable in isolation; otherwise assert on the constant.

**Interfaces:**
- Produces: `_TARGETED_CONTEXT_QUERIES` gains vendor doc-type keys: `"contract"`, `"security_documentation"`, `"pricing"`, `"vendor_profile"`, each mapping to a short retrieval query string. `_retrieve_workflow_context` adds the matching targeted query when those artifact doc-types are present (mirroring the existing resume/jd behavior).
- Consumes: existing retrieval plumbing in `routes/workflows.py`.

- [ ] **Step 1: Read the current shape**

Run: `cd apps/api && python -m pytest tests/ -q` first to confirm green baseline, then open `apps/api/routes/workflows.py` lines 1–140 to see `_TARGETED_CONTEXT_QUERIES` and how `_retrieve_workflow_context` consults artifact types.

- [ ] **Step 2: Write the failing test**

Append to `apps/api/tests/test_vendor_workflow.py`:

```python
def test_vendor_targeted_context_queries_present():
    from routes.workflows import _TARGETED_CONTEXT_QUERIES

    for key in ("contract", "security_documentation", "pricing", "vendor_profile"):
        assert key in _TARGETED_CONTEXT_QUERIES
        assert _TARGETED_CONTEXT_QUERIES[key].strip()
```

- [ ] **Step 3: Run test to verify it fails**

Run: `cd apps/api && python -m pytest tests/test_vendor_workflow.py -k targeted -v`
Expected: FAIL — `KeyError` / `AssertionError` (keys absent).

- [ ] **Step 4: Add the vendor queries**

In `apps/api/routes/workflows.py`, extend `_TARGETED_CONTEXT_QUERIES` (keep the existing resume/jd entries untouched):

```python
_TARGETED_CONTEXT_QUERIES = {
    # ... existing resume / jd entries unchanged ...
    "contract": "contract terms liability indemnity termination IP ownership",
    "security_documentation": "data security certifications SOC 2 ISO 27001 data residency breach",
    "pricing": "pricing total cost payment terms recurring fees discounts",
    "vendor_profile": "vendor company profile business need services provided references",
}
```

Then, in `_retrieve_workflow_context`, where resume/jd artifact types trigger targeted queries, add an additive branch that appends the targeted query for any artifact doc-type present in `_TARGETED_CONTEXT_QUERIES` (do not remove the existing resume/jd special-casing). The smallest clean change: after the existing targeted-query block, iterate artifact doc-types and append `_TARGETED_CONTEXT_QUERIES[doc_type]` when present and not already queued. Match the existing code's de-duplication style.

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd apps/api && python -m pytest tests/test_vendor_workflow.py -k targeted -v`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add apps/api/routes/workflows.py apps/api/tests/test_vendor_workflow.py
git commit -m "feat(api): add vendor doc-type targeted context retrieval queries"
```

---

## Task 8: Seed vendor agents, template, and sample demo documents

**Files:**
- Modify: `supabase/seed.sql`

**Interfaces:**
- Produces: `public.agents` rows for the six vendor agents; a `public.workflow_templates` row for `vendor-onboarding-review`; sample vendor `public.documents` (and any chunk rows the existing seed pattern uses) for a demo vendor "Acme Analytics". All inserts use the existing on-conflict upsert pattern so re-running is idempotent.
- Consumes: existing seed structure/columns.

- [ ] **Step 1: Inspect the existing seed pattern**

Read `supabase/seed.sql` fully to copy the exact column lists and on-conflict clauses used for `agents`, `workflow_templates`, and any document/chunk seeds.

- [ ] **Step 2: Add vendor agent rows**

Append to the `public.agents` insert (matching its columns `slug,name,category,description,provider_preference` and on-conflict):

```sql
insert into public.agents (slug, name, category, description, provider_preference) values
  ('procurement-review', 'Procurement Agent', 'vendor', 'Reviews business need, pricing, and procurement policy fit.', 'aimlapi'),
  ('legal-review', 'Legal Agent', 'vendor', 'Reviews contract risks and terms.', 'aimlapi'),
  ('security-review', 'Security Agent', 'vendor', 'Reviews data/security risks and missing security documentation.', 'aimlapi'),
  ('finance-review', 'Finance Agent', 'vendor', 'Reviews budget and cost concerns.', 'aimlapi'),
  ('compliance-review', 'Compliance Agent', 'vendor', 'Reviews policy and regulatory fit.', 'aimlapi'),
  ('vendor-controller', 'Controller Agent', 'vendor', 'Synthesizes specialist findings into a final vendor recommendation.', 'aimlapi')
on conflict (slug) do update set
  name = excluded.name,
  category = excluded.category,
  description = excluded.description,
  provider_preference = excluded.provider_preference;
```

(Match the exact `provider_preference` values used by existing rows; if the existing rows use a different default, mirror it.)

- [ ] **Step 3: Add the template row**

Append to the `public.workflow_templates` insert (columns `slug,name,description,depth,agent_slugs,required_artifacts`, jsonb arrays):

```sql
insert into public.workflow_templates (slug, name, description, depth, agent_slugs, required_artifacts) values
  (
    'vendor-onboarding-review',
    'Vendor Onboarding Review',
    'Reviews a prospective vendor across procurement, legal, security, finance, and compliance, then produces a decision packet for human approval.',
    'deep',
    '["workflow-router","rag-retriever","procurement-review","legal-review","security-review","finance-review","compliance-review","vendor-controller"]'::jsonb,
    '["vendor_profile","contract","security_documentation","pricing"]'::jsonb
  )
on conflict (slug) do update set
  name = excluded.name,
  description = excluded.description,
  depth = excluded.depth,
  agent_slugs = excluded.agent_slugs,
  required_artifacts = excluded.required_artifacts;
```

- [ ] **Step 4: Add sample demo documents**

Following the existing document-seed pattern (same table/columns, fixed UUIDs, same org as other seeds), add 3–4 non-sensitive sample vendor documents for "Acme Analytics" — a vendor profile, a contract excerpt (net-60, mutual indemnity), a pricing sheet, and intentionally **omit** a security attestation so the Security Agent has a real "missing information" gap to surface in the demo. Keep all content fictional; **no secrets, no real company data**.

- [ ] **Step 5: Verify the SQL parses**

Run: `cd <repo root> && psql "$SUPABASE_DB_URL" -f supabase/seed.sql` if a local DB is available; otherwise at minimum lint with `python -c "import pathlib; pathlib.Path('supabase/seed.sql').read_text()"` and eyeball the diff. Expected: no syntax errors; idempotent on re-run.

- [ ] **Step 6: Commit**

```bash
git add supabase/seed.sql
git commit -m "chore(seed): seed vendor agents, vendor template, and sample demo documents"
```

---

## Task 9: Frontend — template option, types, decision-packet display

**Files:**
- Modify: `apps/web/components/workflow-create-form.tsx`
- Modify: `apps/web/lib/types.ts`
- Modify: `apps/web/components/report-review-panel.tsx`

**Interfaces:**
- Produces: a `vendor-onboarding-review` entry in the form `TEMPLATES` const (label "Vendor Onboarding Review", artifacts list). `DocumentType` extended with vendor doc types. A `DecisionPacket` TS type matching the Pydantic schema, surfaced via `WorkflowReport.report_payload.decision_packet?`. A read-only decision-packet section in the review panel rendered only when the packet is present.
- Consumes: existing form/types/panel structure.

- [ ] **Step 1: Add the template to the create form**

In `apps/web/components/workflow-create-form.tsx`, add to the `TEMPLATES` const:

```ts
  "vendor-onboarding-review": {
    label: "Vendor Onboarding Review",
    artifacts: ["Vendor profile", "Contract", "Security documentation", "Pricing"],
  },
```

(No other change needed — the form maps over `TEMPLATES` and `isTemplateSlug` derives from it.)

- [ ] **Step 2: Extend types**

In `apps/web/lib/types.ts`:

Extend `DocumentType`:

```ts
export type DocumentType =
  | "resume"
  | "jd"
  | "policy"
  | "crm"
  | "code"
  | "vendor_profile"
  | "contract"
  | "security_documentation"
  | "pricing"
  | "other";
```

Add the decision-packet types and reference from the report payload:

```ts
export interface DecisionPacketFinding {
  agent_name: string;
  finding_type: string;
  severity: string;
  title: string;
  content: string;
  evidence_chunk_ids: string[];
  confidence: number;
}

export interface DecisionPacket {
  recommendation: "approve" | "reject" | "conditional_approval" | "needs_review";
  executive_summary: string;
  evidence_chunk_ids: string[];
  agent_findings: DecisionPacketFinding[];
  risks: string[];
  missing_information: string[];
  disagreements: string[];
  next_actions: string[];
  human_approval_required: boolean;
  audit_trail: Record<string, unknown>;
}
```

Ensure the existing `WorkflowReport.report_payload` type includes an optional `decision_packet?: DecisionPacket;` member (it already has an index signature `[key: string]: unknown`, so add the explicit optional field alongside it for type-safe access).

- [ ] **Step 3: Render the packet in the review panel**

In `apps/web/components/report-review-panel.tsx`, read `report.report_payload?.decision_packet` and, when present, render a read-only section above (or below) the existing approve/reject controls showing: recommendation badge, executive summary, risks, missing information, disagreements, next actions, and a "Human approval required" indicator. Keep the existing generic approve/reject controls intact (HR continues to work because HR reports have no `decision_packet`). Use existing styling classes; no new dependencies.

- [ ] **Step 4: Typecheck + build**

Run: `cd apps/web && pnpm typecheck`
Expected: no errors.
Run: `cd apps/web && pnpm build`
Expected: successful build.

- [ ] **Step 5: Commit**

```bash
git add apps/web/components/workflow-create-form.tsx apps/web/lib/types.ts apps/web/components/report-review-panel.tsx
git commit -m "feat(web): add vendor template option and decision-packet display"
```

---

## Task 10: Full verification pass + docs

**Files:**
- Modify: relevant docs (e.g., `apps/api/AGENTS.md` or the project README workflow list) — only where contracts/limitations changed.

- [ ] **Step 1: Run the full API test suite**

Run: `cd apps/api && python -m pytest tests/ -v`
Expected: all PASS, including `test_final_decision.py` (HR untouched), `test_vendor_agents.py`, `test_decision_packet.py`, `test_vendor_workflow.py`.

- [ ] **Step 2: Run repo-level verification (if defined)**

Run: `pnpm test:api` (root) / `pnpm typecheck` / `pnpm build`
Expected: green. (Use whichever scripts exist in root `package.json`; do not invent new ones.)

- [ ] **Step 3: Manual demo smoke**

With the API and web running and the seed applied: create a workflow from the "Vendor Onboarding Review" template, run it (mock provider is fine), and confirm the report view shows a decision packet with `recommendation = needs_review` (mock) or a parsed value (real provider), risks including the missing-security-doc gap, and "Human approval required". Confirm the HR workflow still runs and shows its usual report with no decision-packet section.

- [ ] **Step 4: Update docs**

Update the workflow/template list in project docs to mention `vendor-onboarding-review`, note that the decision packet lives at `report_payload.decision_packet`, and state the current limitation: recommendation parsing relies on the controller's `RECOMMENDATION:` line and falls back to `needs_review` for mock/absent controllers. Document that the `DecisionPacket` + `build_decision_packet` are the reusable template for future enterprise workflows.

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "docs: document vendor onboarding workflow and reusable decision packet"
```

---

## Self-Review

**1. Spec coverage:**
- Six agents (Procurement, Legal, Security, Finance, Compliance, Controller) → Tasks 2–3. ✅
- Decision packet fields (recommendation / executive summary / evidence citations / agent findings / risks / missing information / disagreements / next actions / human approval required / audit trail) → `DecisionPacket` schema + builder, Task 4; surfaced Tasks 5 & 9. ✅
- Recommendation enum approve/reject/conditional approval/needs review → controller vocabulary (Task 3) + `_VALID_RECOMMENDATIONS` (Task 4). ✅
- Inspect repo / identify architecture / propose plan before editing → done (this document; no code edited). ✅
- Smallest clean changes, production-oriented → additive tasks, existing patterns reused. ✅
- Types/schemas added → Task 4 (Pydantic) + Task 9 (TS). ✅
- Mock/sample data → Task 8 seed. ✅
- Verification steps → each task + Task 10. ✅
- Do not remove HR workflow → controller gate is slug-based (`vendor-controller`), HR report path untouched; regression test in Tasks 5 & 10. ✅
- No new dependencies → only stdlib `re`/`datetime` + existing libs. ✅
- Reusable template → generic `DecisionPacket`/`build_decision_packet` keyed on finding_type/severity, not vendor slugs; `consumes_prior_findings` is generic. ✅

**2. Placeholder scan:** No "TBD"/"add error handling"/"similar to Task N" — full code shown for agents, builder, schemas, tests. Task 7 (`_retrieve_workflow_context` branch) and Task 8 (sample documents) and Task 9 Step 3 (panel JSX) describe edits against code whose exact current shape must be read at execution time; they specify exact keys/values and the de-dup/styling pattern to match rather than inventing line numbers. These are deliberate "match existing pattern" instructions, not placeholders.

**3. Type consistency:** `build_decision_packet(*, ordered_findings, controller_finding_type="final_decision", audit_trail)` is used identically in Task 5. `DecisionPacket` / `DecisionPacketFinding` field names match between Pydantic (Task 4) and TS (Task 9). Finding types (`procurement_review`, `legal_review`, `security_review`, `finance_review`, `compliance_review`, `final_decision`) are consistent across agents (Tasks 2–3), builder risk-collection (Task 4), and report-node gate (Task 5). Slugs consistent across registry, template, seed, and tests.

**Resolved during review:** The HR-isolation risk (HR's `final-decision` also emits `finding_type="final_decision"`) is handled by gating packet construction on the `vendor-controller` *slug*, not the finding type — see Task 5 Step 3.
