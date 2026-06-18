import logging
from uuid import UUID

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    Form,
    HTTPException,
    UploadFile,
    status,
)

from core.config import Settings, get_settings
from db.documents import (
    DocumentRepository,
    OrganizationNotFoundError,
    SupabaseDocumentRepository,
    WorkflowNotFoundError,
)
from db.supabase_client import create_supabase_client
from models.schemas import DocumentRead
from rag.embeddings import EmbeddingProvider, get_embedding_provider
from rag.ingestion import run_ingestion_safely

logger = logging.getLogger(__name__)

router = APIRouter(tags=["documents"])

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


def get_embedding_provider_dep(
    settings: Settings = Depends(get_settings),
) -> EmbeddingProvider:
    return get_embedding_provider(settings)


@router.post(
    "/workflows/{workflow_id}/documents",
    response_model=DocumentRead,
    status_code=status.HTTP_201_CREATED,
)
async def upload_document(
    workflow_id: UUID,
    background_tasks: BackgroundTasks,
    doc_type: str = Form(...),
    file: UploadFile = File(...),
    settings: Settings = Depends(get_settings),
    repository: DocumentRepository = Depends(get_document_repository),
    embedding_provider: EmbeddingProvider = Depends(get_embedding_provider_dep),
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

    # Parse -> chunk -> embed -> persist scoped chunks once the response is sent.
    background_tasks.add_task(
        run_ingestion_safely,
        row,
        store=repository,
        embedding_provider=embedding_provider,
    )
    return DocumentRead.model_validate(row)


@router.get("/knowledge/{org_id}/documents", response_model=list[DocumentRead])
@router.get("/organizations/{org_id}/documents", response_model=list[DocumentRead])
async def list_organization_documents(
    org_id: UUID,
    repository: DocumentRepository = Depends(get_document_repository),
) -> list[DocumentRead]:
    rows = await repository.list_organization_documents(org_id)
    return [DocumentRead.model_validate(row) for row in rows]


@router.post(
    "/knowledge/{org_id}/documents",
    response_model=DocumentRead,
    status_code=status.HTTP_201_CREATED,
)
@router.post(
    "/organizations/{org_id}/documents",
    response_model=DocumentRead,
    status_code=status.HTTP_201_CREATED,
)
async def upload_organization_document(
    org_id: UUID,
    background_tasks: BackgroundTasks,
    doc_type: str = Form(...),
    file: UploadFile = File(...),
    settings: Settings = Depends(get_settings),
    repository: DocumentRepository = Depends(get_document_repository),
    embedding_provider: EmbeddingProvider = Depends(get_embedding_provider_dep),
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
        row = await repository.store_organization_document(
            org_id=org_id,
            doc_type=doc_type,
            filename=file.filename or "upload",
            content=content,
            mime_type=file.content_type,
        )
    except OrganizationNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found",
        ) from error

    logger.info("Stored organization document %s for org %s", row.get("id"), org_id)

    # Shared-KB docs have workflow_id=None; ingestion stores NULL-scoped chunks so
    # they're retrievable across every workflow in the organization.
    background_tasks.add_task(
        run_ingestion_safely,
        row,
        store=repository,
        embedding_provider=embedding_provider,
    )
    return DocumentRead.model_validate(row)
