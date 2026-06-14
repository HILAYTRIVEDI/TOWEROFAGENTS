from agents.base_agent import ScaffoldAgent


class EngineeringReviewerAgent(ScaffoldAgent):
    slug = "engineering-reviewer"
    name = "Engineering Reviewer"
    category = "engineering"
    description = "Reviews change evidence, risks, and test coverage."

