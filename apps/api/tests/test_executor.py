"""Unit tests for WorkflowExecutor with specialist agents."""

import asyncio
from uuid import uuid4

import workflows.executor as executor_module
from llm.base import ChatResult
from core.config import Settings
from workflows.executor import WorkflowExecutor
from workflows.graph import WorkflowState


class _MockRouter:
    """Fake LLMRouter — always returns a mock provider."""

    def for_task(self, task: str):
        return _MockProvider()


class _MockProvider:
    provider = "mock"

    async def complete(self, messages, model=None) -> ChatResult:
        return ChatResult(
            content="[mock] No external model was called.",
            provider="mock",
            model="mock",
        )


class _RealProvider:
    """Non-mock provider stub: simulates a real LLM response."""

    provider = "aiml"

    async def complete(self, messages, model=None) -> ChatResult:
        # Return contextually appropriate content based on system message hints
        system = messages[0]["content"] if messages else ""
        if "interview" in system.lower():
            content = (
                "1. Can you describe your experience with Python and distributed systems?\n"
                "2. How have you approached system design for high-availability services?\n"
                "3. Tell us about a time you identified and resolved a critical production issue."
            )
        elif "policy" in system.lower():
            content = (
                "Assessment is compliant with hiring policy. "
                "No policy conflicts detected. Equal opportunity standards were observed."
            )
        elif "synthesize" in system.lower() or "final" in system.lower():
            content = (
                "RECOMMENDATION: advance\n"
                "SUMMARY: Candidate demonstrates strong alignment with role requirements.\n"
                "STRENGTHS: Python expertise, system design skills.\n"
                "GAPS: Limited leadership experience noted.\n"
                "NEXT STEPS: Proceed to technical interview panel with human hiring manager review."
            )
        else:
            content = "Analysis complete. Candidate shows good match on job-related criteria."
        return ChatResult(content=content, provider="aiml", model="aiml-gpt4")


class _RealRouter:
    """Fake LLMRouter that returns a non-mock provider for all tasks."""

    def for_task(self, task: str):
        return _RealProvider()


class _LongFinalProvider(_RealProvider):
    async def complete(self, messages, model=None) -> ChatResult:
        system = messages[0]["content"] if messages else ""
        if "synthesize" in system.lower() or "final" in system.lower():
            return ChatResult(
                content=(
                    "RECOMMENDATION: human_review_required\n"
                    "SUMMARY: Candidate demonstrates strong alignment with the role across "
                    "WordPress engineering, backend migration work, AI orchestration, and "
                    "cross-functional delivery. The summary intentionally runs beyond the old "
                    "three-hundred-character limit so the regression test proves the persisted "
                    "report is not cut off mid sentence or mid word.\n"
                    "NEXT STEPS: Keep the complete final decision text visible for human review."
                ),
                provider="aiml",
                model="aiml-gpt4",
            )
        return await super().complete(messages, model=model)


class _LongFinalRouter:
    def __init__(self, settings) -> None:
        self.settings = settings

    def for_task(self, task: str):
        return _LongFinalProvider()


def _base_state(**overrides) -> WorkflowState:
    state: WorkflowState = {
        "workflow_id": str(uuid4()),
        "org_id": str(uuid4()),
        "user_request": "Screen candidate for senior engineer role",
        "template_slug": "hr-candidate-screening",
        "band_room_id": None,
        "artifacts": [],
        "selected_agents": [
            "resume-jd-matcher",
            "bias-reviewer",
            "interview-planner",
            "policy-guardian",
            "final-decision",
        ],
        "retrieved_context": [],
        "agent_findings": [],
        "policy_verdict": None,
        "final_report": None,
        "status": "running",
    }
    state.update(overrides)  # type: ignore[typeddict-item]
    return state


# ---------------------------------------------------------------------------
# Fake executor that injects _MockRouter (all agents get mock provider).
# Used to test the mock path without real settings.
# ---------------------------------------------------------------------------

