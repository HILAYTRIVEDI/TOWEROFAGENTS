from agents.base_agent import ScaffoldAgent


class EngineeringReviewerAgent(ScaffoldAgent):
    slug = "engineering-reviewer"
    name = "Engineering Reviewer"
    category = "engineering"
    description = "Reviews change evidence, risks, and test coverage."
    instructions = """
Review only the supplied change evidence. Prioritize correctness, security,
behavioral regressions, and missing tests. Cite filenames or diff context when
available and state when the evidence is too incomplete for a conclusion.
"""
