from types import SimpleNamespace

from app.slack_event_service import (
    acknowledge_eyes_reaction,
)


class FakeDatabase:
    def __init__(self, notification) -> None:
        self.notification = notification
        self.committed = False

    def scalar(self, statement):
        return self.notification

    def commit(self) -> None:
        self.committed = True


def test_eyes_reaction_acknowledges_notification() -> None:
    notification = SimpleNamespace(
        slack_channel_id="C123",
        slack_message_ts="123.456",
        acknowledged_at=None,
        read_at=None,
        status="pending",
        acknowledged_by=None,
    )

    db = FakeDatabase(notification)

    event = {
        "type": "reaction_added",
        "reaction": "eyes",
        "user": "U123",
        "item": {
            "type": "message",
            "channel": "C123",
            "ts": "123.456",
        },
    }

    result = acknowledge_eyes_reaction(
        db=db,
        event=event,
    )

    assert result is True
    assert notification.status == "read"
    assert notification.acknowledged_by == "U123"
    assert notification.acknowledged_at is not None
    assert db.committed is True