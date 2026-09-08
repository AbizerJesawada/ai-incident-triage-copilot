from uuid import UUID, uuid4

from fastapi.testclient import TestClient

from app.auth_service import create_access_token, hash_password
from app.database import SessionLocal
from app.main import app
from app.models import Incident, User


def create_user(
    role: str = "user",
    full_name: str = "Test User",
) -> User:
    db = SessionLocal()

    user = User(
        email=f"auth-test-{uuid4()}@example.com",
        full_name=full_name,
        password_hash=hash_password("secure-test-password"),
        role=role,
    )

    db.add(user)
    db.commit()
    db.refresh(user)
    db.expunge(user)
    db.close()

    return user


def create_incident(
    reported_by_user_id: UUID | None,
    title: str,
) -> Incident:
    db = SessionLocal()

    incident = Incident(
        title=title,
        description="A test incident for access-control checks.",
        service_name="payment-api",
        status="open",
        source="test",
        reported_by_user_id=reported_by_user_id,
    )

    db.add(incident)
    db.commit()
    db.refresh(incident)
    db.expunge(incident)
    db.close()

    return incident


def get_headers(user: User) -> dict[str, str]:
    token = create_access_token(
        user_id=user.id,
        role=user.role,
    )

    return {
        "Authorization": f"Bearer {token}",
    }


def delete_test_data(
    incident_ids: list[UUID],
    user_ids: list[UUID],
) -> None:
    db = SessionLocal()

    for incident_id in incident_ids:
        incident = db.get(Incident, incident_id)

        if incident is not None:
            db.delete(incident)

    for user_id in user_ids:
        user = db.get(User, user_id)

        if user is not None:
            db.delete(user)

    db.commit()
    db.close()


def test_register_login_and_get_current_user() -> None:
    client = TestClient(app)
    email = f"register-test-{uuid4()}@example.com"
    user_id = None

    try:
        registration_response = client.post(
            "/auth/register",
            json={
                "email": email,
                "full_name": "Registered Test User",
                "password": "secure-test-password",
            },
        )

        assert registration_response.status_code == 201

        registered_user = registration_response.json()
        user_id = UUID(registered_user["id"])

        assert registered_user["role"] == "user"

        login_response = client.post(
            "/auth/login",
            json={
                "email": email,
                "password": "secure-test-password",
            },
        )

        assert login_response.status_code == 200

        access_token = login_response.json()["access_token"]

        account_response = client.get(
            "/auth/me",
            headers={
                "Authorization": f"Bearer {access_token}",
            },
        )

        assert account_response.status_code == 200
        assert account_response.json()["email"] == email
        assert account_response.json()["role"] == "user"
    finally:
        if user_id is not None:
            delete_test_data(
                incident_ids=[],
                user_ids=[user_id],
            )


def test_normal_user_sees_only_own_incidents() -> None:
    first_user = create_user(full_name="First Test User")
    second_user = create_user(full_name="Second Test User")

    first_incident = create_incident(
        reported_by_user_id=first_user.id,
        title="First user's incident",
    )

    second_incident = create_incident(
        reported_by_user_id=second_user.id,
        title="Second user's incident",
    )

    client = TestClient(app)

    try:
        list_response = client.get(
            "/incidents",
            headers=get_headers(first_user),
        )

        assert list_response.status_code == 200

        incidents = list_response.json()

        assert len(incidents) == 1
        assert incidents[0]["id"] == str(first_incident.id)

        detail_response = client.get(
            f"/incidents/{second_incident.id}",
            headers=get_headers(first_user),
        )

        assert detail_response.status_code == 403
    finally:
        delete_test_data(
            incident_ids=[first_incident.id, second_incident.id],
            user_ids=[first_user.id, second_user.id],
        )


def test_normal_user_cannot_use_engineer_routes() -> None:
    user = create_user()
    incident = create_incident(
        reported_by_user_id=user.id,
        title="Normal user incident",
    )

    client = TestClient(app)

    try:
        resolve_response = client.post(
            f"/incidents/{incident.id}/resolve",
            headers=get_headers(user),
            json={
                "resolution_note": "A normal user must not resolve.",
            },
        )

        similar_response = client.get(
            f"/incidents/{incident.id}/similar",
            headers=get_headers(user),
        )

        assert resolve_response.status_code == 403
        assert similar_response.status_code == 403
    finally:
        delete_test_data(
            incident_ids=[incident.id],
            user_ids=[user.id],
        )