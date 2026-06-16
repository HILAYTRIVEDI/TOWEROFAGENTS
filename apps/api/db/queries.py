import asyncio
from typing import Any, Protocol
from uuid import UUID

from models.schemas import WorkflowCreate


class QueryRepository(Protocol):
    async def save_agent_finding(self, finding: dict[str, Any]) -> dict[str, Any]: ...

    async def save_band_message(self, message: dict[str, Any]) -> dict[str, Any]: ...


class UnconfiguredRepository:
    async def save_agent_finding(self, finding: dict[str, Any]) -> dict[str, Any]:
        raise RuntimeError("Supabase repository is not configured")

    async def save_band_message(self, message: dict[str, Any]) -> dict[str, Any]:
        raise RuntimeError("Supabase repository is not configured")


class WorkflowRepository(Protocol):
    async def create_workflow(self, payload: WorkflowCreate) -> dict[str, Any]: ...

    async def list_workflows(self, org_id: UUID) -> list[dict[str, Any]]: ...

    async def get_workflow(self, workflow_id: UUID) -> dict[str, Any] | None: ...

    async def delete_workflow(self, workflow_id: UUID) -> bool: ...


class SupabaseWorkflowRepository:
    _select = (
        "id,org_id,title,status,band_room_id,created_at,"
        "workflow_templates(slug)"
    )

    def __init__(self, client: Any) -> None:
        self._client = client

    async def create_workflow(self, payload: WorkflowCreate) -> dict[str, Any]:
        return await asyncio.to_thread(self._create_workflow, payload)

    async def list_workflows(self, org_id: UUID) -> list[dict[str, Any]]:
        return await asyncio.to_thread(self._list_workflows, org_id)

    async def get_workflow(self, workflow_id: UUID) -> dict[str, Any] | None:
        return await asyncio.to_thread(self._get_workflow, workflow_id)

    async def delete_workflow(self, workflow_id: UUID) -> bool:
        return await asyncio.to_thread(self._delete_workflow, workflow_id)

    def _create_workflow(self, payload: WorkflowCreate) -> dict[str, Any]:
        template_id = None
        if payload.template_slug:
            template_response = (
                self._client.table("workflow_templates")
                .select("id")
                .eq("slug", payload.template_slug)
                .eq("active", True)
                .limit(1)
                .execute()
            )
            if not template_response.data:
                raise ValueError(f"Unknown workflow template: {payload.template_slug}")
            template_id = template_response.data[0]["id"]

        insert_response = (
            self._client.table("workflows")
            .insert(
                {
                    "org_id": str(payload.org_id),
                    "template_id": template_id,
                    "title": payload.title,
                    "user_request": payload.user_request,
                    "status": "draft",
                }
            )
            .execute()
        )
        if not insert_response.data:
            raise RuntimeError("Supabase workflow insert returned no data")
        workflow_id = UUID(insert_response.data[0]["id"])
        workflow = self._get_workflow(workflow_id)
        if workflow is None:
            raise RuntimeError("Created workflow could not be read back")
        return workflow

    def _list_workflows(self, org_id: UUID) -> list[dict[str, Any]]:
        response = (
            self._client.table("workflows")
            .select(self._select)
            .eq("org_id", str(org_id))
            .order("created_at", desc=True)
            .execute()
        )
        return [self._normalize_workflow(row) for row in response.data or []]

    def _get_workflow(self, workflow_id: UUID) -> dict[str, Any] | None:
        response = (
            self._client.table("workflows")
            .select(self._select)
            .eq("id", str(workflow_id))
            .limit(1)
            .execute()
        )
        if not response.data:
            return None
        return self._normalize_workflow(response.data[0])

    def _delete_workflow(self, workflow_id: UUID) -> bool:
        response = (
            self._client.table("workflows")
            .delete()
            .eq("id", str(workflow_id))
            .execute()
        )
        return bool(response.data)

    @staticmethod
    def _normalize_workflow(row: dict[str, Any]) -> dict[str, Any]:
        template = row.pop("workflow_templates", None)
        row["template_slug"] = template.get("slug") if template else None
        return row
