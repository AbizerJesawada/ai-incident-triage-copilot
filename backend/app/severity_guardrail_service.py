SEVERITY_RANKS = {
    "low": 1,
    "medium": 2,
    "high": 3,
    "critical": 4,
}

CRITICAL_PHRASES = [
    "all users",
    "all customer",
    "complete outage",
    "service unavailable",
    "production down",
    "data loss",
    "every login fails",
    "cannot log in",
    "payments are failing",
]

HIGH_PHRASES = [
    "many users",
    "customers cannot",
    "repeatedly fails",
    "major impact",
    "no workaround",
]

LOW_IMPACT_PHRASES = [
    "small number",
    "minor",
    "noncritical",
    "not urgent",
    "retrying succeeds",
]


def apply_severity_guardrail(
    predicted_severity: str,
    title: str,
    description: str,
) -> dict[str, str]:
    incident_text = f"{title} {description}".lower()

    if any(
        phrase in incident_text
        for phrase in CRITICAL_PHRASES
    ):
        return {
            "final_severity": "critical",
            "reason": (
                "Critical outage phrases were detected "
                "in the incident text."
            ),
        }

    if any(
        phrase in incident_text
        for phrase in HIGH_PHRASES
    ):
        if SEVERITY_RANKS[predicted_severity] < 3:
            return {
                "final_severity": "high",
                "reason": (
                    "High-impact phrases were detected "
                    "in the incident text."
                ),
            }

    if any(
        phrase in incident_text
        for phrase in LOW_IMPACT_PHRASES
    ):
        if predicted_severity == "critical":
            return {
                "final_severity": "high",
                "reason": (
                    "Low-impact phrases were detected, "
                    "so critical severity was reduced."
                ),
            }

    return {
        "final_severity": predicted_severity,
        "reason": (
            "No severity guardrail phrase changed "
            "the ML prediction."
        ),
    }