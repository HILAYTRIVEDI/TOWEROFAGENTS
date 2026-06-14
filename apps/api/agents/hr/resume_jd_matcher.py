from agents.base_agent import ScaffoldAgent


class ResumeJDMatcherAgent(ScaffoldAgent):
    slug = "resume-jd-matcher"
    name = "Resume/JD Matcher"
    category = "hr"
    description = "Compares candidate evidence with role requirements."
    instructions = """
Compare only job-related requirements with evidence explicitly present in the
resume and job description. Distinguish confirmed matches, gaps, and unknowns.
Do not infer protected or sensitive traits and do not make the hiring decision.
"""
