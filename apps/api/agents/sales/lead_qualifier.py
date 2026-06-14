from agents.base_agent import ScaffoldAgent


class LeadQualifierAgent(ScaffoldAgent):
    slug = "lead-qualifier"
    name = "Lead Qualifier"
    category = "sales"
    description = "Scores ICP fit and proposes a follow-up action."
    instructions = """
Evaluate lead fit only from supplied ICP criteria and CRM notes. Separate
positive signals, risks, and missing facts, then suggest a reversible follow-up
action. Do not invent company facts, intent signals, or contact activity.
"""
