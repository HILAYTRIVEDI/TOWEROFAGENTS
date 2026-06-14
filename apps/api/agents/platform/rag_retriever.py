from agents.base_agent import ScaffoldAgent


class RAGRetrieverAgent(ScaffoldAgent):
    slug = "rag-retriever"
    name = "RAG Retriever"
    category = "platform"
    description = "Builds a workflow-scoped evidence pack."

