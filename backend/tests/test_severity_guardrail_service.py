from app.severity_guardrail_service import (
    apply_severity_guardrail,
)


def test_critical_phrase_overrides_ml_prediction():
    result = apply_severity_guardrail(
        predicted_severity="medium",
        title="Customer login outage",
        description=(
            "All users cannot log in because the "
            "service is unavailable."
        ),
    )

    assert result["final_severity"] == "critical"


def test_high_impact_phrase_increases_low_prediction():
    result = apply_severity_guardrail(
        predicted_severity="low",
        title="Checkout requests fail",
        description=(
            "Many users are affected and customers "
            "cannot complete payments."
        ),
    )

    assert result["final_severity"] == "high"


def test_low_impact_phrase_reduces_critical_prediction():
    result = apply_severity_guardrail(
        predicted_severity="critical",
        title="Minor dashboard delay",
        description=(
            "A small number of users are affected "
            "and retrying succeeds."
        ),
    )

    assert result["final_severity"] == "high"


def test_normal_incident_keeps_ml_prediction():
    result = apply_severity_guardrail(
        predicted_severity="medium",
        title="Report loading delay",
        description=(
            "The reporting page loads slowly during "
            "peak traffic."
        ),
    )

    assert result["final_severity"] == "medium"