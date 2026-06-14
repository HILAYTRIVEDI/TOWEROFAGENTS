from agents.base_agent import ScaffoldAgent


class ResumeJDMatcherAgent(ScaffoldAgent):
    slug = "resume-jd-matcher"
    name = "Resume/JD Matcher"
    category = "hr"
    description = "Compares candidate evidence with role requirements."

