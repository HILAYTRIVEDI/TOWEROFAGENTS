from uuid import UUID
import asyncio

from fastapi import APIRouter, Depends, HTTPException, status

from core.config import Settings, get_settings
from db.supabase_client import create_supabase_client
from models.schemas import WorkflowReportRead

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/{report_id}", response_model=WorkflowReportRead)
async def get_report(
    report_id: UUID,
    settings: Settings = Depends(get_settings),
) -> WorkflowReportRead:
    try:
        client = create_supabase_client(settings)
    except RuntimeError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(error),
        ) from error

    response = await asyncio.to_thread(
        lambda: client.table("workflow_reports")
        .select("*")
        .eq("id", str(report_id))
        .limit(1)
        .execute()
    )

    if not response.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found",
        )

    return WorkflowReportRead.model_validate(response.data[0])