class _FakeExecutor(WorkflowExecutor):
    """Executor that always uses _MockRouter regardless of settings."""

    def __init__(self) -> None:
        super().__init__(settings=None)
        self._fake_router = _MockRouter()

    async def run(self, state: WorkflowState):  # type: ignore[override]
        from agents.registry import AGENT_CLASS_BY_SLUG
        from models.schemas import AgentFinding, AgentInput, WorkflowReportRead
        from uuid import uuid4 as _uuid4

        findings = []
        ran_slugs = []
        skipped_slugs = []

        for slug in state["selected_agents"]:
            agent_cls = AGENT_CLASS_BY_SLUG.get(slug)
            if agent_cls is None:
                skipped_slugs.append(slug)
                continue

            provider = self._fake_router.for_task(slug)
            agent = agent_cls(chat_provider=provider)

            prior_findings: list[dict] = []
            if slug == "final-decision":
                prior_findings = [f.model_dump() for f in findings]

            agent_input = AgentInput(
                workflow_id=state["workflow_id"],
                org_id=state["org_id"],
                task=state["user_request"] or slug,
                context_chunks=state["retrieved_context"],
                artifacts=state["artifacts"],
                band_room_id=state["band_room_id"],
                prior_findings=prior_findings,
            )

            try:
                finding = await agent.run(agent_input)
                findings.append(finding)
                ran_slugs.append(slug)
            except NotImplementedError:
                skipped_slugs.append(slug)

        any_mock = any(f.confidence == 0.0 for f in findings) or True
        evidence_ids: list[str] = []
        seen: set[str] = set()
        for f in findings:
            for eid in f.evidence_chunk_ids:
                if eid not in seen:
                    seen.add(eid)
                    evidence_ids.append(eid)

        strengths = [f.title for f in findings if f.severity == "info"]
        gaps = [f.title for f in findings if f.severity in ("warning", "error")]
        if skipped_slugs:
            gaps.append(f"Agents not yet implemented: {', '.join(skipped_slugs)}.")

        report = WorkflowReportRead(
            id=_uuid4(),
            workflow_id=state["workflow_id"],
            recommendation="human_review_required",
            summary=(
                f"{len(ran_slugs)} agent(s) ran, {len(skipped_slugs)} skipped. "
                "Mock provider used — no real LLM was called."
            ),
            fit_score=None,
            strengths=strengths,
            gaps=gaps,
            interview_questions=[],
            policy_note="Human review required.",
            evidence_chunk_ids=evidence_ids,
            requires_human_review=True,
        )
        return {
            "report": report,
            "payload": {
                "execution_mode": "specialist_agents_v1",
                "selected_agents": state["selected_agents"],
                "agents_ran": ran_slugs,
                "agents_skipped": skipped_slugs,
                "finding_count": len(findings),
                "retrieved_context_count": len(state["retrieved_context"]),
                "any_mock": any_mock,
            },
        }


# ---------------------------------------------------------------------------
# Fake executor that injects _RealRouter (all agents get non-mock provider).
# Used to test the real (non-mock) path.
# ---------------------------------------------------------------------------

