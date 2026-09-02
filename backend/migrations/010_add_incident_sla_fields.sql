ALTER TABLE incidents
ADD COLUMN sla_due_at TIMESTAMPTZ;

ALTER TABLE incidents
ADD COLUMN sla_status VARCHAR(20)
NOT NULL DEFAULT 'on_track';

CREATE INDEX idx_incidents_sla_status_due_at
ON incidents (sla_status, sla_due_at);