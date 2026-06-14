from agents.base_agent import ScaffoldAgent


class FinalDecisionAgent(ScaffoldAgent):
    slug = "final-decision"
    name = "Final Decision Agent"
    category = "platform"
    description = "Synthesizes verified findings into a decision packet."
    instructions = """
Synthesize only findings and evidence visible in the room. Clearly label
strengths, gaps, unresolved questions, and the recommended human next step.
Never make an autonomous hiring, employment, legal, or other high-impact final
decision.
"""
