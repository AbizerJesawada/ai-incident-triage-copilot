from datetime import datetime, timedelta, timezone

from app.sla_service import (
    calculate_sla_due_at,
    calculate_sla_status,
)


def test_critical_incident_is_due_in_15_minutes() -> None:
    started_at = datetime(2026, 9, 2, 10, 0, tzinfo=timezone.utc)

    due_at = calculate_sla_due_at(
        predicted_severity="critical",
        started_at=started_at,
    )

    assert due_at == started_at + timedelta(minutes=15)


def test_high_incident_is_due_in_one_hour() -> None:
    started_at = datetime(2026, 9, 2, 10, 0, tzinfo=timezone.utc)

    due_at = calculate_sla_due_at(
        predicted_severity="high",
        started_at=started_at,
    )

    assert due_at == started_at + timedelta(hours=1)


def test_incident_is_at_risk_near_deadline() -> None:
    due_at = datetime(2026, 9, 2, 10, 15, tzinfo=timezone.utc)
    now = datetime(2026, 9, 2, 10, 12, tzinfo=timezone.utc)

    sla_status = calculate_sla_status(
        sla_due_at=due_at,
        predicted_severity="critical",
        now=now,
    )

    assert sla_status == "at_risk"


def test_incident_is_breached_after_deadline() -> None:
    due_at = datetime(2026, 9, 2, 10, 15, tzinfo=timezone.utc)
    now = datetime(2026, 9, 2, 10, 16, tzinfo=timezone.utc)

    sla_status = calculate_sla_status(
        sla_due_at=due_at,
        predicted_severity="critical",
        now=now,
    )

    assert sla_status == "breached"