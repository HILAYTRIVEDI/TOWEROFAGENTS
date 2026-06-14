from typing import NoReturn
from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from models.schemas import WorkflowCreate, WorkflowRead, WorkflowReportRead, WorkflowRunRequest

router = APIRouter(prefix="/workflows", tags=["workflows"])


def not_implemented() -> NoReturn:
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Workflow persistence and execution are not implemented in the base scaffold",
    )


@router.post("", response_model=WorkflowRead)
async def create_workflow(payload: WorkflowCreate) -> WorkflowRead:
    not_implemented()


@router.get("", response_model=list[WorkflowRead])
async def list_workflows() -> list[WorkflowRead]:
    not_implemented()


@router.get("/{workflow_id}", response_model=WorkflowRead)
async def get_workflow(workflow_id: UUID) -> WorkflowRead:
    not_implemented()


@router.post("/{workflow_id}/index", status_code=status.HTTP_202_ACCEPTED)
async def index_workflow(workflow_id: UUID) -> dict[str, str]:
    not_implemented()


@router.post("/{workflow_id}/run", status_code=status.HTTP_202_ACCEPTED)
async def run_workflow(workflow_id: UUID, payload: WorkflowRunRequest) -> dict[str, str]:
    not_implemented()


@router.get("/{workflow_id}/report", response_model=WorkflowReportRead)
async def get_workflow_report(workflow_id: UUID) -> WorkflowReportRead:
    not_implemented()

