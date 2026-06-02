ALTER TABLE alert_api        DROP COLUMN IF EXISTS tags;
ALTER TABLE catalog_apps     DROP COLUMN IF EXISTS object_key;
ALTER TABLE catalog_apps     DROP COLUMN IF EXISTS platform;
ALTER TABLE catalog_apps     DROP COLUMN IF EXISTS csw_code;
ALTER TABLE catalog_apps     DROP COLUMN IF EXISTS synced_at;
ALTER TABLE catalog_app_api  DROP COLUMN IF EXISTS synced_at;
