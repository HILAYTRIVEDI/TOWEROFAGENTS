"""Parity tests for the LangGraph StateGraph executor.

Asserts that the graph-backed executor produces the same observable outputs as
the previous sequential loop for the three scenarios that matter:

1. Every selected/registered agent is visited in template order.
2. ScaffoldAgent slugs land in skipped_slugs (not in agents_ran).
3. The report payload shape is unchanged for a mock run.
"""
import asyncio
from uuid import UUID, uuid4

from core.config import Settings
from workflows.executor import WorkflowExecutor
from workflows.graph import WorkflowState
from workflows.templates import get_template


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------


def _mock_settings() -> Settings:
    """Settings pinned to mock providers so tests are env-independent."""
    return Settings(
        llm_provider="mock",
        embedding_provider="mock",
        band_mode="mock",
        band_default_room_id=None,
        band_reviewer_handle=None,
    )


def _make_state(selected_agents: list[str], **overrides) -> WorkflowState:
    base: WorkflowState = {
        "workflow_id": str(uuid4()),
        "org_id": str(uuid4()),
        "user_request": "Assess candidate",
        "template_slug": "hr-candidate-screening",
        "band_room_id": None,
        "artifacts": [],
        "selected_agents": selected_agents,
        "retrieved_context": [],
        "agent_findings": [],
        "policy_verdict": None,
        "final_report": None,
        "status": "running",
    }
    base.update(overrides)  # type: ignore[typeddict-item]
    return base


def _run(state: WorkflowState) -> dict:
    """Run executor with mock settings so agents receive a mock provider."""
    return asyncio.run(WorkflowExecutor(settings=_mock_settings()).run(state))


# ---------------------------------------------------------------------------
# 1. Graph visits every selected agent in template order
# ---------------------------------------------------------------------------


def test_graph_visits_all_template_agents_in_order() -> None:
    """For hr-candidate-screening all seven agents run in declared template order."""
    template = get_template("hr-candidate-screening")
    state = _make_state(template.agent_slugs)
    result = _run(state)
    payload = result["payload"]

    assert payload["agents_ran"] == template.agent_slugs
    assert payload["agents_skipped"] == []
    assert payload["finding_count"] == len(template.agent_slugs)


def test_graph_visits_sales_template_agents_skipping_scaffold() -> None:
    """For sales-lead-qualification the scaffold agent is skipped."""
    template = get_template("sales-lead-qualification")
    # lead-qualifier is a ScaffoldAgent; rag-retriever and final-decision are real.
    state = _make_state(template.agent_slugs)
    result = _run(state)
    payload = result["payload"]

    assert "lead-qualifier" in payload["agents_skipped"]
    assert "lead-qualifier" not in payload["agents_ran"]
    # The remaining implemented agents did run.
    assert "rag-retriever" in payload["agents_ran"]
    assert "final-decision" in payload["agents_ran"]
    # Template order is preserved for implemented agents.
    assert payload["agents_ran"] == ["rag-retriever", "final-decision"]


# ---------------------------------------------------------------------------
# 2. ScaffoldAgent slugs land in skipped_slugs
# ---------------------------------------------------------------------------


def test_scaffold_agent_slug_lands_in_skipped_slugs() -> None:
    """engineering-reviewer is a ScaffoldAgent; it must appear in skipped_slugs."""
    state = _make_state(["engineering-reviewer", "policy-guardian", "final-decision"])
    result = _run(state)
    payload = result["payload"]

    assert "engineering-reviewer" in payload["agents_skipped"]
    assert "engineering-reviewer" not in payload["agents_ran"]
    # Implemented agents after the scaffold still run.
    assert "policy-guardian" in payload["agents_ran"]
    assert "final-decision" in payload["agents_ran"]


def test_unknown_slug_lands_in_skipped_slugs() -> None:
    """A slug with no registered class also lands in skipped_slugs."""
    state = _make_state(["workflow-router", "nonexistent-agent", "final-decision"])
    result = _run(state)
    payload = result["payload"]

    assert "nonexistent-agent" in payload["agents_skipped"]
    assert "workflow-router" in payload["agents_ran"]
    assert "final-decision" in payload["agents_ran"]


# ---------------------------------------------------------------------------
# 3. Report payload shape is unchanged for a mock run
# ---------------------------------------------------------------------------


def test_mock_run_payload_shape_matches_contract() -> None:
    """Required payload keys and types are preserved after the LangGraph refactor."""
    template = get_template("hr-candidate-screening")
    state = _make_state(template.agent_slugs)
    result = _run(state)

    payload = result["payload"]
    report = result["report"]
    ordered_findings = result["ordered_findings"]

    # Required payload keys.
    assert payload["execution_mode"] == "specialist_agents_v1"
    assert isinstance(payload["selected_agents"], list)
    assert isinstance(payload["agents_ran"], list)
    assert isinstance(payload["agents_skipped"], list)
    assert isinstance(payload["finding_count"], int)
    assert isinstance(payload["providers_used"], list)
    assert isinstance(payload["retrieved_context_count"], int)
    assert isinstance(payload["retrieved_chunk_ids"], list)
    assert isinstance(payload["any_mock"], bool)
    assert payload["any_mock"] is True  # No real LLM settings → mock run.

    # Report fields.
    assert report.recommendation == "human_review_required"
    assert report.requires_human_review is True
    assert isinstance(report.summary, str)
    assert len(report.summary) > 0
    assert isinstance(report.strengths, list)
    assert isinstance(report.gaps, list)
    assert isinstance(report.interview_questions, list)
    assert isinstance(report.evidence_chunk_ids, list)
    assert isinstance(report.id, UUID)
    assert isinstance(report.workflow_id, UUID)

    # ordered_findings is list of (slug, AgentFinding) pairs.
    assert isinstance(ordered_findings, list)
    assert len(ordered_findings) == payload["finding_count"]
    for slug, finding in ordered_findings:
        assert isinstance(slug, str)
        assert finding.content  # mock findings have placeholder content


def test_empty_agent_list_produces_valid_report() -> None:
    """Graph with no agents still produces a well-formed report."""
    state = _make_state([])
    result = _run(state)

    payload = result["payload"]
    assert payload["execution_mode"] == "specialist_agents_v1"
    assert payload["agents_ran"] == []
    assert payload["finding_count"] == 0
    assert result["ordered_findings"] == []
    # gaps should note that no agent produced a finding.
    assert any("No specialist agent" in g for g in result["report"].gaps)
