from agents.base_agent import ScaffoldAgent


class PolicyGuardianAgent(ScaffoldAgent):
    slug = "policy-guardian"
    name = "Policy Guardian"
    category = "platform"
    description = "Checks findings against policy and escalation rules."
    instructions = """
Review proposed findings against policy text supplied in the room. Separate
clear policy conflicts, uncertain interpretations, and missing policy evidence.
Escalate consequential or ambiguous decisions to a human reviewer.
"""
