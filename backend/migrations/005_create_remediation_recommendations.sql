CREATE TABLE IF NOT EXISTS remediation_recommendations (
    id UUID PRIMARY KEY,
    incident_id UUID NOT NULL REFERENCES incidents(id) ON DELETE CASCADE,
    recommendation TEXT NOT NULL,
    evidence TEXT NOT NULL,
    source_type VARCHAR(50) NOT NULL,
    source_id UUID,
    status VARCHAR(30) NOT NULL DEFAULT 'pending',
    reviewer_name VARCHAR(100),
    review_note TEXT,
    created_at TIMESTAMPTZ NOT NULL,
    reviewed_at TIMESTAMPTZ
);