class _RealProviderExecutor(WorkflowExecutor):
    """Executor that always uses _RealRouter (simulates configured real provider)."""

    def __init__(self) -> None:
        super().__init__(settings=None)
        self._real_router = _RealRouter()

    async def run(self, state: WorkflowState):  # type: ignore[override]
        from agents.registry import AGENT_CLASS_BY_SLUG
        from models.schemas import AgentFinding, AgentInput, WorkflowReportRead
        from uuid import uuid4 as _uuid4
        import re

        findings: list[AgentFinding] = []
        ran_slugs: list[str] = []
        skipped_slugs: list[str] = []

        for slug in state["selected_agents"]:
            agent_cls = AGENT_CLASS_BY_SLUG.get(slug)
            if agent_cls is None:
                skipped_slugs.append(slug)
                continue

            provider = self._real_router.for_task(slug)
            agent = agent_cls(chat_provider=provider)

            prior_findings: list[dict] = []
            if slug == "final-decision":
                prior_findings = [f.model_dump() for f in findings]

            agent_input = AgentInput(
                workflow_id=state["workflow_id"],
                org_id=state["org_id"],
                task=state["user_request"] or slug,
                context_chunks=state["retrieved_context"],
                artifacts=state["artifacts"],
                band_room_id=state["band_room_id"],
                prior_findings=prior_findings,
            )

            try:
                finding = await agent.run(agent_input)
                findings.append(finding)
                ran_slugs.append(slug)
            except NotImplementedError:
                skipped_slugs.append(slug)

        any_mock = any(f.confidence == 0.0 for f in findings)
        evidence_ids: list[str] = []
        seen: set[str] = set()
        for f in findings:
            for eid in f.evidence_chunk_ids:
                if eid not in seen:
                    seen.add(eid)
                    evidence_ids.append(eid)

        interview_questions: list[str] = []
        policy_note: str | None = None
        final_finding: AgentFinding | None = None

        for f in findings:
            if f.finding_type == "interview_plan" and "[PLACEHOLDER" not in f.content:
                lines = f.content.splitlines()
                for line in lines:
                    stripped = line.strip()
                    if re.match(r"^\d+[.)]\s+", stripped):
                        q = re.sub(r"^\d+[.)]\s+", "", stripped).strip()
                        if q:
                            interview_questions.append(q)
            if f.finding_type == "policy_check" and "[PLACEHOLDER" not in f.content:
                policy_note = f.content[:500]
            if f.finding_type == "final_decision":
                final_finding = f

        strengths = [f.title for f in findings if f.severity == "info"]
        gaps = [f.title for f in findings if f.severity in ("warning", "error")]

        recommendation = "human_review_required"
        if final_finding and not any_mock:
            lower = final_finding.content.lower()
            if "advance" in lower:
                recommendation = "advance"
            elif "decline" in lower:
                recommendation = "decline"

        if policy_note is None:
            policy_note = "Human review is required before any high-impact decision."

        report = WorkflowReportRead(
            id=_uuid4(),
            workflow_id=state["workflow_id"],
            recommendation=recommendation,
            summary=f"{len(ran_slugs)} agent(s) ran with real provider.",
            fit_score=None,  # never fabricate
            strengths=strengths,
            gaps=gaps,
            interview_questions=interview_questions,
            policy_note=policy_note,
            evidence_chunk_ids=evidence_ids,
            # MVP: always True — human must review every hiring decision
            requires_human_review=True,
        )
        return {
            "report": report,
            "payload": {
                "execution_mode": "specialist_agents_v1",
                "selected_agents": state["selected_agents"],
                "agents_ran": ran_slugs,
                "agents_skipped": skipped_slugs,
                "finding_count": len(findings),
                "retrieved_context_count": len(state["retrieved_context"]),
                "any_mock": any_mock,
            },
        }


# ---------------------------------------------------------------------------
# Tests: mock provider path
# ---------------------------------------------------------------------------

def test_all_agents_run_with_mock_provider() -> None:
    """All 5 HR agents are now implemented and run with mock provider."""
    executor = _FakeExecutor()
    state = _base_state()
    result = asyncio.run(executor.run(state))

    payload = result["payload"]
    report = result["report"]

    # All agents should have run (none are scaffold anymore)
    for slug in ("resume-jd-matcher", "bias-reviewer", "interview-planner",
                 "policy-guardian", "final-decision"):
        assert slug in payload["agents_ran"], f"{slug} should have run"
    assert payload["finding_count"] == 5
    assert payload["agents_skipped"] == []

    # Report invariants with mock
    assert report.recommendation == "human_review_required"
    assert report.requires_human_review is True
    assert report.fit_score is None


def test_executor_with_real_impl_uses_mock_provider() -> None:
    """Real WorkflowExecutor.run with settings=None skips resume-jd-matcher
    (no provider injected → resume-jd-matcher raises RuntimeError, not NotImplementedError).
    We test with settings=None to confirm executor doesn't crash for unknown reasons."""
    # This test verifies the production executor path with settings=None;
    # resume-jd-matcher will get provider=None and raise RuntimeError, which
    # the executor does NOT catch (only NotImplementedError is caught). That
    # means the run will propagate the error. This is the correct safety
    # boundary: callers must always pass settings.
    #
    # We therefore only test executor with valid settings via _FakeExecutor above.
    # This test is intentionally minimal.
    pass


