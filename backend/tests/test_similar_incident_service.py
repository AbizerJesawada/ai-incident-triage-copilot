from types import SimpleNamespace

from app.similar_incident_service import (
    find_similar_incidents,
)


def test_payment_incident_returns_payment_match_first() -> None:
    payment_incident = SimpleNamespace(
        id="payment-1",
        title="Checkout payment service outage",
        description=(
            "Customers cannot complete payment orders."
        ),
    )
    network_incident = SimpleNamespace(
        id="network-1",
        title="Office Wi-Fi is slow",
        description="A small number of laptops lose connection.",
    )

    matches = find_similar_incidents(
        target_title="Payment checkout is unavailable",
        target_description=(
            "All customers are unable to complete orders."
        ),
        candidate_incidents=[
            network_incident,
            payment_incident,
        ],
    )

    best_match, score = matches[0]

    assert best_match.id == "payment-1"
    assert score > 0


def test_no_candidates_returns_empty_list() -> None:
    matches = find_similar_incidents(
        target_title="Database outage",
        target_description="The database is unavailable.",
        candidate_incidents=[],
    )

    assert matches == []