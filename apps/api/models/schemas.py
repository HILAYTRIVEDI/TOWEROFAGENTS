from datetime import datetime
from enum import StrEnum
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class WorkflowStatus(StrEnum):
    DRAFT = "draft"
    INDEXING = "indexing"
    READY = "ready"
    RUNNING = "running"
    AWAITING_REVIEW = "awaiting_review"
    COMPLETED = "completed"
    FAILED = "failed"


class ReviewStatus(StrEnum):
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    REJECTED = "rejected"


class AgentInput(BaseModel):
    workflow_id: str
    org_id: str
    task: str
    context_chunks: list[dict[str, Any]] = Field(default_factory=list)
    artifacts: list[dict[str, Any]] = Field(default_factory=list)
    band_room_id: str | None = None
    # Populated by the executor for final-decision only: serialized prior findings.
    prior_findings: list[dict[str, Any]] = Field(default_factory=list)


class AgentFinding(BaseModel):
    agent_name: str
    finding_type: str
    severity: str
    title: str
    content: str
    evidence_chunk_ids: list[str] = Field(default_factory=list)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    requires_human_review: bool = False


class WorkflowCreate(BaseModel):
    org_id: UUID
    title: str = Field(min_length=1, max_length=200)
    user_request: str = Field(min_length=1, max_length=5000)
    template_slug: str | None = None
    band_room_id: str | None = Field(default=None, max_length=200)

    @field_validator("band_room_id", mode="before")
    @classmethod
    def empty_band_room_id_to_none(cls, value: str | None) -> str | None:
        if value is None:
            return None
        stripped = str(value).strip()
        return stripped or None


class WorkflowRead(BaseModel):
    id: UUID
    org_id: UUID
    title: str
    template_slug: str | None
    status: WorkflowStatus
    band_room_id: str | None = None
    created_at: datetime


class WorkflowRunRequest(BaseModel):
    force_reindex: bool = False


class WorkflowBandSessionRequest(BaseModel):
    band_room_id: str | None = Field(default=None, max_length=200)
    create_mock_session: bool = False

    @field_validator("band_room_id", mode="before")
    @classmethod
    def empty_band_room_id_to_none(cls, value: str | None) -> str | None:
        if value is None:
            return None
        stripped = str(value).strip()
        return stripped or None


class DocumentRead(BaseModel):
    id: UUID
    org_id: UUID
    workflow_id: UUID | None = None
    doc_type: str
    filename: str
    mime_type: str | None = None
    status: str
    created_at: datetime


class AgentDescriptor(BaseModel):
    slug: str
    name: str
    category: str
    description: str


class WorkflowTemplateRead(BaseModel):
    slug: str
    name: str
    depth: str
    agent_slugs: list[str]
    required_artifacts: list[str]


class WorkflowReportRead(BaseModel):
    id: UUID
    workflow_id: UUID
    recommendation: str
    summary: str
    fit_score: float | None = None
    strengths: list[str] = Field(default_factory=list)
    gaps: list[str] = Field(default_factory=list)
    interview_questions: list[str] = Field(default_factory=list)
    policy_note: str | None = None
    evidence_chunk_ids: list[str] = Field(default_factory=list)
    requires_human_review: bool = True
    report_payload: dict[str, Any] = Field(default_factory=dict)
    # Human-approval gate (HR candidate-screening only).
    review_status: ReviewStatus = ReviewStatus.PENDING_REVIEW
    reviewer_note: str | None = None
    reviewed_at: datetime | None = None


class WorkflowReviewRequest(BaseModel):
    decision: Literal["approve", "reject"]
    note: str | None = Field(default=None, max_length=2000)


class WorkflowReviewRead(BaseModel):
    report_id: UUID
    workflow_id: UUID
    review_status: ReviewStatus
    reviewer_note: str | None = None
    reviewed_at: datetime


class BandMessageRead(BaseModel):
    id: UUID
    workflow_id: UUID
    band_message_id: str | None = None
    band_room_id: str
    sender_type: str
    sender_ref: str | None = None
    content: str
    message_type: str
    raw_payload: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime


class AgentFindingRead(BaseModel):
    id: UUID
    workflow_id: UUID
    agent_slug: str
    finding_type: str
    severity: str
    title: str
    content: str
    evidence_chunk_ids: list[UUID] = Field(default_factory=list)
    confidence: float
    requires_human_review: bool
    raw_output: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime


class HealthResponse(BaseModel):
    service: str
    status: str
    environment: str
    integrations: dict[str, str]
