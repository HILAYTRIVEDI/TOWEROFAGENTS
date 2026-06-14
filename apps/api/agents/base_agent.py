from abc import ABC, abstractmethod

from models.schemas import AgentFinding, AgentInput


class BaseAgent(ABC):
    slug: str
    name: str
    category: str
    description: str
    instructions: str

    @abstractmethod
    async def run(self, agent_input: AgentInput) -> AgentFinding:
        """Execute the agent and return one typed finding."""


class ScaffoldAgent(BaseAgent):
    async def run(self, agent_input: AgentInput) -> AgentFinding:
        raise NotImplementedError(f"{self.name} execution is not implemented in the bootstrap")
