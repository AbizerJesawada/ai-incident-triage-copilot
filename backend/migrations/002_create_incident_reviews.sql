CREATE TABLE IF NOT EXISTS incident_reviews (
    id UUID PRIMARY KEY,
    incident_id UUID NOT NULL REFERENCES incidents(id),
    reviewer_name VARCHAR(100) NOT NULL,
    decision VARCHAR(30) NOT NULL,
    review_note TEXT,
    created_at TIMESTAMPTZ NOT NULL
);