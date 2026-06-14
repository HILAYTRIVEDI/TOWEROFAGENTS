from typing import Any, TypedDict


class WorkflowState(TypedDict):
    workflow_id: str
    org_id: str
    user_request: str
    template_slug: str | None
    band_room_id: str | None
    artifacts: list[dict[str, Any]]
    selected_agents: list[str]
    retrieved_context: list[dict[str, Any]]
    agent_findings: list[dict[str, Any]]
    policy_verdict: dict[str, Any] | None
    final_report: str | None
    status: str


PLANNED_NODE_ORDER = (
    "intake",
    "select_template",
    "create_band_room",
    "retrieve_context",
    "spawn_agents",
    "specialist_agent_execution",
    "policy_guardian",
    "final_decision",
    "save_report",
)


def build_workflow_graph() -> Any:
    raise NotImplementedError("LangGraph execution is not implemented in the bootstrap")

