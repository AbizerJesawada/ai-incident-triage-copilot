from app.escalation_router import route_incident


def test_critical_incident_requires_engineer_review() -> None:
    result = route_incident(
        predicted_severity="critical",
        category_confidence=0.90,
        severity_confidence=0.90,
    )

    assert result["route"] == "critical_escalation"
    assert result["human_review_required"] is True


def test_confident_low_incident_uses_standard_triage() -> None:
    result = route_incident(
        predicted_severity="low",
        category_confidence=0.90,
        severity_confidence=0.85,
    )

    assert result["route"] == "standard_triage"
    assert result["human_review_required"] is False