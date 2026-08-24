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