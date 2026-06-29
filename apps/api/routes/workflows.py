import logging
from collections import Counter
from datetime import UTC, datetime
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

from band.client import create_band_client
from band.room_orchestrator import RoomOrchestrator
from band.run_audit import WorkflowRoomAuditor
from core.config import Settings, get_settings
from db.documents import DocumentRepository
from db.queries import SupabaseWorkflowRepository, WorkflowRepository
from db.supabase_client import create_supabase_client
from models.schemas import (
    AgentFindingRead,
    BandMessageRead,
    ReviewStatus,
    WorkflowBandSessionRequest,
    WorkflowCreate,
    WorkflowRead,
    WorkflowReportRead,
    WorkflowReviewRead,
    WorkflowReviewRequest,
    WorkflowRunRequest,
)
from rag.embeddings import EmbeddingProvider
from rag.ingestion import run_ingestion_safely
from rag.retriever import Retriever, SupabaseChunkSearchClient
from routes.documents import get_document_repository, get_embedding_provider_dep
from workflows.executor import WorkflowExecutor
from workflows.templates import get_template

router = APIRouter(prefix="/workflows", tags=["workflows"])
logger = logging.getLogger(__name__)

_TARGETED_CONTEXT_QUERIES = {
    "resume": "Resume evidence: candidate work history, skills, projects, experience, education, and qualifications.",
    "jd": "Job description evidence: role requirements, responsibilities, required skills, preferred qualifications, and evaluation criteria.",
    "contract": "contract terms liability indemnity termination IP ownership",
    "security_documentation": "data security certifications SOC 2 ISO 27001 data residency breach",
    "pricing": "pricing total cost payment terms recurring fees discounts",
    "vendor_profile": "vendor company profile business need services provided references",
}


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
        return Retriever(
            SupabaseChunkSearchClient(create_supabase_client(settings)),
            dimensions=settings.embedding_dimensions,
        )
    except RuntimeError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(error),
        ) from error


async def _retrieve_workflow_context(
    *,
    workflow: dict,
    artifacts: list[dict],
    embedding_provider: EmbeddingProvider,
    retriever: Retriever,
) -> tuple[list[dict], list[str]]:
    base_query = workflow.get("user_request") or workflow["title"]
    artifact_types = {str(artifact.get("doc_type", "")) for artifact in artifacts}
    queries = [base_query]
    if "resume" in artifact_types:
        queries.append(f"{base_query}\n{_TARGETED_CONTEXT_QUERIES['resume']}")
    if artifact_types & {"jd", "job_description"}:
        queries.append(f"{base_query}\n{_TARGETED_CONTEXT_QUERIES['jd']}")
    queued_queries = set(queries)
    for doc_type in sorted(artifact_types & _TARGETED_CONTEXT_QUERIES.keys()):
        query = f"{base_query}\n{_TARGETED_CONTEXT_QUERIES[doc_type]}"
        if query not in queued_queries:
            queries.append(query)
            queued_queries.add(query)

    chunks_by_key: dict[str, dict] = {}
    for query in queries:
        query_embedding = await embedding_provider.embed_query(query)
        for chunk in await retriever.search(
            query_embedding=query_embedding,
            org_id=str(workflow["org_id"]),
            workflow_id=str(workflow["id"]),
        ):
            key = str(chunk.get("id") or f"{chunk.get('document_id')}:{chunk.get('content')}")
            chunks_by_key.setdefault(key, chunk)
    return list(chunks_by_key.values()), queries


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


