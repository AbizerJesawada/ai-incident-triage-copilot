from datetime import datetime, timedelta, timezone


SLA_DURATIONS = {
    "critical": timedelta(minutes=15),
    "high": timedelta(hours=1),
    "medium": timedelta(hours=4),
    "low": timedelta(hours=24),
}


def calculate_sla_due_at(
    predicted_severity: str,
    started_at: datetime,
) -> datetime:
    duration = SLA_DURATIONS.get(
        predicted_severity,
        SLA_DURATIONS["medium"],
    )

    return started_at + duration


def calculate_sla_status(
    sla_due_at: datetime | None,
    predicted_severity: str,
    now: datetime | None = None,
) -> str:
    if sla_due_at is None:
        return "on_track"

    current_time = now or datetime.now(timezone.utc)

    if current_time >= sla_due_at:
        return "breached"

    duration = SLA_DURATIONS.get(
        predicted_severity,
        SLA_DURATIONS["medium"],
    )
    at_risk_time = sla_due_at - (duration / 4)

    if current_time >= at_risk_time:
        return "at_risk"

    return "on_track"