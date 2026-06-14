from agents.base_agent import ScaffoldAgent


class BiasReviewerAgent(ScaffoldAgent):
    slug = "bias-reviewer"
    name = "Bias/Safety Reviewer"
    category = "hr"
    description = "Flags unsupported, sensitive, or potentially biased reasoning."
    instructions = """
Audit candidate-screening reasoning for unsupported assumptions, proxy use,
sensitive-trait inference, inconsistent standards, and non-job-related factors.
Recommend corrections and human review; do not rank candidates yourself.
"""
