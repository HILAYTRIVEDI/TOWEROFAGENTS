from agents.base_agent import ScaffoldAgent


class LeadQualifierAgent(ScaffoldAgent):
    slug = "lead-qualifier"
    name = "Lead Qualifier"
    category = "sales"
    description = "Scores ICP fit and proposes a follow-up action."

