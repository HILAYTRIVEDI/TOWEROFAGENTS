from agents.base_agent import ScaffoldAgent


class WorkflowRouterAgent(ScaffoldAgent):
    slug = "workflow-router"
    name = "Workflow Router"
    category = "platform"
    description = "Selects the workflow template and specialist roster."
    instructions = """
Identify whether the request belongs to HR candidate screening, sales lead
qualification, or engineering change review. Recommend the smallest relevant
specialist roster and list the required artifacts. Do not claim that a workflow
was started; execution is not implemented yet.
"""
