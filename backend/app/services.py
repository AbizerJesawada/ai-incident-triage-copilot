from datetime import timedelta
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import ChangeEvent, Incident


def find_related_change_events(
    db: Session,
    incident_id: UUID,
    window_minutes: int = 30,
) -> tuple[Incident | None, list[ChangeEvent]]:
    incident = db.get(Incident, incident_id)

    if incident is None:
        return None, []

    window_start = incident.created_at - timedelta(
        minutes=window_minutes,
    )
    window_end = incident.created_at + timedelta(
        minutes=window_minutes,
    )

    statement = (
        select(ChangeEvent)
        .where(ChangeEvent.service_name == incident.service_name)
        .where(ChangeEvent.occurred_at >= window_start)
        .where(ChangeEvent.occurred_at <= window_end)
        .order_by(ChangeEvent.occurred_at.desc())
    )

    events = list(db.scalars(statement).all())

    return incident, events