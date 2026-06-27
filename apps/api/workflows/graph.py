from __future__ import annotations

import operator
from typing import Annotated, Any, TypedDict


class WorkflowState(TypedDict):
    workflow_id: str
    org_id: str
    user_request: str
    template_slug: str | None
    band_room_id: str | None
    artifacts: list[dict[str, Any]]
    selected_agents: list[str]
    retrieved_context: list[dict[str, Any]]
    # Accumulates findings across agent nodes; reducer concatenates additions.
    agent_findings: Annotated[list[dict[str, Any]], operator.add]
    policy_verdict: dict[str, Any] | None
    final_report: str | None
    status: str
    # Execution-tracking fields — populated by agent nodes via accumulator reducers.
    ran_slugs: Annotated[list[str], operator.add]
    skipped_slugs: Annotated[list[str], operator.add]
    providers_used: Annotated[list[str], operator.add]
    # Set by WorkflowExecutor before graph invocation (True when no real LLM router).
    use_mock: bool
    # Written by the terminal aggregate_report node; read by WorkflowExecutor after invoke.
    report_result: dict[str, Any] | None


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


def build_workflow_graph(selected_agents: list[str], router: Any = None) -> Any:
    """Build and compile a LangGraph StateGraph for the given agent sequence.

    One node is created per entry in *selected_agents* (keyed by slug).
    Edges form a linear chain in template order, terminating at an
    aggregate_report node that builds WorkflowReportRead.

    Lazy imports of LangGraph and node factories break the potential
    module-level circular dependency with agent_nodes.py.
    """
    from langgraph.graph import END, START, StateGraph

    from workflows.agent_nodes import make_agent_node, make_report_node

    graph: StateGraph = StateGraph(WorkflowState)

    if not selected_agents:
        # No agents selected: go straight to aggregation.
        graph.add_node("aggregate_report", make_report_node())
        graph.add_edge(START, "aggregate_report")
        graph.add_edge("aggregate_report", END)
        return graph.compile()

    # One node per agent slug — names must be unique within the graph.
    node_names: list[str] = []
    for slug in selected_agents:
        node_name = f"agent_{slug.replace('-', '_')}"
        graph.add_node(node_name, make_agent_node(slug, router))
        node_names.append(node_name)

    # Terminal aggregation node.
    graph.add_node("aggregate_report", make_report_node())

    # Linear chain: START → agent_0 → agent_1 → … → aggregate_report → END
    graph.add_edge(START, node_names[0])
    for i in range(len(node_names) - 1):
        graph.add_edge(node_names[i], node_names[i + 1])
    graph.add_edge(node_names[-1], "aggregate_report")
    graph.add_edge("aggregate_report", END)

    return graph.compile()
