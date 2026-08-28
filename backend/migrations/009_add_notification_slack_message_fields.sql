ALTER TABLE engineer_notifications
    ADD COLUMN IF NOT EXISTS slack_channel_id VARCHAR(100);

ALTER TABLE engineer_notifications
    ADD COLUMN IF NOT EXISTS slack_message_ts VARCHAR(50);