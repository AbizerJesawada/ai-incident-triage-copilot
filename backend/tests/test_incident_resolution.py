from fastapi.testclient import TestClient

from app.database import SessionLocal
from app.main import app
from app.models import Incident


def create_open_incident() -> Incident:
    db = SessionLocal()

    incident = Incident(
        title="Resolution workflow test incident",
        description="A test incident for the resolution endpoint.",
        service_name="payment-api",
        status="open",
        source="test",
    )

    db.add(incident)
    db.commit()
    db.refresh(incident)
    db.expunge(incident)
    db.close()

    return incident


def delete_incident(incident_id: object) -> None:
    db = SessionLocal()

    incident = db.get(Incident, incident_id)

    if incident is not None:
        db.delete(incident)
        db.commit()

    db.close()


def test_resolve_incident_saves_resolution_details() -> None:
    incident = create_open_incident()
    client = TestClient(app)

    try:
        response = client.post(
            f"/incidents/{incident.id}/resolve",
            json={
                "resolved_by": "Test Engineer",
                "resolution_note": (
                    "Restarted the payment worker and confirmed "
                    "successful requests."
                ),
            },
        )

        assert response.status_code == 200

        resolved_incident = response.json()

        assert resolved_incident["status"] == "resolved"
        assert resolved_incident["sla_status"] == "resolved"
        assert resolved_incident["resolved_by"] == "Test Engineer"
        assert resolved_incident["resolved_at"] is not None
    finally:
        delete_incident(incident.id)


def test_resolving_an_incident_twice_returns_conflict() -> None:
    incident = create_open_incident()
    client = TestClient(app)

    try:
        payload = {
            "resolved_by": "Test Engineer",
            "resolution_note": "The test incident was fixed.",
        }

        first_response = client.post(
            f"/incidents/{incident.id}/resolve",
            json=payload,
        )
        second_response = client.post(
            f"/incidents/{incident.id}/resolve",
            json=payload,
        )

        assert first_response.status_code == 200
        assert second_response.status_code == 409
    finally:
        delete_incident(incident.id)