from fastapi import APIRouter

from agents.registry import list_agents
from models.schemas import AgentDescriptor

router = APIRouter(prefix="/agents", tags=["agents"])


@router.get("", response_model=list[AgentDescriptor])
async def get_agents() -> list[AgentDescriptor]:
    return list_agents()

