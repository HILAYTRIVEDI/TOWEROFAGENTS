"""WorkflowExecutor: thin driver over the LangGraph workflow graph.

The per-agent dispatch and report-building logic lives in agent_nodes.py.
This module builds the compiled graph, invokes it with an initialised state,
and maps the final graph state to the return shape expected by
routes/workflows.py (keys: "report", "ordered_findings", "payload").
"""
from typing import Any

from llm.router import LLMRouter
from models.schemas import AgentFinding, WorkflowReportRead
from workflows.graph import WorkflowState, build_workflow_graph

# Re-export helpers so callers that relied on importing them from here still work.
from workflows.agent_nodes import _clean_note, _extract_questions  # noqa: F401


class WorkflowExecutor:
    def __init__(self, settings=None) -> None:
        # settings is optional so existing call-sites that omit it still work.
        self._settings = settings

    async def run(self, state: WorkflowState) -> dict[str, Any]:
        router = LLMRouter(self._settings) if self._settings else None

        # Extend the caller-supplied state dict with accumulator fields required
        # by the graph.  agent_findings is already [] from routes/workflows.py.
        init_state: dict[str, Any] = {
            **state,
            "ran_slugs": [],
            "skipped_slugs": [],
            "providers_used": [],
            "use_mock": router is None,
            "report_result": None,
        }

        compiled = build_workflow_graph(state["selected_agents"], router)
        final_state: dict[str, Any] = await compiled.ainvoke(init_state)

        # Reconstruct typed objects from the serialised graph state.
        findings = [AgentFinding.model_validate(d) for d in final_state["agent_findings"]]
        ran_slugs: list[str] = final_state["ran_slugs"]
        skipped_slugs: list[str] = final_state["skipped_slugs"]
        providers_used: list[str] = final_state["providers_used"]
        any_mock: bool = final_state.get("use_mock", True) or any(
            f.confidence == 0.0 for f in findings
        )

        report = WorkflowReportRead.model_validate(final_state["report_result"])
        decision_packet = report.report_payload.get("decision_packet")

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
                **({"decision_packet": decision_packet} if decision_packet else {}),
            },
        }
