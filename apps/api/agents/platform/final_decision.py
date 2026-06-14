from agents.base_agent import ScaffoldAgent


class FinalDecisionAgent(ScaffoldAgent):
    slug = "final-decision"
    name = "Final Decision Agent"
    category = "platform"
    description = "Synthesizes verified findings into a decision packet."

