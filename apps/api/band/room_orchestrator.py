from band.client import BandClient


class RoomOrchestrator:
    def __init__(self, client: BandClient) -> None:
        self._client = client

    async def open_workflow_room(
        self,
        *,
        title: str,
        goal: str,
        agent_names: list[str],
        existing_room_id: str | None = None,
    ) -> str:
        room_id = existing_room_id or await self._client.create_room(title)
        assignments = ", ".join(agent_names) if agent_names else "No agents assigned"
        await self._client.post_message(
            room_id,
            f"Workflow: {title}\nGoal: {goal}\nAssignments: {assignments}",
        )
        return room_id

