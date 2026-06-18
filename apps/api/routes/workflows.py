from uuid import UUID

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    HTTPException,
    Query,
    Response,
    status,
)

from core.config import Settings, get_settings
from db.documents import DocumentRepository
from db.queries import SupabaseWorkflowRepository, WorkflowRepository
from db.supabase_client import create_supabase_client
from models.schemas import WorkflowCreate, WorkflowRead, WorkflowReportRead, WorkflowRunRequest
from rag.embeddings import EmbeddingProvider
from rag.ingestion import run_ingestion_safely
from rag.retriever import Retriever, SupabaseChunkSearchClient
from routes.documents import get_document_repository, get_embedding_provider_dep
from workflows.executor import WorkflowExecutor
from workflows.templates import get_template

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


def get_retriever(settings: Settings = Depends(get_settings)) -> Retriever:
    try:
        return Retriever(SupabaseChunkSearchClient(create_supabase_client(settings)))
    except RuntimeError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(error),
        ) from error


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
async def index_workflow(
    workflow_id: UUID,
    background_tasks: BackgroundTasks,
    repository: WorkflowRepository = Depends(get_workflow_repository),
    documents: DocumentRepository = Depends(get_document_repository),
    embedding_provider: EmbeddingProvider = Depends(get_embedding_provider_dep),
) -> dict[str, str]:
    workflow = await repository.get_workflow(workflow_id)
    if workflow is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow not found",
        )

    # Re-index every document attached to this workflow. Ingestion replaces a
    # document's existing chunks, so this is safe to call repeatedly.
    rows = await documents.list_workflow_documents(workflow_id)
    for row in rows:
        background_tasks.add_task(
            run_ingestion_safely,
            row,
            store=documents,
            embedding_provider=embedding_provider,
        )

    return {
        "status": "accepted",
        "workflow_id": str(workflow_id),
        "documents": str(len(rows)),
    }


@router.post("/{workflow_id}/run", status_code=status.HTTP_202_ACCEPTED)
async def run_workflow(
    workflow_id: UUID,
    payload: WorkflowRunRequest,
    settings: Settings = Depends(get_settings),
    repository: WorkflowRepository = Depends(get_workflow_repository),
    documents: DocumentRepository = Depends(get_document_repository),
    embedding_provider: EmbeddingProvider = Depends(get_embedding_provider_dep),
    retriever: Retriever = Depends(get_retriever),
) -> dict[str, str]:
    workflow = await repository.get_workflow(workflow_id)
    if workflow is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow not found",
        )

    await repository.update_workflow_status(workflow_id, "running")
    try:
        artifacts = await documents.list_organization_documents(UUID(str(workflow["org_id"])))
        try:
            template = get_template(workflow["template_slug"]) if workflow.get("template_slug") else None
        except ValueError:
            template = None
        selected_agents = template.agent_slugs if template else []
        retrieved_context = []
        retrieval_error = None
        try:
            query_embedding = await embedding_provider.embed_query(
                workflow.get("user_request") or workflow["title"]
            )
        except RuntimeError as error:
            retrieval_error = str(error)
        else:
            retrieved_context = await retriever.search(
                query_embedding=query_embedding,
                org_id=str(workflow["org_id"]),
                workflow_id=str(workflow["id"]),
            )
        result = await WorkflowExecutor(settings=settings).run(
            {
                "workflow_id": str(workflow["id"]),
                "org_id": str(workflow["org_id"]),
                "user_request": workflow.get("user_request") or "",
                "template_slug": workflow.get("template_slug"),
                "band_room_id": workflow.get("band_room_id"),
                "artifacts": artifacts,
                "selected_agents": selected_agents,
                "retrieved_context": retrieved_context,
                "agent_findings": [],
                "policy_verdict": None,
                "final_report": None,
                "status": "running",
            }
        )
        result["payload"]["force_reindex_requested"] = payload.force_reindex
        if retrieval_error:
            result["payload"]["retrieval_error"] = retrieval_error
        saved = await repository.save_workflow_report(
            workflow=workflow,
            report=result["report"],
            payload=result["payload"],
        )
        await repository.update_workflow_status(workflow_id, "awaiting_review")
    except Exception:
        await repository.update_workflow_status(workflow_id, "failed")
        raise

    return {
        "status": "awaiting_review",
        "workflow_id": str(workflow_id),
        "report_id": str(saved["id"]),
    }


@router.get("/{workflow_id}/report", response_model=WorkflowReportRead)
async def get_workflow_report(
    workflow_id: UUID,
    repository: WorkflowRepository = Depends(get_workflow_repository),
) -> WorkflowReportRead:
    report = await repository.get_workflow_report(workflow_id)
    if report is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow report not found",
        )
    return WorkflowReportRead.model_validate(report)