@router.post("/{workflow_id}/band-session", response_model=WorkflowRead)
async def set_workflow_band_session(
    workflow_id: UUID,
    payload: WorkflowBandSessionRequest,
    settings: Settings = Depends(get_settings),
    repository: WorkflowRepository = Depends(get_workflow_repository),
) -> WorkflowRead:
    workflow = await repository.get_workflow(workflow_id)
    if workflow is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow not found",
        )

    band_room_id = (payload.band_room_id or "").strip()
    if not band_room_id and payload.create_mock_session:
        if settings.band_mode == "sdk":
            if not settings.band_api_key or not settings.band_agent_id:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail=(
                        "Band SDK is not configured: BAND_API_KEY and BAND_AGENT_ID must be set. "
                        "Set those variables, or paste an existing room ID instead."
                    ),
                )
        elif settings.band_mode != "mock":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported BAND_MODE: {settings.band_mode!r}. Use 'mock' or 'sdk'.",
            )
        template = get_template(workflow["template_slug"]) if workflow.get("template_slug") else None
        agent_names = template.agent_slugs if template else []
        band_room_id = await RoomOrchestrator(create_band_client(settings)).open_workflow_room(
            title=f"ATower discussion: {workflow['title']}",
            goal=workflow.get("user_request") or workflow["title"],
            agent_names=agent_names,
        )

    if not band_room_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Provide a Band room ID or request a mock session.",
        )

    updated = await repository.update_workflow_band_room(workflow_id, band_room_id)
    if updated is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow not found",
        )
    return WorkflowRead.model_validate(updated)


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
        retrieval_queries = []
        retrieval_error = None
        try:
            retrieved_context, retrieval_queries = await _retrieve_workflow_context(
                workflow=workflow,
                artifacts=artifacts,
                embedding_provider=embedding_provider,
                retriever=retriever,
            )
        except RuntimeError as error:
            retrieval_error = str(error)
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
        result["payload"]["retrieval_queries"] = retrieval_queries
        if retrieval_error:
            result["payload"]["retrieval_error"] = retrieval_error
        band_room_id = workflow.get("band_room_id") or settings.band_default_room_id
        ordered_findings = result.get("ordered_findings", [])
        result["payload"]["band_audit"] = {
            "room_id": band_room_id,
            "message_count": 0,
            "modes": {},
        }
        saved = await repository.save_workflow_report(
            workflow=workflow,
            report=result["report"],
            payload=result["payload"],
        )
        for slug, finding in ordered_findings:
            try:
                await repository.save_agent_finding(
                    {
                        "org_id": str(workflow["org_id"]),
                        "workflow_id": str(workflow["id"]),
                        "agent_slug": slug,
                        "finding_type": finding.finding_type,
                        "severity": finding.severity,
                        "title": finding.title,
                        "content": finding.content,
                        "evidence_chunk_ids": finding.evidence_chunk_ids,
                        "confidence": finding.confidence,
                        "requires_human_review": finding.requires_human_review,
                        "raw_output": finding.model_dump(mode="json"),
                    }
                )
            except Exception as error:  # noqa: BLE001
                logger.warning(
                    "Agent finding persistence failed for workflow %s agent %s: %s",
                    workflow_id,
                    slug,
                    error,
                )
        if band_room_id and ordered_findings:
            try:
                posted_messages = await WorkflowRoomAuditor(settings).post_discussion(
                    room_id=band_room_id,
                    ordered_findings=ordered_findings,
                )
                modes = Counter(message.mode for message in posted_messages)
                result["payload"]["band_audit"] = {
                    "room_id": band_room_id,
                    "message_count": len(posted_messages),
                    "modes": dict(modes),
                }
                for message in posted_messages:
                    await repository.save_band_message(
                        {
                            "org_id": str(workflow["org_id"]),
                            "workflow_id": str(workflow["id"]),
                            "band_message_id": message.band_message_id,
                            "band_room_id": band_room_id,
                            "sender_type": "agent",
                            "sender_ref": message.sender_slug,
                            "content": message.content,
                            "message_type": "message",
                            "raw_payload": message.raw_payload
                            | {
                                "mentions": message.mentions,
                                "sender_agent_id": message.sender_agent_id,
                            },
                        }
                    )
                saved = await repository.save_workflow_report(
                    workflow=workflow,
                    report=result["report"],
                    payload=result["payload"],
                )
            except Exception as error:  # noqa: BLE001
                logger.warning("Band audit failed for workflow %s: %s", workflow_id, error)
                result["payload"]["band_audit"] = {
                    "room_id": band_room_id,
                    "message_count": 0,
                    "modes": {"failed": len(ordered_findings)},
                    "error": str(error),
                }
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


@router.get("/{workflow_id}/messages", response_model=list[BandMessageRead])
async def get_workflow_messages(
    workflow_id: UUID,
    repository: WorkflowRepository = Depends(get_workflow_repository),
) -> list[BandMessageRead]:
    rows = await repository.get_band_messages(workflow_id)
    return [BandMessageRead.model_validate(row) for row in rows]


@router.get("/{workflow_id}/findings", response_model=list[AgentFindingRead])
async def get_workflow_findings(
    workflow_id: UUID,
    repository: WorkflowRepository = Depends(get_workflow_repository),
) -> list[AgentFindingRead]:
    rows = await repository.get_agent_findings(workflow_id)
    return [AgentFindingRead.model_validate(row) for row in rows]


@router.post("/{workflow_id}/review", response_model=WorkflowReviewRead)
async def submit_workflow_review(
    workflow_id: UUID,
    payload: WorkflowReviewRequest,
    repository: WorkflowRepository = Depends(get_workflow_repository),
) -> WorkflowReviewRead:
    report = await repository.get_workflow_report(workflow_id)
    if report is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow report not found",
        )

    if not report.get("requires_human_review"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This report does not require human review",
        )

    current_status = report.get("review_status", ReviewStatus.PENDING_REVIEW)
    if current_status != ReviewStatus.PENDING_REVIEW:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Report has already been reviewed (current status: {current_status})",
        )

    review_status = (
        ReviewStatus.APPROVED if payload.decision == "approve" else ReviewStatus.REJECTED
    )
    reviewed_at = datetime.now(UTC)
    report_id = UUID(str(report["id"]))

    await repository.submit_workflow_review(
        report_id=report_id,
        review_status=review_status.value,
        note=payload.note,
        reviewed_at=reviewed_at,
    )

    return WorkflowReviewRead(
        report_id=report_id,
        workflow_id=workflow_id,
        review_status=review_status,
        reviewer_note=payload.note,
        reviewed_at=reviewed_at,
    )
