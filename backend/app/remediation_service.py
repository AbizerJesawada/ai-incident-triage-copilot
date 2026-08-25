from app.models import (
    ChangeEvent,
    Incident,
    IncidentChangeCorrelation,
)


MIN_RECOMMENDATION_SCORE = 0.70


def build_recommendation_text(
    change_event: ChangeEvent,
) -> str:
    reference = change_event.reference_id or str(change_event.id)

    if change_event.event_type == "deployment":
        return (
            f"Review deployment {reference}, compare its changes "
            "with the previous version, and consider rollback only "
            "after engineer verification."
        )

    if change_event.event_type == "configuration_change":
        return (
            f"Review configuration change {reference}, verify the "
            "current settings, and restore the previous configuration "
            "only after engineer verification."
        )

    return (
        f"Review feature flag change {reference}, verify its current "
        "state, and consider disabling the flag only after engineer "
        "verification."
    )


def generate_remediation_recommendations(
    incident: Incident,
    correlations: list[IncidentChangeCorrelation],
    change_events_by_id: dict,
) -> list[dict[str, object]]:
    possible_causes = [
        correlation
        for correlation in correlations
        if correlation.correlation_score >= MIN_RECOMMENDATION_SCORE
        and change_events_by_id[
            correlation.change_event_id
        ].occurred_at <= incident.created_at
    ]

    if not possible_causes:
        return []

    strongest_correlation = max(
        possible_causes,
        key=lambda correlation: correlation.correlation_score,
    )

    change_event = change_events_by_id[
        strongest_correlation.change_event_id
    ]

    evidence = (
        f"{change_event.event_type.replace('_', ' ').title()} "
        f"{change_event.reference_id or change_event.id} "
        f"occurred {strongest_correlation.time_difference_minutes} "
        f"minutes before the {incident.service_name} incident. "
        f"{strongest_correlation.correlation_reason}"
    )

    return [
        {
            "recommendation": build_recommendation_text(
                change_event
            ),
            "evidence": evidence,
            "source_type": "change_event",
            "source_id": change_event.id,
        }
    ]