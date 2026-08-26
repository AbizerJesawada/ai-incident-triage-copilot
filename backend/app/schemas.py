from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


Severity = Literal[
    "unknown",
    "low",
    "medium",
    "high",
    "critical",
]

IncidentCategory = Literal[
    "application_error",
    "authentication",
    "database",
    "network",
]

IncidentStatus = Literal[
    "open",
    "investigating",
    "resolved",
]

ChangeEventType = Literal[
    "deployment",
    "configuration_change",
    "feature_flag",
]

ReviewDecision = Literal[
    "approved",
    "needs_investigation",
    "rejected",
]

RecommendationStatus = Literal[
    "pending",
    "approved",
    "rejected",
]

class IncidentCreate(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    description: str = Field(min_length=3)
    service_name: str = Field(min_length=2, max_length=100)
    severity: Severity = "unknown"
    source: str = Field(default="manual", max_length=50)


class IncidentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    description: str
    service_name: str
    severity: Severity
    status: IncidentStatus
    source: str
    predicted_category: str | None
    predicted_severity: Severity | None
    category_confidence: float | None
    severity_confidence: float | None
    triage_route: str | None
    model_tier: str | None
    human_review_required: bool
    triage_reason: str | None
    triaged_at: datetime | None
    created_at: datetime
    updated_at: datetime


class IncidentUpdate(BaseModel):
    severity: Severity | None = None
    status: IncidentStatus | None = None


class ChangeEventCreate(BaseModel):
    service_name: str = Field(min_length=2, max_length=100)
    event_type: ChangeEventType
    description: str = Field(min_length=3)
    reference_id: str | None = Field(
        default=None,
        max_length=100,
    )
    occurred_at: datetime | None = None


class ChangeEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    service_name: str
    event_type: ChangeEventType
    description: str
    reference_id: str | None
    occurred_at: datetime


class IncidentClassificationRequest(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    description: str = Field(min_length=3)
    service_name: str = Field(min_length=2, max_length=100)


class IncidentClassificationResponse(BaseModel):
    predicted_category: str
    predicted_severity: Severity
    category_confidence: float
    severity_confidence: float


class IncidentRoutingResponse(BaseModel):
    predicted_category: str
    predicted_severity: Severity
    category_confidence: float
    severity_confidence: float
    route: str
    model_tier: str
    human_review_required: bool
    reason: str


class IncidentReviewCreate(BaseModel):
    reviewer_name: str = Field(min_length=2, max_length=100)
    decision: ReviewDecision
    review_note: str | None = Field(
        default=None,
        max_length=2000,
    )
    actual_category: IncidentCategory | None = None
    actual_severity: Severity | None = None


class IncidentReviewResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    incident_id: UUID
    reviewer_name: str
    decision: ReviewDecision
    review_note: str | None
    actual_category: IncidentCategory | None
    actual_severity: Severity | None
    created_at: datetime

class FeedbackTrainingExample(BaseModel):
    incident_id: UUID
    review_id: UUID
    title: str
    description: str
    service_name: str
    category: IncidentCategory
    severity: Severity
    reviewer_name: str
    reviewed_at: datetime

class IncidentChangeCorrelationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    incident_id: UUID
    change_event_id: UUID
    time_difference_minutes: float
    correlation_score: float
    correlation_reason: str
    created_at: datetime

class IncidentCorrelationTimelineItem(BaseModel):
    correlation_id: UUID
    change_event_id: UUID
    event_type: ChangeEventType
    reference_id: str | None
    description: str
    occurred_at: datetime
    time_difference_minutes: float
    correlation_score: float
    correlation_reason: str

class RootCauseHypothesisResponse(BaseModel):
    incident_id: UUID
    hypothesis: str
    strongest_correlation_score: float | None

class RemediationRecommendationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    incident_id: UUID
    recommendation: str
    evidence: str
    source_type: str
    source_id: UUID | None
    status: RecommendationStatus
    reviewer_name: str | None
    review_note: str | None
    created_at: datetime
    reviewed_at: datetime | None


class RemediationRecommendationReview(BaseModel):
    status: Literal["approved", "rejected"]
    reviewer_name: str = Field(min_length=2, max_length=100)
    review_note: str | None = Field(
        default=None,
        max_length=2000,
    )

class BriefingEvidenceSource(BaseModel):
    source_type: str
    source_id: UUID
    reference_id: str | None
    description: str

class BriefingEvidenceValidation(BaseModel):
    mentioned_reference_ids: list[str]
    unsupported_reference_ids: list[str]

class IncidentBriefingResponse(BaseModel):
    incident_id: UUID
    briefing: str
    evidence_sources: list[BriefingEvidenceSource]
    evidence_validation: BriefingEvidenceValidation
    grounding_status: Literal["verified", "unverified"]