from agents.base_agent import ScaffoldAgent


class PolicyGuardianAgent(ScaffoldAgent):
    slug = "policy-guardian"
    name = "Policy Guardian"
    category = "platform"
    description = "Checks findings against policy and escalation rules."

