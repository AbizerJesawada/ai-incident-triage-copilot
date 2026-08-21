CONFIDENCE_THRESHOLD = 0.70


def route_incident(
    predicted_severity: str,
    category_confidence: float,
    severity_confidence: float,
) -> dict[str, object]:
    lowest_confidence = min(
        category_confidence,
        severity_confidence,
    )

    if predicted_severity == "critical":
        return {
            "route": "critical_escalation",
            "model_tier": "strong",
            "human_review_required": True,
            "reason": (
                "The incident is predicted as critical, so it requires "
                "strong analysis and mandatory engineer review."
            ),
        }

    if lowest_confidence < CONFIDENCE_THRESHOLD:
        return {
            "route": "uncertain_escalation",
            "model_tier": "strong",
            "human_review_required": True,
            "reason": (
                "The ML model confidence is below 0.70, so the prediction "
                "requires stronger analysis and engineer review."
            ),
        }

    if predicted_severity == "high":
        return {
            "route": "high_priority_review",
            "model_tier": "strong",
            "human_review_required": True,
            "reason": (
                "The incident is predicted as high severity, so it requires "
                "priority analysis and engineer review."
            ),
        }

    return {
        "route": "standard_triage",
        "model_tier": "standard",
        "human_review_required": False,
        "reason": (
            "The incident has non-high severity and sufficient ML confidence, "
            "so it can use the standard triage workflow."
        ),
    }