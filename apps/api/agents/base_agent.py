from abc import ABC, abstractmethod

from llm.base import ChatProvider
from models.schemas import AgentFinding, AgentInput


class BaseAgent(ABC):
    slug: str
    name: str
    category: str
    description: str
    instructions: str

    def __init__(self, chat_provider: ChatProvider | None = None) -> None:
        self._chat_provider = chat_provider

    @abstractmethod
    async def run(self, agent_input: AgentInput) -> AgentFinding:
        """Execute the agent and return one typed finding."""


class ScaffoldAgent(BaseAgent):
    async def run(self, agent_input: AgentInput) -> AgentFinding:
        raise NotImplementedError(f"{self.name} execution is not implemented in the bootstrap")
