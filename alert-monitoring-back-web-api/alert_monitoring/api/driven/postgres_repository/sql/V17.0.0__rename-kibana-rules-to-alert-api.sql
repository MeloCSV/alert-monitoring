ALTER TABLE kibana_rules RENAME TO alert_api;

DROP INDEX IF EXISTS kibana_rules_is_global_idx;
ALTER TABLE alert_api DROP CONSTRAINT IF EXISTS kibana_rules_rule_id_kibana_name_key;

ALTER TABLE alert_api DROP COLUMN IF EXISTS schedule_interval;
ALTER TABLE alert_api DROP COLUMN IF EXISTS disabled_apis;
ALTER TABLE alert_api DROP COLUMN IF EXISTS is_global;
ALTER TABLE alert_api DROP COLUMN IF EXISTS last_execution_date;
ALTER TABLE alert_api DROP COLUMN IF EXISTS last_execution_status;
ALTER TABLE alert_api DROP COLUMN IF EXISTS kibana_url;
ALTER TABLE alert_api DROP COLUMN IF EXISTS kibana_name;

ALTER TABLE alert_api RENAME COLUMN notification_channels TO notification_channel;
ALTER TABLE alert_api ALTER COLUMN notification_channel TYPE VARCHAR(100) USING (notification_channel->>0);

ALTER TABLE alert_api RENAME COLUMN apis TO apis_alertadas;

ALTER TABLE alert_api ADD CONSTRAINT alert_api_rule_id_key UNIQUE (rule_id);
