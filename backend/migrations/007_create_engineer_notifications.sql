CREATE TABLE IF NOT EXISTS engineer_notifications (
    id UUID PRIMARY KEY,
    incident_id UUID NOT NULL REFERENCES incidents(id)
        ON DELETE CASCADE,
    notification_type VARCHAR(50) NOT NULL,
    message TEXT NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    created_at TIMESTAMPTZ NOT NULL,
    read_at TIMESTAMPTZ
);