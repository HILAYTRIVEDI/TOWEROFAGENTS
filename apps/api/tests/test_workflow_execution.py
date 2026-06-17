import pytest
from workflows.graph import WorkflowState, PLANNED_NODE_ORDER, build_workflow_graph
from workflows.executor import WorkflowExecutor


def test_workflow_state_schema() -> None:
    # Verify that the keys in WorkflowState TypedDict match expected structure
    expected_keys = {
        "workflow_id",
        "org_id",
        "user_request",
        "template_slug",
        "band_room_id",
        "artifacts",
        "selected_agents",
        "retrieved_context",
        "agent_findings",
        "policy_verdict",
        "final_report",
        "status",
    }
    assert set(WorkflowState.__annotations__.keys()) == expected_keys


def test_planned_node_order() -> None:
    # Verify the sequential planned order of nodes
    assert PLANNED_NODE_ORDER == (
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

