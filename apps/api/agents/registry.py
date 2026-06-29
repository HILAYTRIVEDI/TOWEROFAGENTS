from agents.engineering.engineering_reviewer import EngineeringReviewerAgent
from agents.hr.bias_reviewer import BiasReviewerAgent
from agents.hr.interview_planner import InterviewPlannerAgent
from agents.hr.resume_jd_matcher import ResumeJDMatcherAgent
from agents.platform.final_decision import FinalDecisionAgent
from agents.platform.policy_guardian import PolicyGuardianAgent
from agents.platform.rag_retriever import RAGRetrieverAgent
from agents.platform.workflow_router import WorkflowRouterAgent
from agents.sales.lead_qualifier import LeadQualifierAgent
from agents.vendor.compliance_agent import ComplianceAgent
from agents.vendor.finance_agent import FinanceAgent
from agents.vendor.legal_agent import LegalAgent
from agents.vendor.procurement_agent import ProcurementAgent
from agents.vendor.security_agent import SecurityAgent
from agents.vendor.vendor_controller import VendorControllerAgent
from models.schemas import AgentDescriptor

AGENT_TYPES = (
    WorkflowRouterAgent,
    RAGRetrieverAgent,
    PolicyGuardianAgent,
    FinalDecisionAgent,
    ResumeJDMatcherAgent,
    BiasReviewerAgent,
    InterviewPlannerAgent,
    LeadQualifierAgent,
    EngineeringReviewerAgent,
    ProcurementAgent,
    LegalAgent,
    SecurityAgent,
    FinanceAgent,
    ComplianceAgent,
    VendorControllerAgent,
)

# slug -> agent class; used by the executor to instantiate with a provider.
AGENT_CLASS_BY_SLUG: dict[str, type] = {cls.slug: cls for cls in AGENT_TYPES}


def list_agents() -> list[AgentDescriptor]:
    return [
        AgentDescriptor(
            slug=agent.slug,
            name=agent.name,
            category=agent.category,
            description=agent.description,
        )
        for agent in AGENT_TYPES
    ]
