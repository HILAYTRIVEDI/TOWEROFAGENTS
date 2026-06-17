import asyncio
import logging
import re
from datetime import datetime
from typing import Any, TypedDict
from langgraph.graph import StateGraph, START, END

from agents.registry import AGENT_TYPES
from core.config import Settings
from band.client import BandClient

logger = logging.getLogger(__name__)


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


def clean_uuids(uuid_list: list[str]) -> list[str]:
    pattern = re.compile(
        r"^[a-f0-9]{8}-?[a-f0-9]{4}-?[a-f0-9]{4}-?[a-f0-9]{4}-?[a-f0-9]{12}$",
        re.IGNORECASE,
    )
    return [uid for uid in uuid_list if pattern.match(uid)]


def build_workflow_graph(
    settings: Settings, supabase_client: Any, band_client: BandClient
) -> Any:
    async def intake_node(state: WorkflowState) -> dict[str, Any]:
        workflow_id = state["workflow_id"]
        logger.info("Intake node: starting execution for workflow %s", workflow_id)

        # Retrieve workflow details
        workflow = await asyncio.to_thread(
            lambda: supabase_client.table("workflows")
            .select("title, user_request, band_room_id, template_id, status")
            .eq("id", workflow_id)
            .single()
            .execute()
        )

        user_request = state.get("user_request") or workflow.data.get("user_request")
        band_room_id = state.get("band_room_id") or workflow.data.get("band_room_id")

        # Get template slug if template_id is present
        template_slug = state.get("template_slug")
        if not template_slug and workflow.data.get("template_id"):
            template_resp = await asyncio.to_thread(
                lambda: supabase_client.table("workflow_templates")
                .select("slug")
                .eq("id", workflow.data["template_id"])
                .single()
                .execute()
            )
            if template_resp.data:
                template_slug = template_resp.data["slug"]

        # Fetch documents
        docs_resp = await asyncio.to_thread(
            lambda: supabase_client.table("documents")
            .select("id, filename, doc_type, status, storage_path")
            .eq("workflow_id", workflow_id)
            .execute()
        )
        artifacts = docs_resp.data or []

        # Update workflow status to running
        await asyncio.to_thread(
            lambda: supabase_client.table("workflows")
            .update({"status": "running"})
            .eq("id", workflow_id)
            .execute()
        )

        return {
            "user_request": user_request,
            "band_room_id": band_room_id,
            "template_slug": template_slug,
            "artifacts": artifacts,
            "status": "running",
        }

    async def select_template_node(state: WorkflowState) -> dict[str, Any]:
        template_slug = state.get("template_slug")
        logger.info("Select template node: template_slug is %s", template_slug)

        if not template_slug:
            from agents.platform.workflow_router import WorkflowRouterAgent
            router_agent = WorkflowRouterAgent()
            from models.schemas import AgentInput

            agent_input = AgentInput(
                workflow_id=state["workflow_id"],
                org_id=state["org_id"],
                task="Determine workflow template and specialist roster.",
                context_chunks=[],
                artifacts=state["artifacts"],
                band_room_id=state["band_room_id"],
            )
            finding = await router_agent.run(agent_input)

            combined = (
                (state["user_request"] or "").lower()
                + " "
                + (finding.content or "").lower()
            )
            if "sale" in combined or "lead" in combined or "crm" in combined:
                template_slug = "sales-lead-qualification"
            elif "engineer" in combined or "code" in combined or "diff" in combined:
                template_slug = "engineering-change-review"
            else:
                template_slug = "hr-candidate-screening"

        # Update template_id in database if template_slug is resolved now
        if template_slug:
            template_resp = await asyncio.to_thread(
                lambda: supabase_client.table("workflow_templates")
                .select("id")
                .eq("slug", template_slug)
                .single()
                .execute()
            )
            if template_resp.data:
                template_id = (
                    template_resp.data[0]["id"]
                    if isinstance(template_resp.data, list)
                    else template_resp.data["id"]
                )
                await asyncio.to_thread(
                    lambda: supabase_client.table("workflows")
                    .update({"template_id": template_id})
                    .eq("id", state["workflow_id"])
                    .execute()
                )

        return {"template_slug": template_slug}

    async def create_band_room_node(state: WorkflowState) -> dict[str, Any]:
        band_room_id = state.get("band_room_id")
        template_slug = state["template_slug"] or "hr-candidate-screening"
        logger.info("Create band room node: room_id is %s", band_room_id)

        from workflows.templates import get_template

        template = get_template(template_slug)

        agent_names = []
        for slug in template.agent_slugs:
            for ag in AGENT_TYPES:
                if ag.slug == slug:
                    agent_names.append(ag.name)

        if not band_room_id:
            from band.room_orchestrator import RoomOrchestrator

            orchestrator = RoomOrchestrator(band_client)

            workflow_title = "Screening Workflow"
            wf_title_resp = await asyncio.to_thread(
                lambda: supabase_client.table("workflows")
                .select("title")
                .eq("id", state["workflow_id"])
                .single()
                .execute()
            )
            if wf_title_resp.data:
                workflow_title = wf_title_resp.data["title"]

            band_room_id = await orchestrator.open_workflow_room(
                title=workflow_title,
                goal=state["user_request"] or "Execute screening",
                agent_names=agent_names,
            )

            await asyncio.to_thread(
                lambda: supabase_client.table("workflows")
                .update({"band_room_id": band_room_id})
                .eq("id", state["workflow_id"])
                .execute()
            )

        return {"band_room_id": band_room_id}

    async def retrieve_context_node(state: WorkflowState) -> dict[str, Any]:
        workflow_id = state["workflow_id"]
        org_id = state["org_id"]
        logger.info("Retrieve context node: workflow_id %s", workflow_id)

        from agents.platform.rag_retriever import RAGRetrieverAgent

        retriever_agent = RAGRetrieverAgent()

        chunks_resp = await asyncio.to_thread(
            lambda: supabase_client.table("document_chunks")
            .select("id, content, metadata")
            .eq("workflow_id", workflow_id)
            .execute()
        )
        chunks = chunks_resp.data or []

        from models.schemas import AgentInput

        agent_input = AgentInput(
            workflow_id=workflow_id,
            org_id=org_id,
            task="Retrieve relevant documents and prepare context.",
            context_chunks=chunks,
            artifacts=state["artifacts"],
            band_room_id=state["band_room_id"],
        )
        await retriever_agent.run(agent_input)

        return {"retrieved_context": chunks}

    async def spawn_agents_node(state: WorkflowState) -> dict[str, Any]:
        template_slug = state["template_slug"] or "hr-candidate-screening"
        logger.info("Spawn agents node: template_slug %s", template_slug)

        from workflows.templates import get_template

        template = get_template(template_slug)
        selected_agents = template.agent_slugs

        workflow_id = state["workflow_id"]
        org_id = state["org_id"]

        agents_resp = await asyncio.to_thread(
            lambda: supabase_client.table("agents").select("id, slug").execute()
        )
        agent_map = {row["slug"]: row["id"] for row in agents_resp.data or []}

        for idx, slug in enumerate(selected_agents):
            agent_id = agent_map.get(slug)
            if agent_id:
                try:
                    await asyncio.to_thread(
                        lambda: supabase_client.table("workflow_agents")
                        .upsert(
                            {
                                "org_id": org_id,
                                "workflow_id": workflow_id,
                                "agent_id": agent_id,
                                "execution_order": idx,
                                "status": "assigned",
                            },
                            on_conflict="workflow_id,agent_id",
                        )
                        .execute()
                    )
                except Exception as e:
                    logger.error("Failed to upsert workflow agent %s: %s", slug, e)

        return {"selected_agents": selected_agents}

    async def specialist_agent_execution_node(state: WorkflowState) -> dict[str, Any]:
        workflow_id = state["workflow_id"]
        org_id = state["org_id"]
        selected_agents = state["selected_agents"]
        band_room_id = state["band_room_id"]
        artifacts = state["artifacts"]
        retrieved_context = state["retrieved_context"]
        logger.info("Specialist execution node starting")

        agent_findings = []
        agent_classes = {ag.slug: ag for ag in AGENT_TYPES}

        specialist_slugs = [
            slug
            for slug in selected_agents
            if slug
            not in {
                "workflow-router",
                "rag-retriever",
                "policy-guardian",
                "final-decision",
            }
        ]

        from models.schemas import AgentInput

        for slug in specialist_slugs:
            agent_class = agent_classes.get(slug)
            if not agent_class:
                continue

            agent_db_id = None
            agent_resp = await asyncio.to_thread(
                lambda: supabase_client.table("agents")
                .select("id")
                .eq("slug", slug)
                .limit(1)
                .execute()
            )
            if agent_resp.data:
                agent_db_id = agent_resp.data[0]["id"]

            if agent_db_id:
                await asyncio.to_thread(
                    lambda: supabase_client.table("workflow_agents")
                    .update({"status": "running"})
                    .eq("workflow_id", workflow_id)
                    .eq("agent_id", agent_db_id)
                    .execute()
                )

            agent_inst = agent_class()
            agent_input = AgentInput(
                workflow_id=workflow_id,
                org_id=org_id,
                task=f"Run specialist analysis for {agent_inst.name}.",
                context_chunks=retrieved_context,
                artifacts=artifacts,
                band_room_id=band_room_id,
            )

            finding = await agent_inst.run(agent_input)
            agent_findings.append(finding.model_dump())

            if agent_db_id:
                await asyncio.to_thread(
                    lambda: supabase_client.table("workflow_agents")
                    .update({"status": "completed"})
                    .eq("workflow_id", workflow_id)
                    .eq("agent_id", agent_db_id)
                    .execute()
                )

        return {"agent_findings": agent_findings}

    async def policy_guardian_node(state: WorkflowState) -> dict[str, Any]:
        selected_agents = state["selected_agents"]
        if "policy-guardian" not in selected_agents:
            logger.info("Policy guardian skipped (not selected)")
            return {"policy_verdict": None}

        workflow_id = state["workflow_id"]
        org_id = state["org_id"]
        band_room_id = state["band_room_id"]
        artifacts = state["artifacts"]
        retrieved_context = state["retrieved_context"]
        agent_findings = state["agent_findings"]
        logger.info("Policy guardian node starting")

        from agents.platform.policy_guardian import PolicyGuardianAgent

        guardian = PolicyGuardianAgent()

        agent_db_id = None
        agent_resp = await asyncio.to_thread(
            lambda: supabase_client.table("agents")
            .select("id")
            .eq("slug", "policy-guardian")
            .limit(1)
            .execute()
        )
        if agent_resp.data:
            agent_db_id = agent_resp.data[0]["id"]

        if agent_db_id:
            await asyncio.to_thread(
                lambda: supabase_client.table("workflow_agents")
                .update({"status": "running"})
                .eq("workflow_id", workflow_id)
                .eq("agent_id", agent_db_id)
                .execute()
            )

        from models.schemas import AgentInput

        task_str = "Review the following specialist agent findings against policy:\n" + "\n".join(
            [
                f"- {f.get('agent_name')}: {f.get('title')} (Severity: {f.get('severity')}) - {f.get('content')}"
                for f in agent_findings
            ]
        )

        agent_input = AgentInput(
            workflow_id=workflow_id,
            org_id=org_id,
            task=task_str,
            context_chunks=retrieved_context,
            artifacts=artifacts,
            band_room_id=band_room_id,
        )

        finding = await guardian.run(agent_input)

        if agent_db_id:
            await asyncio.to_thread(
                lambda: supabase_client.table("workflow_agents")
                .update({"status": "completed"})
                .eq("workflow_id", workflow_id)
                .eq("agent_id", agent_db_id)
                .execute()
            )

        return {"policy_verdict": finding.model_dump()}

    async def final_decision_node(state: WorkflowState) -> dict[str, Any]:
        selected_agents = state["selected_agents"]
        if "final-decision" not in selected_agents:
            logger.info("Final decision skipped (not selected)")
            return {"final_report": None}

        workflow_id = state["workflow_id"]
        org_id = state["org_id"]
        band_room_id = state["band_room_id"]
        artifacts = state["artifacts"]
        retrieved_context = state["retrieved_context"]
        agent_findings = state["agent_findings"]
        policy_verdict = state["policy_verdict"]
        logger.info("Final decision node starting")

        from agents.platform.final_decision import FinalDecisionAgent

        decision_agent = FinalDecisionAgent()

        agent_db_id = None
        agent_resp = await asyncio.to_thread(
            lambda: supabase_client.table("agents")
            .select("id")
            .eq("slug", "final-decision")
            .limit(1)
            .execute()
        )
        if agent_resp.data:
            agent_db_id = agent_resp.data[0]["id"]

        if agent_db_id:
            await asyncio.to_thread(
                lambda: supabase_client.table("workflow_agents")
                .update({"status": "running"})
                .eq("workflow_id", workflow_id)
                .eq("agent_id", agent_db_id)
                .execute()
            )

        from models.schemas import AgentInput

        findings_summary = "\n".join(
            [
                f"- {f.get('agent_name')}: {f.get('title')} ({f.get('severity')}) - {f.get('content')}"
                for f in agent_findings
            ]
        )
        if policy_verdict:
            findings_summary += f"\n- Policy Guardian: {policy_verdict.get('title')} ({policy_verdict.get('severity')}) - {policy_verdict.get('content')}"

        task_str = (
            f"Synthesize all findings into a final report:\n{findings_summary}"
        )

        agent_input = AgentInput(
            workflow_id=workflow_id,
            org_id=org_id,
            task=task_str,
            context_chunks=retrieved_context,
            artifacts=artifacts,
            band_room_id=band_room_id,
        )

        finding = await decision_agent.run(agent_input)

        if agent_db_id:
            await asyncio.to_thread(
                lambda: supabase_client.table("workflow_agents")
                .update({"status": "completed"})
                .eq("workflow_id", workflow_id)
                .eq("agent_id", agent_db_id)
                .execute()
            )

        return {"final_report": finding.content}

    async def save_report_node(state: WorkflowState) -> dict[str, Any]:
        workflow_id = state["workflow_id"]
        org_id = state["org_id"]
        final_report = state["final_report"]
        agent_findings = state["agent_findings"]
        policy_verdict = state["policy_verdict"]
        logger.info("Save report node starting for workflow %s", workflow_id)

        requires_human_review = False
        recommendation = "moving forward"
        fit_score = 80.0
        strengths = []
        gaps = []
        interview_questions = []
        policy_note = None

        for f in agent_findings:
            if f.get("requires_human_review") or f.get("severity") in {
                "high",
                "critical",
            }:
                requires_human_review = True

            content = f.get("content", "")
            if f.get("agent_slug") == "resume-jd-matcher":
                strengths.append("Matches core technical requirements.")
                if "react" in content.lower() or "gap" in content.lower():
                    gaps.append("React or frontend experience gap.")
            elif f.get("agent_slug") == "interview-planner":
                for line in content.split("\n"):
                    line_clean = line.strip().lstrip("0123456789.- ")
                    if line_clean and (
                        "?" in line_clean
                        or line_clean.startswith("Can")
                        or line_clean.startswith("How")
                        or line_clean.startswith("Walk")
                    ):
                        interview_questions.append(line_clean)
            elif f.get("agent_slug") == "lead-qualifier":
                fit_score = 75.0
                strengths.append("ICP alignment is good.")
                gaps.append("CRM integration scale pain points.")
            elif f.get("agent_slug") == "engineering-reviewer":
                fit_score = 70.0
                gaps.append("Code risk: Connection pool leak risk in client.")
                interview_questions.append(
                    "How do you manage db client session states?"
                )

        if policy_verdict:
            policy_note = policy_verdict.get("content")
            if policy_verdict.get("requires_human_review") or policy_verdict.get(
                "severity"
            ) in {"high", "critical"}:
                requires_human_review = True
                recommendation = "human review required"

        if final_report:
            score_match = re.search(
                r"fit\s*score:\s*(\d+)", final_report, re.IGNORECASE
            )
            if score_match:
                fit_score = float(score_match.group(1))

            if "reject" in final_report.lower():
                recommendation = "reject"
            elif (
                "human review" in final_report.lower()
                or "requires review" in final_report.lower()
            ):
                recommendation = "human review required"
            elif (
                "interview" in final_report.lower()
                or "move forward" in final_report.lower()
            ):
                recommendation = "moving forward"

            if not strengths:
                strengths = ["Strong candidate background based on matching results."]
            if not gaps:
                gaps = ["Minor candidate uncertainties to be verified during interview."]
            if not interview_questions:
                interview_questions = [
                    "Can you describe your experience design choices?",
                    "How do you test and verify your code compliance?",
                ]

        evidence_chunk_ids = []
        for f in agent_findings:
            evidence_chunk_ids.extend(f.get("evidence_chunk_ids", []))
        if policy_verdict:
            evidence_chunk_ids.extend(policy_verdict.get("evidence_chunk_ids", []))

        clean_ev_ids = clean_uuids(evidence_chunk_ids)

        report_payload = {
            "org_id": org_id,
            "workflow_id": workflow_id,
            "recommendation": recommendation,
            "summary": final_report or "No report content generated.",
            "fit_score": fit_score,
            "strengths": strengths,
            "gaps": gaps,
            "interview_questions": interview_questions,
            "policy_note": policy_note,
            "evidence_chunk_ids": clean_ev_ids,
            "requires_human_review": requires_human_review,
            "report_payload": {"synthesized_at": datetime.now().isoformat()},
        }

        await asyncio.to_thread(
            lambda: supabase_client.table("workflow_reports")
            .upsert(report_payload, on_conflict="workflow_id")
            .execute()
        )

        final_workflow_status = (
            "awaiting_review" if requires_human_review else "completed"
        )
        await asyncio.to_thread(
            lambda: supabase_client.table("workflows")
            .update({"status": final_workflow_status})
            .eq("id", workflow_id)
            .execute()
        )

        if state.get("band_room_id"):
            try:
                decision_msg = (
                    f"🏆 [Workflow Final Decision]\n"
                    f"Recommendation: {recommendation.upper()}\n"
                    f"Fit Score: {fit_score}%\n"
                    f"Summary: {final_report[:200]}..."
                )
                await band_client.post_message(state["band_room_id"], decision_msg)
            except Exception as e:
                logger.error("Failed to post final decision to Band: %s", e)

        return {"status": final_workflow_status}

    workflow = StateGraph(WorkflowState)

    workflow.add_node("intake", intake_node)
    workflow.add_node("select_template", select_template_node)
    workflow.add_node("create_band_room", create_band_room_node)
    workflow.add_node("retrieve_context", retrieve_context_node)
    workflow.add_node("spawn_agents", spawn_agents_node)
    workflow.add_node("specialist_agent_execution", specialist_agent_execution_node)
    workflow.add_node("policy_guardian", policy_guardian_node)
    workflow.add_node("final_decision", final_decision_node)
    workflow.add_node("save_report", save_report_node)

    workflow.add_edge(START, "intake")
    workflow.add_edge("intake", "select_template")
    workflow.add_edge("select_template", "create_band_room")
    workflow.add_edge("create_band_room", "retrieve_context")
    workflow.add_edge("retrieve_context", "spawn_agents")
    workflow.add_edge("spawn_agents", "specialist_agent_execution")
    workflow.add_edge("specialist_agent_execution", "policy_guardian")
    workflow.add_edge("policy_guardian", "final_decision")
    workflow.add_edge("final_decision", "save_report")
    workflow.add_edge("save_report", END)

    return workflow.compile()
