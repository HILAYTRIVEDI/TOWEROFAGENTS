from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class WorkflowStatus(StrEnum):
    DRAFT = "draft"
    INDEXING = "indexing"
    READY = "ready"
    RUNNING = "running"
    AWAITING_REVIEW = "awaiting_review"
    COMPLETED = "completed"
    FAILED = "failed"


class AgentInput(BaseModel):
    workflow_id: str
    org_id: str
    task: str
    context_chunks: list[dict[str, Any]] = Field(default_factory=list)
    artifacts: list[dict[str, Any]] = Field(default_factory=list)
    band_room_id: str | None = None


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


class DocumentRead(BaseModel):
    id: UUID
    workflow_id: UUID
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


class HealthResponse(BaseModel):
    service: str
    status: str
    environment: str
    integrations: dict[str, str]

