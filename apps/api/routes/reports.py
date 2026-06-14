from typing import NoReturn
from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from models.schemas import WorkflowReportRead

router = APIRouter(prefix="/reports", tags=["reports"])


def not_implemented() -> NoReturn:
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Report persistence is not implemented in the base scaffold",
    )


@router.get("/{report_id}", response_model=WorkflowReportRead)
async def get_report(report_id: UUID) -> WorkflowReportRead:
    not_implemented()

