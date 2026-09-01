from datetime import datetime, timezone

from app.escalation_router import route_incident
from app.ml_classifier import predict_incident
from app.severity_guardrail_service import (
    apply_severity_guardrail,
)


def triage_incident(
    title: str,
    description: str,
    service_name: str,
) -> dict[str, object]:
    prediction = predict_incident(
        title=title,
        description=description,
        service_name=service_name,
    )

    guardrail = apply_severity_guardrail(
        predicted_severity=str(
            prediction["predicted_severity"]
        ),
        title=title,
        description=description,
    )

    prediction["predicted_severity"] = guardrail[
        "final_severity"
    ]

    routing = route_incident(
        predicted_severity=str(
            prediction["predicted_severity"]
        ),
        category_confidence=float(
            prediction["category_confidence"]
        ),
        severity_confidence=float(
            prediction["severity_confidence"]
        ),
    )

    return {
        **prediction,
        **routing,
        "reason": (
            f"{routing['reason']} "
            f"Severity guardrail: {guardrail['reason']}"
        ),
        "triaged_at": datetime.now(timezone.utc),
    }