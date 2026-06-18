from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from db.queries import WorkflowRepository
from models.schemas import WorkflowReportRead
from routes.workflows import get_workflow_repository

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/{report_id}", response_model=WorkflowReportRead)
async def get_report(
    report_id: UUID,
    repository: WorkflowRepository = Depends(get_workflow_repository),
) -> WorkflowReportRead:
    report = await repository.get_report(report_id)
    if report is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found",
        )
    return WorkflowReportRead.model_validate(report)
