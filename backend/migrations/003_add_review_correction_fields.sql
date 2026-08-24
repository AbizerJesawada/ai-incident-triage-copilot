ALTER TABLE incident_reviews
ADD COLUMN IF NOT EXISTS actual_category VARCHAR(50);

ALTER TABLE incident_reviews
ADD COLUMN IF NOT EXISTS actual_severity VARCHAR(20);