CREATE TABLE IF NOT EXISTS llm_generation_logs (
    id UUID PRIMARY KEY,
    incident_id UUID NOT NULL REFERENCES incidents(id) ON DELETE CASCADE,
    model_name VARCHAR(100) NOT NULL,
    grounding_status VARCHAR(30),
    status VARCHAR(30) NOT NULL,
    latency_ms DOUBLE PRECISION NOT NULL,
    prompt_token_count INTEGER,
    response_token_count INTEGER,
    error_message TEXT,
    created_at TIMESTAMPTZ NOT NULL
);