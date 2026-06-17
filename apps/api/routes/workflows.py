import asyncio
import logging
from typing import NoReturn
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status, BackgroundTasks

from core.config import Settings, get_settings
from db.queries import SupabaseWorkflowRepository, WorkflowRepository
from db.supabase_client import create_supabase_client
from models.schemas import WorkflowCreate, WorkflowRead, WorkflowReportRead, WorkflowRunRequest
from rag.embeddings import get_embedding_provider
from rag.parser import parse_document
from rag.chunker import chunk_text

logger = logging.getLogger(__name__)

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


async def index_workflow_documents(workflow_id: UUID, settings: Settings) -> None:
    try:
        client = create_supabase_client(settings)
    except Exception as e:
        logger.error(f"Failed to create supabase client during indexing: {e}")
        return

    try:
        # Update workflow status to "indexing"
        await asyncio.to_thread(
            lambda: client.table("workflows")
            .update({"status": "indexing"})
            .eq("id", str(workflow_id))
            .execute()
        )

        # Get all documents for this workflow
        docs_response = await asyncio.to_thread(
            lambda: client.table("documents")
            .select("*")
            .eq("workflow_id", str(workflow_id))
            .execute()
        )
        documents = docs_response.data or []

        # If there are no documents, set workflow to "ready" and return
        if not documents:
            await asyncio.to_thread(
                lambda: client.table("workflows")
                .update({"status": "ready"})
                .eq("id", str(workflow_id))
                .execute()
            )
            return

        embedding_provider = get_embedding_provider(settings)

        for doc in documents:
            doc_id = doc["id"]
            filename = doc["filename"]
            storage_path = doc["storage_path"]
            org_id = doc["org_id"]

            try:
                # Update document status to "parsing"
                await asyncio.to_thread(
                    lambda: client.table("documents")
                    .update({"status": "parsing"})
                    .eq("id", str(doc_id))
                    .execute()
                )

                # Download file content from storage
                content_bytes = await asyncio.to_thread(
                    client.storage.from_(settings.documents_bucket).download,
                    storage_path
                )

                # Parse document content
                parsed_doc = await asyncio.to_thread(parse_document, filename, content_bytes)

                # Chunk text
                chunks = await asyncio.to_thread(chunk_text, parsed_doc.text, parsed_doc.metadata)

                # Generate embeddings and save chunks
                if chunks:
                    texts = [c.content for c in chunks]
                    embeddings = await embedding_provider.embed_documents(texts)

                    # Clear existing chunks for this document
                    await asyncio.to_thread(
                        lambda: client.table("document_chunks")
                        .delete()
                        .eq("document_id", str(doc_id))
                        .execute()
                    )

                    # Insert chunks
                    chunk_records = []
                    for i, chunk in enumerate(chunks):
                        chunk_records.append({
                            "document_id": str(doc_id),
                            "org_id": str(org_id),
                            "workflow_id": str(workflow_id),
                            "chunk_index": chunk.index,
                            "content": chunk.content,
                            "metadata": chunk.metadata,
                            "embedding": embeddings[i],
                        })

                    await asyncio.to_thread(
                        lambda: client.table("document_chunks")
                        .insert(chunk_records)
                        .execute()
                    )

                # Update document status to "indexed"
                await asyncio.to_thread(
                    lambda: client.table("documents")
                    .update({"status": "indexed"})
                    .eq("id", str(doc_id))
                    .execute()
                )

            except Exception as doc_error:
                logger.error(f"Failed to index document {filename} (ID: {doc_id}): {doc_error}", exc_info=True)
                # Update document status to "failed"
                await asyncio.to_thread(
                    lambda: client.table("documents")
                    .update({"status": "failed"})
                    .eq("id", str(doc_id))
                    .execute()
                )
                raise doc_error

        # Update workflow status to "ready"
        await asyncio.to_thread(
            lambda: client.table("workflows")
            .update({"status": "ready"})
            .eq("id", str(workflow_id))
            .execute()
        )

    except Exception as e:
        logger.error(f"Error during indexing of workflow {workflow_id}: {e}", exc_info=True)
        try:
            await asyncio.to_thread(
                lambda: client.table("workflows")
                .update({
                    "status": "failed",
                    "error_message": str(e)
                })
                .eq("id", str(workflow_id))
                .execute()
            )
        except Exception as update_err:
            logger.error(f"Failed to update workflow {workflow_id} to failed status: {update_err}")


@router.post("/{workflow_id}/index", status_code=status.HTTP_202_ACCEPTED)
async def index_workflow(
    workflow_id: UUID,
    background_tasks: BackgroundTasks,
    settings: Settings = Depends(get_settings),
) -> dict[str, str]:
    # 1. Verify workflow exists
    try:
        client = create_supabase_client(settings)
    except RuntimeError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(error),
        ) from error

    workflow_response = await asyncio.to_thread(
        lambda: client.table("workflows").select("id").eq("id", str(workflow_id)).limit(1).execute()
    )
    if not workflow_response.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow not found",
        )

    # 2. Queue background task
    background_tasks.add_task(index_workflow_documents, workflow_id, settings)

    return {"status": "indexing", "message": "Workflow indexing started"}


@router.post("/{workflow_id}/run", status_code=status.HTTP_202_ACCEPTED)
async def run_workflow(workflow_id: UUID, payload: WorkflowRunRequest) -> dict[str, str]:
    execution_not_implemented()


@router.get("/{workflow_id}/report", response_model=WorkflowReportRead)
async def get_workflow_report(workflow_id: UUID) -> WorkflowReportRead:
    execution_not_implemented()
