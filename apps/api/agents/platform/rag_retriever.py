from agents.base_agent import ScaffoldAgent


class RAGRetrieverAgent(ScaffoldAgent):
    slug = "rag-retriever"
    name = "RAG Retriever"
    category = "platform"
    description = "Builds a workflow-scoped evidence pack."
    instructions = """
Assess whether the room contains enough source material for an evidence pack.
Ask for missing artifacts and identify which supplied sources support each
statement. Never imply that retrieval or indexing occurred unless tool output
in the current conversation proves it.
"""
