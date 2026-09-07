ALTER TABLE incidents
ADD COLUMN resolved_by VARCHAR(100);

ALTER TABLE incidents
ADD COLUMN resolution_note TEXT;

ALTER TABLE incidents
ADD COLUMN resolved_at TIMESTAMPTZ;