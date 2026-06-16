from typing import NoReturn
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status

from core.config import Settings, get_settings
from db.queries import SupabaseWorkflowRepository, WorkflowRepository
from db.supabase_client import create_supabase_client
from models.schemas import WorkflowCreate, WorkflowRead, WorkflowReportRead, WorkflowRunRequest

router = APIRouter(prefix="/workflows", tags=["workflows"])


def get_workflow_repository(
    settings: Settings = Depends(get_settings),
) -> WorkflowRepository:
    try:
        return SupabaseWorkflowRepository(create_supabase_client(settings))
    except RuntimeError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(error),
        ) from error


def execution_not_implemented() -> NoReturn:
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Workflow indexing and execution are not implemented yet",
    )


@router.post("", response_model=WorkflowRead, status_code=status.HTTP_201_CREATED)
async def create_workflow(
    payload: WorkflowCreate,
    repository: WorkflowRepository = Depends(get_workflow_repository),
) -> WorkflowRead:
    try:
        workflow = await repository.create_workflow(payload)
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error
    return WorkflowRead.model_validate(workflow)


@router.get("", response_model=list[WorkflowRead])
async def list_workflows(
    org_id: UUID | None = Query(default=None),
    repository: WorkflowRepository = Depends(get_workflow_repository),
) -> list[WorkflowRead]:
    if org_id is None:
        return []
    rows = await repository.list_workflows(org_id)
    return [WorkflowRead.model_validate(row) for row in rows]


@router.get("/{workflow_id}", response_model=WorkflowRead)
async def get_workflow(
    workflow_id: UUID,
    repository: WorkflowRepository = Depends(get_workflow_repository),
) -> WorkflowRead:
    workflow = await repository.get_workflow(workflow_id)
    if workflow is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow not found",
        )
    return WorkflowRead.model_validate(workflow)


@router.delete("/{workflow_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_workflow(
    workflow_id: UUID,
    repository: WorkflowRepository = Depends(get_workflow_repository),
) -> Response:
    deleted = await repository.delete_workflow(workflow_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow not found",
        )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{workflow_id}/index", status_code=status.HTTP_202_ACCEPTED)
async def index_workflow(workflow_id: UUID) -> dict[str, str]:
    execution_not_implemented()


@router.post("/{workflow_id}/run", status_code=status.HTTP_202_ACCEPTED)
async def run_workflow(workflow_id: UUID, payload: WorkflowRunRequest) -> dict[str, str]:
    execution_not_implemented()


@router.get("/{workflow_id}/report", response_model=WorkflowReportRead)
async def get_workflow_report(workflow_id: UUID) -> WorkflowReportRead:
    execution_not_implemented()
