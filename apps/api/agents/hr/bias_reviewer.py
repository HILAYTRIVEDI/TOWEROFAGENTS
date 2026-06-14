from agents.base_agent import ScaffoldAgent


class BiasReviewerAgent(ScaffoldAgent):
    slug = "bias-reviewer"
    name = "Bias/Safety Reviewer"
    category = "hr"
    description = "Flags unsupported, sensitive, or potentially biased reasoning."