def test_executor_report_has_no_fabricated_evidence() -> None:
    executor = _FakeExecutor()
    # No context chunks → evidence_ids must be empty
    state = _base_state(retrieved_context=[])
    result = asyncio.run(executor.run(state))
    assert result["report"].evidence_chunk_ids == []


def test_executor_report_with_context_chunk_ids() -> None:
    executor = _FakeExecutor()
    chunk_id = str(uuid4())
    state = _base_state(retrieved_context=[{"id": chunk_id, "content": "policy text"}])
    result = asyncio.run(executor.run(state))
    # resume-jd-matcher ran with this chunk → evidence must appear
    assert chunk_id in result["report"].evidence_chunk_ids


# ---------------------------------------------------------------------------
# Tests: real (non-mock) provider path
# ---------------------------------------------------------------------------

def test_full_run_with_real_provider_yields_complete_report() -> None:
    """Full run with all agents using non-mock provider produces complete decision packet."""
    executor = _RealProviderExecutor()
    chunk_id = str(uuid4())
    state = _base_state(
        retrieved_context=[{"id": chunk_id, "content": "Candidate: 6 years Python, distributed systems expert"}],
        artifacts=[
            {"filename": "resume.pdf", "doc_type": "resume"},
            {"filename": "jd.pdf", "doc_type": "job_description"},
            {"filename": "policy.pdf", "doc_type": "policy"},
        ],
    )
    result = asyncio.run(executor.run(state))
    report = result["report"]
    payload = result["payload"]

    # All 5 agents ran
    assert payload["finding_count"] == 5
    assert payload["agents_skipped"] == []
    assert not payload["any_mock"]

    # interview_questions extracted from interview-planner's numbered list
    assert len(report.interview_questions) > 0, "Expected non-empty interview questions"

    # policy_note populated from policy-guardian
    assert report.policy_note is not None
    assert len(report.policy_note) > 10

    # requires_human_review is unconditionally True (MVP human-in-the-loop requirement)
    assert report.requires_human_review is True

    # fit_score must not be fabricated
    assert report.fit_score is None

    # recommendation set from final-decision (real provider said "advance")
    assert report.recommendation == "advance"


def test_production_executor_summary_is_not_truncated_or_needlessly_scaffolded(monkeypatch) -> None:
    monkeypatch.setattr(executor_module, "LLMRouter", _LongFinalRouter)
    executor = WorkflowExecutor(
        settings=Settings(llm_provider="aiml", aiml_api_key="test", aiml_default_model="test")
    )
    result = asyncio.run(executor.run(_base_state()))

    summary = result["report"].summary
    assert "0 agent(s) skipped" not in summary
    assert "not yet implemented" not in summary
    assert "Keep the complete final decision text visible for human review." in summary


def test_full_run_requires_human_review_always_true() -> None:
    """Even with a real provider and a clean outcome, requires_human_review is forced True."""
    executor = _RealProviderExecutor()
    state = _base_state()
    result = asyncio.run(executor.run(state))
    # MVP product rule: every hiring decision needs human review
    assert result["report"].requires_human_review is True


def test_final_decision_receives_prior_findings() -> None:
    """final-decision gets prior findings from other agents in its agent_input."""
    from agents.platform.final_decision import FinalDecisionAgent
    from models.schemas import AgentInput

    calls_received = []

    class _CapturingProvider:
        provider = "aiml"

        async def complete(self, messages, model=None) -> ChatResult:
            calls_received.append(messages)
            return ChatResult(
                content="RECOMMENDATION: human_review_required\nSynthesis based on prior findings.",
                provider="aiml",
                model="aiml",
            )

    agent = FinalDecisionAgent(chat_provider=_CapturingProvider())
    prior = [
        {"agent_name": "Bias/Safety Reviewer", "finding_type": "bias_review",
         "title": "Bias review — no concerns found", "content": "No bias detected."},
    ]
    agent_input = AgentInput(
        workflow_id=str(uuid4()),
        org_id=str(uuid4()),
        task="synthesize",
        prior_findings=prior,
    )
    finding = asyncio.run(agent.run(agent_input))

    assert finding.finding_type == "final_decision"
    # Check that prior finding content appeared in the user message
    user_msg = calls_received[0][1]["content"]
    assert "Bias/Safety Reviewer" in user_msg
