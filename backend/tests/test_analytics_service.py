from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

from app.analytics_service import build_incident_analytics


def make_incident(
    *,
    status: str,
    severity: str,
    sla_status: str,
    service_name: str,
    created_at: datetime,
    resolved_at: datetime | None = None,
) -> SimpleNamespace:
    return SimpleNamespace(
        status=status,
        predicted_severity=severity,
        severity="unknown",
        sla_status=sla_status,
        service_name=service_name,
        created_at=created_at,
        resolved_at=resolved_at,
    )


def test_build_incident_analytics_returns_operational_summary() -> None:
    started_at = datetime(2026, 9, 8, 10, 0, tzinfo=timezone.utc)

    incidents = [
        make_incident(
            status="open",
            severity="high",
            sla_status="on_track",
            service_name="payment-api",
            created_at=started_at,
        ),
        make_incident(
            status="open",
            severity="critical",
            sla_status="breached",
            service_name="payment-api",
            created_at=started_at,
        ),
        make_incident(
            status="resolved",
            severity="critical",
            sla_status="resolved",
            service_name="billing-api",
            created_at=started_at,
            resolved_at=started_at + timedelta(minutes=30),
        ),
        make_incident(
            status="resolved",
            severity="medium",
            sla_status="resolved",
            service_name="identity-api",
            created_at=started_at,
            resolved_at=started_at + timedelta(minutes=60),
        ),
    ]

    summary = build_incident_analytics(incidents)

    assert summary["total_incidents"] == 4
    assert summary["open_incidents"] == 2
    assert summary["resolved_incidents"] == 2
    assert summary["critical_incidents"] == 2
    assert summary["sla_on_track"] == 1
    assert summary["sla_at_risk"] == 0
    assert summary["sla_breached"] == 1
    assert summary["average_resolution_minutes"] == 45.0
    assert summary["incidents_by_service"] == {
        "payment-api": 2,
    }
    assert summary["incidents_by_severity"] == {
        "critical": 2,
        "high": 1,
        "medium": 1,
    }


def test_build_incident_analytics_handles_no_resolutions() -> None:
    started_at = datetime(2026, 9, 8, 10, 0, tzinfo=timezone.utc)

    summary = build_incident_analytics(
        [
            make_incident(
                status="open",
                severity="low",
                sla_status="on_track",
                service_name="notification-api",
                created_at=started_at,
            ),
        ],
    )

    assert summary["resolved_incidents"] == 0
    assert summary["average_resolution_minutes"] is None