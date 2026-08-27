from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import EngineerNotification, Incident


def create_review_notification_if_needed(
    db: Session,
    incident: Incident,
) -> EngineerNotification | None:
    if not incident.human_review_required:
        return None

    existing_notification = db.scalar(
        select(EngineerNotification)
        .where(EngineerNotification.incident_id == incident.id)
        .where(
            EngineerNotification.notification_type
            == "human_review_required"
        )
        .where(EngineerNotification.status == "pending")
    )

    if existing_notification is not None:
        return existing_notification

    notification = EngineerNotification(
        incident_id=incident.id,
        notification_type="human_review_required",
        message=(
            f"Incident '{incident.title}' for "
            f"{incident.service_name} requires engineer review. "
            f"Reason: {incident.triage_reason}"
        ),
    )

    db.add(notification)

    return notification