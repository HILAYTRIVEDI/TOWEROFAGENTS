"""Per-agent and aggregation node factories for the LangGraph workflow graph.

Each factory returns an async function compatible with LangGraph StateGraph nodes.
The nodes communicate via WorkflowState accumulator fields (ran_slugs, skipped_slugs,
agent_findings, providers_used) and the terminal aggregate_report node writes
report_result to close the graph.
"""
from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any
from uuid import uuid4

from agents.registry import AGENT_CLASS_BY_SLUG
from models.schemas import AgentFinding, AgentInput, WorkflowReportRead

if TYPE_CHECKING:
    from workflows.graph import WorkflowState

# ---------------------------------------------------------------------------
# Constants (shared with executor.py)
# ---------------------------------------------------------------------------

_FINAL_DECISION_SLUG = "final-decision"
_INTERVIEW_PLAN_TYPE = "interview_plan"
_POLICY_CHECK_TYPE = "policy_check"


# ---------------------------------------------------------------------------
# Helper functions (factored out of executor.py)
# ---------------------------------------------------------------------------


def _extract_questions(content: str) -> list[str]:
    """Extract numbered questions from interview-planner content (best-effort)."""
    lines = content.splitlines()
    questions: list[str] = []
    for line in lines:
        stripped = line.strip()
        if re.match(r"^\d+[.)]\s+", stripped):
            q = re.sub(r"^\d+[.)]\s+", "", stripped).strip()
            if q:
                questions.append(q)
    if not questions and "[PLACEHOLDER" not in content:
        questions = [s.strip() for s in content.split("?") if len(s.strip()) > 10]
        questions = [q + "?" for q in questions if q]
    return questions


