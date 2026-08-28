ALTER TABLE engineer_notifications
    ADD COLUMN IF NOT EXISTS acknowledged_by VARCHAR(100);

ALTER TABLE engineer_notifications
    ADD COLUMN IF NOT EXISTS acknowledged_at TIMESTAMPTZ;