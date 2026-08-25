from datetime import timedelta

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models import (
    ChangeEvent,
    Incident,
    IncidentChangeCorrelation,
)

def calculate_correlation(
    change_event: ChangeEvent,
    time_difference_minutes: float,
) -> tuple[float, str]:
    score = 0.40
    reasons = ["The incident and change affect the same service."]

    if time_difference_minutes <= 5:
        score += 0.45
        reasons.append(
            "The change occurred within 5 minutes of the incident."
        )
    elif time_difference_minutes <= 15:
        score += 0.30
        reasons.append(
            "The change occurred within 15 minutes of the incident."
        )
    elif time_difference_minutes <= 30:
        score += 0.15
        reasons.append(
            "The change occurred within 30 minutes of the incident."
        )

    if change_event.event_type == "deployment":
        score += 0.10
        reasons.append("The change was a deployment.")
    elif change_event.event_type == "configuration_change":
        score += 0.08
        reasons.append("The change was a configuration change.")
    elif change_event.event_type == "feature_flag":
        score += 0.05
        reasons.append("The change was a feature flag change.")

    return min(round(score, 4), 0.99), " ".join(reasons)

def refresh_incident_change_correlations(
    db: Session,
    incident: Incident,
    window_minutes: int = 30,
) -> list[IncidentChangeCorrelation]:
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

    change_events = list(db.scalars(statement).all())

    db.execute(
        delete(IncidentChangeCorrelation).where(
            IncidentChangeCorrelation.incident_id == incident.id
        )
    )

    correlations = []

    for change_event in change_events:
        time_difference_minutes = abs(
            (
                incident.created_at - change_event.occurred_at
            ).total_seconds()
            / 60
        )

        correlation_score, correlation_reason = (
            calculate_correlation(
                change_event=change_event,
                time_difference_minutes=time_difference_minutes,
            )
        )

        correlation = IncidentChangeCorrelation(
            incident_id=incident.id,
            change_event_id=change_event.id,
            time_difference_minutes=round(
                time_difference_minutes,
                2,
            ),
            correlation_score=correlation_score,
            correlation_reason=correlation_reason,
        )

        db.add(correlation)
        correlations.append(correlation)

    db.flush()

    return correlations

def build_root_cause_hypothesis(
    incident: Incident,
    correlations: list[IncidentChangeCorrelation],
    change_events_by_id: dict,
) -> str:
    if not correlations:
        return (
            "No recent change events were found for the affected "
            "service. No temporal correlation hypothesis is available."
        )

    strongest_correlation = max(
        correlations,
        key=lambda correlation: correlation.correlation_score,
    )

    change_event = change_events_by_id[
        strongest_correlation.change_event_id
    ]

    reference = (
        change_event.reference_id
        or str(change_event.id)
    )

    return (
        "Possible correlation, not a confirmed root cause: "
        f"{change_event.event_type.replace('_', ' ')} "
        f"{reference} occurred "
        f"{strongest_correlation.time_difference_minutes} minutes "
        f"from the {incident.service_name} incident. "
        "Investigate this change first."
    )