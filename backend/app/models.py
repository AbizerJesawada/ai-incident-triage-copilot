from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, String, Text
from sqlalchemy import Uuid as SQLAlchemyUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Incident(Base):
    __tablename__ = "incidents"

    id: Mapped[UUID] = mapped_column(
        SQLAlchemyUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text)
    service_name: Mapped[str] = mapped_column(String(100))
    severity: Mapped[str] = mapped_column(
        String(20),
        default="unknown",
    )
    status: Mapped[str] = mapped_column(
        String(20),
        default="open",
    )
    source: Mapped[str] = mapped_column(
        String(50),
        default="manual",
    )
    predicted_category: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )
    predicted_severity: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )
    category_confidence: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )
    severity_confidence: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )
    triage_route: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )
    model_tier: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )
    human_review_required: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
    )
    triage_reason: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    triaged_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )


class ChangeEvent(Base):
    __tablename__ = "change_events"

    id: Mapped[UUID] = mapped_column(
        SQLAlchemyUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    service_name: Mapped[str] = mapped_column(String(100))
    event_type: Mapped[str] = mapped_column(String(30))
    description: Mapped[str] = mapped_column(Text)
    reference_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )

class IncidentChangeCorrelation(Base):
    __tablename__ = "incident_change_correlations"

    id: Mapped[UUID] = mapped_column(
        SQLAlchemyUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    incident_id: Mapped[UUID] = mapped_column(
        SQLAlchemyUUID(as_uuid=True),
        ForeignKey("incidents.id"),
    )
    change_event_id: Mapped[UUID] = mapped_column(
        SQLAlchemyUUID(as_uuid=True),
        ForeignKey("change_events.id"),
    )
    time_difference_minutes: Mapped[float] = mapped_column(Float)
    correlation_score: Mapped[float] = mapped_column(Float)
    correlation_reason: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )

class RemediationRecommendation(Base):
    __tablename__ = "remediation_recommendations"

    id: Mapped[UUID] = mapped_column(
        SQLAlchemyUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    incident_id: Mapped[UUID] = mapped_column(
        SQLAlchemyUUID(as_uuid=True),
        ForeignKey("incidents.id"),
    )
    recommendation: Mapped[str] = mapped_column(Text)
    evidence: Mapped[str] = mapped_column(Text)
    source_type: Mapped[str] = mapped_column(String(50))
    source_id: Mapped[UUID | None] = mapped_column(
        SQLAlchemyUUID(as_uuid=True),
        nullable=True,
    )
    status: Mapped[str] = mapped_column(
        String(30),
        default="pending",
    )
    reviewer_name: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    review_note: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

class LLMGenerationLog(Base):
    __tablename__ = "llm_generation_logs"

    id: Mapped[UUID] = mapped_column(
        SQLAlchemyUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    incident_id: Mapped[UUID] = mapped_column(
        SQLAlchemyUUID(as_uuid=True),
        ForeignKey("incidents.id"),
    )
    model_name: Mapped[str] = mapped_column(String(100))
    grounding_status: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
    )
    status: Mapped[str] = mapped_column(String(30))
    latency_ms: Mapped[float] = mapped_column(Float)
    prompt_token_count: Mapped[int | None] = mapped_column(
        nullable=True,
    )
    response_token_count: Mapped[int | None] = mapped_column(
        nullable=True,
    )
    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )

class EngineerNotification(Base):
    __tablename__ = "engineer_notifications"

    id: Mapped[UUID] = mapped_column(
        SQLAlchemyUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    incident_id: Mapped[UUID] = mapped_column(
        SQLAlchemyUUID(as_uuid=True),
        ForeignKey("incidents.id"),
    )
    notification_type: Mapped[str] = mapped_column(
        String(50),
    )
    message: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(
        String(20),
        default="pending",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
    read_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    acknowledged_by: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    acknowledged_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    slack_channel_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    slack_message_ts: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

class IncidentReview(Base):
    __tablename__ = "incident_reviews"

    id: Mapped[UUID] = mapped_column(
        SQLAlchemyUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    incident_id: Mapped[UUID] = mapped_column(
        SQLAlchemyUUID(as_uuid=True),
        ForeignKey("incidents.id"),
    )
    reviewer_name: Mapped[str] = mapped_column(String(100))
    decision: Mapped[str] = mapped_column(String(30))
    review_note: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    actual_category: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )
    actual_severity: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )