ALTER TABLE alerts RENAME TO alert_app;
ALTER INDEX ix_alerts_name RENAME TO ix_alert_app_name;
ALTER TABLE alert_app DROP COLUMN IF EXISTS alert_type;
ALTER TABLE alert_app DROP COLUMN IF EXISTS cluster;
ALTER TABLE alert_app DROP COLUMN IF EXISTS prometheus_name;
