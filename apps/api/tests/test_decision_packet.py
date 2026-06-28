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
    packet = build_decision_packet(
        ordered_findings=ordered,
        audit_trail={"workflow_id": "w1"},
    )
    assert packet.recommendation == "conditional_approval"
    assert packet.human_approval_required is True
    assert packet.audit_trail["workflow_id"] == "w1"


def test_executive_summary_uses_controller_body():
    ordered = [
        ("vendor-controller", _controller("RECOMMENDATION: approve\nSUMMARY: green light"))
    ]
    packet = build_decision_packet(ordered_findings=ordered, audit_trail={})
    assert (
        "green light" in packet.executive_summary
        or "approve" in packet.executive_summary.lower()
    )


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
            _controller("[PLACEHOLDER ...] RECOMMENDATION: approve", confidence=0.0),
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
    assert [f.agent_name for f in packet.agent_findings] == [
        "Procurement Agent",
        "Controller Agent",
    ]
