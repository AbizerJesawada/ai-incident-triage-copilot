CREATE TABLE IF NOT EXISTS incident_change_correlations (
    id UUID PRIMARY KEY,
    incident_id UUID NOT NULL REFERENCES incidents(id) ON DELETE CASCADE,
    change_event_id UUID NOT NULL REFERENCES change_events(id) ON DELETE CASCADE,
    time_difference_minutes DOUBLE PRECISION NOT NULL,
    correlation_score DOUBLE PRECISION NOT NULL,
    correlation_reason TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL,
    UNIQUE (incident_id, change_event_id)
);