def _clean_note(content: str, max_chars: int = 500) -> str:
    """Flatten an LLM note into a single scannable plain-text paragraph.

    Strips markdown artifacts (headings, bold, bullets, list markers) and
    collapses whitespace so report cards never show a wall of structured text.
    Truncates at a sentence boundary when possible so output never cuts
    mid-sentence.
    """
    text = content.strip()
    text = re.sub(r"[*_`#>]+", "", text)
    text = re.sub(r"(?m)^\s*(?:[-*+]|\d+[.)])\s+", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(r"\s+\d+[.)]\s+", " ", text)
    text = re.sub(r"\s+[-*+]\s+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()

    if len(text) <= max_chars:
        return text
    head = text[:max_chars]
    cut = max(head.rfind(". "), head.rfind("! "), head.rfind("? "))
    if cut > max_chars // 2:
        return head[: cut + 1].strip()
    return head.rstrip() + "…"


# ---------------------------------------------------------------------------
# Node factories
# ---------------------------------------------------------------------------


def make_agent_node(slug: str, router: Any = None):
    """Return an async LangGraph node that runs one agent identified by *slug*.

    On success the node returns accumulator updates for agent_findings,
    ran_slugs, and providers_used.  On NotImplementedError (ScaffoldAgent) it
    appends to skipped_slugs without crashing.
    """

    async def node(state: WorkflowState) -> dict[str, Any]:
        agent_cls = AGENT_CLASS_BY_SLUG.get(slug)
        if agent_cls is None:
            return {"skipped_slugs": [slug]}

        provider = router.for_task(slug) if router else None
        agent = agent_cls(chat_provider=provider)

        # final-decision receives all prior findings so it can synthesise.
        prior_findings: list[dict] = []
        if slug == _FINAL_DECISION_SLUG:
            prior_findings = list(state["agent_findings"])

        agent_input = AgentInput(
            workflow_id=state["workflow_id"],
            org_id=state["org_id"],
            task=state["user_request"] or state.get("template_slug") or slug,
            context_chunks=state["retrieved_context"],
            artifacts=state["artifacts"],
            band_room_id=state["band_room_id"],
            prior_findings=prior_findings,
        )

        try:
            finding = await agent.run(agent_input)
            provider_name = (
                getattr(provider, "_provider_name", None)
                or (finding.confidence == 0.0 and "mock")
                or "unknown"
            )
            return {
                "agent_findings": [finding.model_dump(mode="json")],
                "ran_slugs": [slug],
                "providers_used": [provider_name],
            }
        except NotImplementedError:
            # Scaffold agents are not yet implemented — record the gap, don't crash.
            return {"skipped_slugs": [slug]}

    # Give the node a descriptive name for LangGraph tracing.
    node.__name__ = f"agent_{slug.replace('-', '_')}"
    return node


def make_report_node():
    """Return the async terminal aggregation node that builds WorkflowReportRead.

    Reads accumulated state fields and writes *report_result* (a JSON-safe dict)
    so the executor can reconstruct the typed Pydantic object after graph completion.
    """

    async def node(state: WorkflowState) -> dict[str, Any]:
        findings = [AgentFinding.model_validate(d) for d in state["agent_findings"]]
        ran_slugs: list[str] = list(state.get("ran_slugs", []))
        skipped_slugs: list[str] = list(state.get("skipped_slugs", []))

        any_mock = state.get("use_mock", True) or any(f.confidence == 0.0 for f in findings)

        # Aggregate evidence IDs (deduplicated, preserving order).
        seen: set[str] = set()
        evidence_ids: list[str] = []
        for f in findings:
            for eid in f.evidence_chunk_ids:
                if eid not in seen:
                    seen.add(eid)
                    evidence_ids.append(eid)

        interview_questions: list[str] = []
        policy_note: str | None = None
        final_finding: AgentFinding | None = None

        for f in findings:
            if f.finding_type == _INTERVIEW_PLAN_TYPE and "[PLACEHOLDER" not in f.content:
                interview_questions = _extract_questions(f.content)
            if f.finding_type == _POLICY_CHECK_TYPE and "[PLACEHOLDER" not in f.content:
                policy_note = _clean_note(f.content)
            if f.finding_type == "final_decision":
                final_finding = f

        strengths: list[str] = [f.title for f in findings if f.severity == "info"]
        gaps: list[str] = [f.title for f in findings if f.severity in ("warning", "error")]

        if skipped_slugs:
            gaps.append(
                f"The following agents have not executed yet: {', '.join(skipped_slugs)}."
            )
        if not findings:
            gaps.append("No specialist agent produced a finding for this run.")

        recommendation = "human_review_required"
        fit_score: float | None = None

        if final_finding and not any_mock:
            lower = final_finding.content.lower()
            if "advance" in lower:
                recommendation = "advance"
            elif "decline" in lower:
                recommendation = "decline"
            fit_score = None

        run_summary = (
            f"Specialist agent run: {len(ran_slugs)} agent(s) produced "
            f"{len(findings)} finding(s)."
        )
        if skipped_slugs:
            run_summary += (
                f" {len(skipped_slugs)} agent(s) skipped because they are not yet "
                f"implemented: {', '.join(skipped_slugs)}."
            )
        summary_parts = [run_summary]
        if any_mock:
            summary_parts.append(
                "The LLM provider is set to 'mock' — no external model was called. "
                "All findings are placeholders and require human review before use."
            )
        if final_finding and not any_mock:
            summary_parts.append(final_finding.content.strip())
        elif not final_finding:
            summary_parts.append(
                "The final-decision agent did not produce a finding; "
                "recommendation is 'human_review_required'."
            )

        # MVP: requires_human_review is ALWAYS True.
        requires_human_review = True

        if policy_note is None:
            policy_note = "Human review is required before any high-impact decision."

        report = WorkflowReportRead(
            id=uuid4(),
            workflow_id=state["workflow_id"],
            recommendation=recommendation,
            summary=" ".join(summary_parts),
            fit_score=fit_score,
            strengths=strengths,
            gaps=gaps,
            interview_questions=interview_questions,
            policy_note=policy_note,
            evidence_chunk_ids=evidence_ids,
            requires_human_review=requires_human_review,
        )

        return {"report_result": report.model_dump(mode="json")}

    node.__name__ = "aggregate_report"
    return node
