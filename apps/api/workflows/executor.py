from typing import Any
from core.config import get_settings
from db.supabase_client import create_supabase_client
from band.client import create_band_client
from workflows.graph import WorkflowState, build_workflow_graph


class WorkflowExecutor:
    def __init__(self) -> None:
        self._settings = get_settings()
        self._supabase_client = create_supabase_client(self._settings)
        self._band_client = create_band_client(self._settings)
        self._graph = build_workflow_graph(
            self._settings, self._supabase_client, self._band_client
        )

    async def run(self, state: WorkflowState) -> dict[str, Any]:
        result = await self._graph.ainvoke(state)
        return result
