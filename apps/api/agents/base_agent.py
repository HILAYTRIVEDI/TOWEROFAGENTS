import asyncio
import logging
import re
from abc import ABC, abstractmethod
from typing import Any

from models.schemas import AgentFinding, AgentInput
from llm.router import LLMRouter
from core.config import get_settings
from db.supabase_client import create_supabase_client
from band.client import create_band_client

logger = logging.getLogger(__name__)


def clean_uuids(uuid_list: list[str]) -> list[str]:
    pattern = re.compile(
        r"^[a-f0-9]{8}-?[a-f0-9]{4}-?[a-f0-9]{4}-?[a-f0-9]{4}-?[a-f0-9]{12}$",
        re.IGNORECASE,
    )
    return [uid for uid in uuid_list if pattern.match(uid)]


def parse_finding_from_text(text: str, agent_name: str, fallback: dict) -> AgentFinding:
    title = fallback.get("title", f"{agent_name} Analysis")
    finding_type = fallback.get("finding_type", "analysis")
    severity = fallback.get("severity", "info")
    confidence = fallback.get("confidence", 0.8)
    requires_human_review = fallback.get("requires_human_review", False)
    content = text

    lines = text.strip().split("\n")
    parsed_any = False
    content_lines = []
    in_content = False

    for line in lines:
        if in_content:
            content_lines.append(line)
            continue
        if ":" in line:
            parts = line.split(":", 1)
            key = parts[0].strip().lower()
            val = parts[1].strip()
            if key == "title":
                title = val
                parsed_any = True
            elif key in {"finding type", "finding_type"}:
                finding_type = val
                parsed_any = True
            elif key == "severity":
                if val.lower() in {"info", "low", "medium", "high", "critical"}:
                    severity = val.lower()
                    parsed_any = True
            elif key == "confidence":
                try:
                    confidence = float(val)
                    parsed_any = True
                except ValueError:
                    pass
            elif key in {"requires human review", "requires_human_review"}:
                requires_human_review = val.lower() in {"true", "yes", "1"}
                parsed_any = True
            elif key == "content":
                in_content = True
                content_lines.append(val)
                parsed_any = True
        else:
            if not parsed_any:
                pass

    if in_content and content_lines:
        content = "\n".join(content_lines)
    elif not parsed_any:
        if "[mock]" not in text:
            content = text

    return AgentFinding(
        agent_name=agent_name,
        finding_type=finding_type,
        severity=severity,
        title=title,
        content=content,
        evidence_chunk_ids=fallback.get("evidence_chunk_ids", []),
        confidence=confidence,
        requires_human_review=requires_human_review,
    )


class BaseAgent(ABC):
    slug: str
    name: str
    category: str
    description: str
    instructions: str

    @abstractmethod
    async def run(self, agent_input: AgentInput) -> AgentFinding:
        """Execute the agent and return one typed finding."""


