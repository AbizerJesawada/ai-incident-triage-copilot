from types import SimpleNamespace

from app.notification_service import (
    create_review_notification_if_needed,
)


class FakeDatabase:
    def __init__(self) -> None:
        self.added_items = []

    def scalar(self, statement):
        return None

    def add(self, item) -> None:
        self.added_items.append(item)

    def flush(self) -> None:
        pass


def test_no_notification_for_incident_without_review() -> None:
    db = FakeDatabase()

    incident = SimpleNamespace(
        id="incident-1",
        title="Low priority alert",
        service_name="catalog-api",
        triage_reason="Standard triage is enough.",
        human_review_required=False,
    )

    notification = create_review_notification_if_needed(
        db=db,
        incident=incident,
    )

    assert notification is None
    assert db.added_items == []