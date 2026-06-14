from agents.base_agent import ScaffoldAgent


class WorkflowRouterAgent(ScaffoldAgent):
    slug = "workflow-router"
    name = "Workflow Router"
    category = "platform"
    description = "Selects the workflow template and specialist roster."

