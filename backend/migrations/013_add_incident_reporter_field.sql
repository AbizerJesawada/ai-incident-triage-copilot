ALTER TABLE incidents
ADD COLUMN reported_by_user_id UUID
REFERENCES users(id)
ON DELETE SET NULL;

CREATE INDEX idx_incidents_reported_by_user_id
ON incidents (reported_by_user_id);