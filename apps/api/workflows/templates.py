from models.schemas import WorkflowTemplateRead

WORKFLOW_TEMPLATES = {
    "hr-candidate-screening": WorkflowTemplateRead(
        slug="hr-candidate-screening",
        name="HR Candidate Screening",
        depth="deep",
        agent_slugs=[
            "workflow-router",
            "rag-retriever",
            "resume-jd-matcher",
            "bias-reviewer",
            "interview-planner",
            "policy-guardian",
            "final-decision",
        ],
        required_artifacts=["resume", "job_description", "hiring_policy"],
    ),
    "sales-lead-qualification": WorkflowTemplateRead(
        slug="sales-lead-qualification",
        name="Sales Lead Qualification",
        depth="shallow",
        agent_slugs=["lead-qualifier", "rag-retriever", "final-decision"],
        required_artifacts=["crm_notes"],
    ),
    "engineering-change-review": WorkflowTemplateRead(
        slug="engineering-change-review",
        name="Engineering Change Review",
        depth="shallow",
        agent_slugs=["engineering-reviewer", "policy-guardian", "final-decision"],
        required_artifacts=["code_diff"],
    ),
}


def get_template(slug: str) -> WorkflowTemplateRead:
    try:
        return WORKFLOW_TEMPLATES[slug]
    except KeyError as error:
        raise ValueError(f"Unknown workflow template: {slug}") from error

