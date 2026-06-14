import logging
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status

from core.config import Settings, get_settings
from db.documents import DocumentRepository, SupabaseDocumentRepository, WorkflowNotFoundError
from db.supabase_client import create_supabase_client
from models.schemas import DocumentRead

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/workflows", tags=["documents"])

# Mirrors the doc_type check constraint on public.documents.
ALLOWED_DOC_TYPES = {"resume", "jd", "policy", "crm", "code", "other"}


def get_document_repository(
    settings: Settings = Depends(get_settings),
) -> DocumentRepository:
    try:
        client = create_supabase_client(settings)
    except RuntimeError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(error),
        ) from error
    return SupabaseDocumentRepository(client, settings.documents_bucket)


@router.post(
    "/{workflow_id}/documents",
    response_model=DocumentRead,
    status_code=status.HTTP_201_CREATED,
)
async def upload_document(
    workflow_id: UUID,
    doc_type: str = Form(...),
    file: UploadFile = File(...),
    settings: Settings = Depends(get_settings),
    repository: DocumentRepository = Depends(get_document_repository),
) -> DocumentRead:
    if doc_type not in ALLOWED_DOC_TYPES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"doc_type must be one of {sorted(ALLOWED_DOC_TYPES)}",
        )

    content = await file.read()
    if not content:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Uploaded file is empty",
        )
    if len(content) > settings.max_upload_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds the {settings.max_upload_bytes} byte upload limit",
        )

    try:
        row = await repository.store_document(
            workflow_id=workflow_id,
            doc_type=doc_type,
            filename=file.filename or "upload",
            content=content,
            mime_type=file.content_type,
        )
    except WorkflowNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow not found",
        ) from error

    # Confidential content: log only non-sensitive identifiers, never bytes.
    logger.info("Stored document %s for workflow %s", row.get("id"), workflow_id)
    return DocumentRead.model_validate(row)