class ScaffoldAgent(BaseAgent):
    async def run(self, agent_input: AgentInput) -> AgentFinding:
        settings = get_settings()
        router = LLMRouter(settings)
        provider = router.for_task(self.slug)

        fallback_data = {
            "title": f"{self.name} Analysis",
            "finding_type": "analysis",
            "severity": "info",
            "confidence": 0.8,
            "requires_human_review": False,
            "evidence_chunk_ids": [],
        }

        if self.slug == "resume-jd-matcher":
            fallback_data.update(
                {
                    "title": "Candidate Resume vs Job Description Match",
                    "finding_type": "match_analysis",
                    "severity": "info",
                    "confidence": 0.85,
                    "requires_human_review": False,
                }
            )
        elif self.slug == "bias-reviewer":
            fallback_data.update(
                {
                    "title": "Fairness and Bias Assessment",
                    "finding_type": "bias_check",
                    "severity": "low",
                    "confidence": 0.95,
                    "requires_human_review": False,
                }
            )
        elif self.slug == "interview-planner":
            fallback_data.update(
                {
                    "title": "Customized Interview Plan",
                    "finding_type": "interview_plan",
                    "severity": "info",
                    "confidence": 0.90,
                    "requires_human_review": False,
                }
            )
        elif self.slug == "lead-qualifier":
            fallback_data.update(
                {
                    "title": "Sales Lead ICP Matching",
                    "finding_type": "lead_qualification",
                    "severity": "medium",
                    "confidence": 0.80,
                    "requires_human_review": False,
                }
            )
        elif self.slug == "engineering-reviewer":
            fallback_data.update(
                {
                    "title": "Code Diff Risk Assessment",
                    "finding_type": "code_review",
                    "severity": "medium",
                    "confidence": 0.88,
                    "requires_human_review": True,
                }
            )
        elif self.slug == "workflow-router":
            fallback_data.update(
                {
                    "title": "Workflow Template Classification",
                    "finding_type": "routing_decision",
                    "severity": "info",
                    "confidence": 0.98,
                    "requires_human_review": False,
                }
            )
        elif self.slug == "rag-retriever":
            fallback_data.update(
                {
                    "title": "Document Context Retrieval Summary",
                    "finding_type": "context_retrieval",
                    "severity": "info",
                    "confidence": 0.95,
                    "requires_human_review": False,
                }
            )
        elif self.slug == "policy-guardian":
            fallback_data.update(
                {
                    "title": "Hiring Policy Compliance Verification",
                    "finding_type": "policy_compliance",
                    "severity": "low",
                    "confidence": 0.92,
                    "requires_human_review": False,
                }
            )
        elif self.slug == "final-decision":
            fallback_data.update(
                {
                    "title": "Final Candidate Screening Synthesis",
                    "finding_type": "synthesis",
                    "severity": "info",
                    "confidence": 0.90,
                    "requires_human_review": True,
                }
            )

        context_str = "\n".join(
            [f"- Chunk: {c.get('content', '')}" for c in agent_input.context_chunks]
        )
        artifacts_str = "\n".join(
            [
                f"- Artifact: {art.get('filename', '')} ({art.get('doc_type', '')}): {art.get('content', '') or art.get('storage_path', '')}"
                for art in agent_input.artifacts
            ]
        )

        prompt = f"""You are the {self.name} agent.
Instructions:
{self.instructions}

User Request/Task:
{agent_input.task}

Context Evidence Chunks:
{context_str or "No context chunks provided."}

Artifacts:
{artifacts_str or "No artifacts provided."}

Please analyze the above information and output your findings.
You MUST format your output exactly as follows:
Title: <finding title>
Finding Type: <finding type>
Severity: <info/low/medium/high/critical>
Confidence: <float between 0.0 and 1.0>
Requires Human Review: <true/false>
Content: <finding details, observations, strengths, gaps, or decisions>
"""

        res = await provider.complete(messages=[{"role": "user", "content": prompt}])
        text = res.content or ""

        evidence_chunk_ids = []
        for chunk in agent_input.context_chunks:
            if "id" in chunk:
                evidence_chunk_ids.append(str(chunk["id"]))
        fallback_data["evidence_chunk_ids"] = evidence_chunk_ids

        finding = parse_finding_from_text(text, self.name, fallback_data)

        if "[mock]" in text:
            if self.slug == "resume-jd-matcher":
                finding.content = "Candidate matches 85% of core requirements (Python, system design). Gap identified: React/frontend experience."
            elif self.slug == "bias-reviewer":
                finding.content = "No demographic or protected-class bias detected in the screening process. Content is objective."
            elif self.slug == "interview-planner":
                finding.content = "Proposed interview questions:\n1. Can you explain your architecture choices for stateful graphs?\n2. How do you approach testing distributed systems?"
            elif self.slug == "lead-qualifier":
                finding.content = "ICP fit score is strong. Pain point: CRM scalability. Suggested next step: Schedule discovery call."
            elif self.slug == "engineering-reviewer":
                finding.content = "Risks: Potential resource leak in supabase connection handling. Suggested action: Add test verifying close() is called."
            elif self.slug == "workflow-router":
                finding.content = "Input request identified as candidate screening. Suggested routing: 'hr-candidate-screening'."
            elif self.slug == "rag-retriever":
                finding.content = "Retrieved 3 chunks: resume details, job requirements, and organizational hiring policy."
            elif self.slug == "policy-guardian":
                finding.content = "Compliance check: candidate meets all mandatory education and background criteria. No policy exceptions."
            elif self.slug == "final-decision":
                finding.content = "Synthesis: Strong candidate for backend role. Recommending technical interview, focusing on the frontend gap."

        if settings.supabase_url and settings.supabase_service_role_key:
            try:
                supabase = create_supabase_client(settings)
                agent_resp = await asyncio.to_thread(
                    lambda: supabase.table("agents")
                    .select("id")
                    .eq("slug", self.slug)
                    .limit(1)
                    .execute()
                )
                agent_db_id = None
                if agent_resp.data:
                    agent_db_id = agent_resp.data[0]["id"]

                workflow_agent_id = None
                if agent_db_id:
                    wa_resp = await asyncio.to_thread(
                        lambda: supabase.table("workflow_agents")
                        .select("id")
                        .eq("workflow_id", agent_input.workflow_id)
                        .eq("agent_id", agent_db_id)
                        .limit(1)
                        .execute()
                    )
                    if wa_resp.data:
                        workflow_agent_id = wa_resp.data[0]["id"]

                clean_ev_ids = clean_uuids(finding.evidence_chunk_ids)

                insert_payload = {
                    "org_id": agent_input.org_id,
                    "workflow_id": agent_input.workflow_id,
                    "agent_slug": self.slug,
                    "finding_type": finding.finding_type,
                    "severity": finding.severity,
                    "title": finding.title,
                    "content": finding.content,
                    "confidence": finding.confidence,
                    "requires_human_review": finding.requires_human_review,
                    "evidence_chunk_ids": clean_ev_ids,
                    "raw_output": {"response": text},
                }
                if workflow_agent_id:
                    insert_payload["workflow_agent_id"] = workflow_agent_id

                await asyncio.to_thread(
                    lambda: supabase.table("agent_findings")
                    .insert(insert_payload)
                    .execute()
                )
            except Exception as e:
                logger.error("Failed to save finding in db: %s", e, exc_info=True)

        if agent_input.band_room_id:
            try:
                band_client = create_band_client(settings)
                band_content = (
                    f"[{self.name} completed]\n"
                    f"Title: {finding.title}\n"
                    f"Severity: {finding.severity} | Confidence: {finding.confidence:.2f}\n"
                    f"Result: {finding.content}"
                )
                await band_client.post_message(agent_input.band_room_id, band_content)
            except Exception as e:
                logger.error("Failed to post finding to Band: %s", e, exc_info=True)

        return finding
