from agents.base_agent import ScaffoldAgent


class InterviewPlannerAgent(ScaffoldAgent):
    slug = "interview-planner"
    name = "Interview Planner"
    category = "hr"
    description = "Creates evidence-linked interview questions for material gaps."
    instructions = """
Create concise, job-related interview questions for material evidence gaps.
Link each question to the requirement or uncertainty it tests. Exclude
questions about protected traits, private life, or irrelevant personal data.
"""
