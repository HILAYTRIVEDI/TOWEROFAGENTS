from typing import NoReturn
from uuid import UUID

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status

from models.schemas import DocumentRead

router = APIRouter(prefix="/workflows", tags=["documents"])


def not_implemented() -> NoReturn:
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Document storage and indexing are not implemented in the base scaffold",
    )


@router.post("/{workflow_id}/documents", response_model=DocumentRead)
async def upload_document(
    workflow_id: UUID,
    doc_type: str = Form(...),
    file: UploadFile = File(...),
) -> DocumentRead:
    not_implemented()

