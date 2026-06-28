"""Generic decision-packet assembly, reusable across enterprise workflows."""

from __future__ import annotations

import re
from typing import Any

from models.schemas import AgentFinding, DecisionPacket, DecisionPacketFinding

_VALID_RECOMMENDATIONS = {"approve", "reject", "conditional_approval", "needs_review"}
_RECOMMENDATION_RE = re.compile(r"RECOMMENDATION:\s*([a-z_]+)", re.IGNORECASE)
_RISK_SEVERITIES = {"warning", "error"}
_SECTION_RE = r"{label}:\s*(.+?)(?:\n[A-Z][A-Z ]+:|\Z)"


def _parse_recommendation(content: str) -> str | None:
    match = _RECOMMENDATION_RE.search(content)
    if not match:
        return None
    value = match.group(1).strip().lower()
    return value if value in _VALID_RECOMMENDATIONS else None


def _parse_list_section(content: str, label: str) -> list[str]:
    match = re.search(
        _SECTION_RE.format(label=re.escape(label)),
        content,
        re.DOTALL | re.IGNORECASE,
    )
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
            controller = finding

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

    for _slug, finding in ordered_findings:
        if finding.finding_type == controller_finding_type:
            continue
        if finding.severity in _RISK_SEVERITIES and finding.title not in risks:
            risks.append(finding.title)

    evidence_ids: list[str] = []
    for _slug, finding in ordered_findings:
        for chunk_id in finding.evidence_chunk_ids:
            if chunk_id not in evidence_ids:
                evidence_ids.append(chunk_id)

    packet_findings = [
        DecisionPacketFinding(
            agent_name=finding.agent_name,
            finding_type=finding.finding_type,
            severity=finding.severity,
            title=finding.title,
            content=finding.content,
            evidence_chunk_ids=list(finding.evidence_chunk_ids),
            confidence=finding.confidence,
        )
        for _slug, finding in ordered_findings
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
