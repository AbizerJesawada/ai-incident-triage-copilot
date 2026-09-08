from collections import Counter
from datetime import datetime
from typing import Iterable

from app.models import Incident


def build_incident_analytics(
    incidents: Iterable[Incident],
) -> dict[str, object]:
    incident_list = list(incidents)

    open_incidents = [
        incident
        for incident in incident_list
        if incident.status != "resolved"
    ]

    resolved_incidents = [
        incident
        for incident in incident_list
        if incident.status == "resolved"
    ]

    sla_status_counts = Counter(
        incident.sla_status or "on_track"
        for incident in open_incidents
    )

    severity_counts = Counter(
        incident.predicted_severity
        or incident.severity
        or "unknown"
        for incident in incident_list
    )

    service_counts = Counter(
        incident.service_name
        for incident in open_incidents
    )

    resolution_minutes = [
        (
            incident.resolved_at - incident.created_at
        ).total_seconds() / 60
        for incident in resolved_incidents
        if incident.resolved_at is not None
        and incident.created_at is not None
    ]

    average_resolution_minutes = (
        round(
            sum(resolution_minutes) / len(resolution_minutes),
            2,
        )
        if resolution_minutes
        else None
    )

    return {
        "total_incidents": len(incident_list),
        "open_incidents": len(open_incidents),
        "resolved_incidents": len(resolved_incidents),
        "critical_incidents": severity_counts["critical"],
        "sla_on_track": sla_status_counts["on_track"],
        "sla_at_risk": sla_status_counts["at_risk"],
        "sla_breached": sla_status_counts["breached"],
        "average_resolution_minutes": average_resolution_minutes,
        "incidents_by_service": dict(
            service_counts.most_common(),
        ),
        "incidents_by_severity": dict(
            severity_counts.most_common(),
        ),
    }