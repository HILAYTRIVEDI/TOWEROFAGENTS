import re
from typing import Any
from uuid import uuid4

from agents.registry import AGENT_CLASS_BY_SLUG
from core.config import Settings
from llm.router import LLMRouter
from models.schemas import AgentFinding, AgentInput, WorkflowReportRead
from workflows.graph import WorkflowState

# Slug of the synthesis agent that receives all prior findings.
_FINAL_DECISION_SLUG = "final-decision"
# Finding type produced by the interview planner; questions are extracted from its content.
_INTERVIEW_PLAN_TYPE = "interview_plan"
# Finding type produced by policy guardian; policy note comes from its content.
_POLICY_CHECK_TYPE = "policy_check"


def _extract_questions(content: str) -> list[str]:
    """Extract numbered questions from interview-planner content (best-effort)."""
    # Match lines like "1. ..." or "1) ..."
    lines = content.splitlines()
    questions: list[str] = []
    for line in lines:
        stripped = line.strip()
        if re.match(r"^\d+[.)]\s+", stripped):
            q = re.sub(r"^\d+[.)]\s+", "", stripped).strip()
            if q:
                questions.append(q)
    # Fall back to non-placeholder sentences if no numbered list found
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
    # Drop markdown emphasis and inline-code markers.
    text = re.sub(r"[*_`#>]+", "", text)
    # Strip leading list markers (-, *, +, "1.", "1)") at the start of any line.
    text = re.sub(r"(?m)^\s*(?:[-*+]|\d+[.)])\s+", "", text)
    # Collapse all runs of whitespace (including newlines) into single spaces.
    text = re.sub(r"\s+", " ", text).strip()
    # Strip residual inline list markers left over once newlines collapsed,
    # e.g. "...context. 2. Uncertain..." or "...acknowledged - Skills...".
    text = re.sub(r"\s+\d+[.)]\s+", " ", text)
    text = re.sub(r"\s+[-*+]\s+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()

    if len(text) <= max_chars:
        return text
    # Truncate, then back up to the last sentence end within the limit.
    head = text[:max_chars]
    cut = max(head.rfind(". "), head.rfind("! "), head.rfind("? "))
    if cut > max_chars // 2:
        return head[: cut + 1].strip()
    return head.rstrip() + "…"


class WorkflowExecutor:
    def __init__(self, settings: Settings | None = None) -> None:
        # settings is optional so existing call-sites that omit it still work
        # during the transition period; the executor falls back to the mock
        # provider when settings are absent.
        self._settings = settings

    async def run(self, state: WorkflowState) -> dict[str, Any]:
        router = LLMRouter(self._settings) if self._settings else None

        findings: list[AgentFinding] = []
        ran_slugs: list[str] = []
        skipped_slugs: list[str] = []
        providers_used: list[str] = []

        for slug in state["selected_agents"]:
            agent_cls = AGENT_CLASS_BY_SLUG.get(slug)
            if agent_cls is None:
                skipped_slugs.append(slug)
                continue

            # Build provider for this agent's task (task name = slug for routing)
            provider = router.for_task(slug) if router else None
            agent = agent_cls(chat_provider=provider)

            # final-decision receives the accumulated prior findings so it can synthesize.
            prior_findings: list[dict] = []
            if slug == _FINAL_DECISION_SLUG:
                prior_findings = [f.model_dump() for f in findings]

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
                findings.append(finding)
                ran_slugs.append(slug)
                providers_used.append(
                    getattr(provider, "_provider_name", None)
                    or (finding.confidence == 0.0 and "mock")
                    or "unknown"
                )
            except NotImplementedError:
                # Scaffold agents are not yet implemented — record the gap, don't crash.
                skipped_slugs.append(slug)

        # Detect whether any mock provider was used (confidence==0.0 and title prefix)
        any_mock = any(f.confidence == 0.0 for f in findings) or (router is None)

        # Aggregate evidence IDs (deduplicated, preserving order)
        seen: set[str] = set()
        evidence_ids: list[str] = []
        for f in findings:
            for eid in f.evidence_chunk_ids:
                if eid not in seen:
                    seen.add(eid)
                    evidence_ids.append(eid)

        # Extract specialist outputs for the report fields
        interview_questions: list[str] = []
        policy_note: str | None = None
        final_finding: AgentFinding | None = None

        for f in findings:
            if f.finding_type == _INTERVIEW_PLAN_TYPE and "[PLACEHOLDER" not in f.content:
                interview_questions = _extract_questions(f.content)
            if f.finding_type == _POLICY_CHECK_TYPE and "[PLACEHOLDER" not in f.content:
                # Flatten to a clean, scannable plain-text note for the report card.
                policy_note = _clean_note(f.content)
            if f.finding_type == "final_decision":
                final_finding = f

        # Derive strengths/gaps from findings content (one bullet per finding)
        strengths: list[str] = [f.title for f in findings if f.severity == "info"]
        gaps: list[str] = [f.title for f in findings if f.severity in ("warning", "error")]

        # Agents not yet implemented
        if skipped_slugs:
            gaps.append(
                f"The following agents have not executed yet: {', '.join(skipped_slugs)}."
            )
        if not findings:
            gaps.append("No specialist agent produced a finding for this run.")

        # Determine recommendation: use final-decision output when real, else conservative
        recommendation = "human_review_required"
        fit_score: float | None = None

        if final_finding and not any_mock:
            # Extract recommendation from final-decision content (best-effort keyword scan)
            lower = final_finding.content.lower()
            if "advance" in lower:
                recommendation = "advance"
            elif "decline" in lower:
                recommendation = "decline"
            # fit_score: only emit when a real provider was used and final-decision is real.
            # We do NOT fabricate a score; the LLM output does not produce a float score,
            # so fit_score remains None unless a future agent is explicitly designed to emit one.
            fit_score = None

        # Build summary
        summary_parts = [
            f"Specialist agent run: {len(ran_slugs)} agent(s) produced "
            f"{len(findings)} finding(s); {len(skipped_slugs)} agent(s) skipped "
            f"(not yet implemented)."
        ]
        if any_mock:
            summary_parts.append(
                "The LLM provider is set to 'mock' — no external model was called. "
                "All findings are placeholders and require human review before use."
            )
        if final_finding and not any_mock:
            summary_parts.append(final_finding.content[:300])
        elif not final_finding:
            summary_parts.append(
                "The final-decision agent did not produce a finding; "
                "recommendation is 'human_review_required'."
            )

        # MVP: requires_human_review is ALWAYS True. This is an explicit product decision:
        # every AI-assisted hiring recommendation must be reviewed by a human before action.
        # Remove this override only when a formal human-in-the-loop approval step is wired in.
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

        return {
            "report": report,
            "ordered_findings": list(zip(ran_slugs, findings, strict=True)),
            "payload": {
                "execution_mode": "specialist_agents_v1",
                "selected_agents": state["selected_agents"],
                "agents_ran": ran_slugs,
                "agents_skipped": skipped_slugs,
                "finding_count": len(findings),
                "providers_used": providers_used,
                "retrieved_context_count": len(state["retrieved_context"]),
                "retrieved_chunk_ids": [
                    str(c["id"]) for c in state["retrieved_context"] if c.get("id")
                ],
                "any_mock": any_mock,
            },
        }
