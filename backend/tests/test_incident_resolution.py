from uuid import uuid4

from fastapi.testclient import TestClient

from app.auth_service import create_access_token, hash_password
from app.database import SessionLocal
from app.main import app
from app.models import Incident, User


def create_engineer() -> User:
    db = SessionLocal()

    engineer = User(
        email=f"resolution-test-{uuid4()}@example.com",
        full_name="Test Engineer",
        password_hash=hash_password("secure-test-password"),
        role="engineer",
    )

    db.add(engineer)
    db.commit()
    db.refresh(engineer)
    db.expunge(engineer)
    db.close()

    return engineer


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


def delete_test_data(
    incident_id: object,
    engineer_id: object,
) -> None:
    db = SessionLocal()

    incident = db.get(Incident, incident_id)

    if incident is not None:
        db.delete(incident)

    engineer = db.get(User, engineer_id)

    if engineer is not None:
        db.delete(engineer)

    db.commit()
    db.close()


def get_engineer_headers(engineer: User) -> dict[str, str]:
    token = create_access_token(
        user_id=engineer.id,
        role=engineer.role,
    )

    return {
        "Authorization": f"Bearer {token}",
    }


def test_resolve_incident_saves_resolution_details() -> None:
    engineer = create_engineer()
    incident = create_open_incident()
    client = TestClient(app)

    try:
        response = client.post(
            f"/incidents/{incident.id}/resolve",
            headers=get_engineer_headers(engineer),
            json={
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
        delete_test_data(incident.id, engineer.id)


def test_resolving_incident_twice_returns_conflict() -> None:
    engineer = create_engineer()
    incident = create_open_incident()
    client = TestClient(app)

    try:
        payload = {
            "resolution_note": "The test incident was fixed.",
        }

        first_response = client.post(
            f"/incidents/{incident.id}/resolve",
            headers=get_engineer_headers(engineer),
            json=payload,
        )

        second_response = client.post(
            f"/incidents/{incident.id}/resolve",
            headers=get_engineer_headers(engineer),
            json=payload,
        )

        assert first_response.status_code == 200
        assert second_response.status_code == 409
    finally:
        delete_test_data(incident.id, engineer.id)