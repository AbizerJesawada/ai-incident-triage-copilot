from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import DateTime, String, Text
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