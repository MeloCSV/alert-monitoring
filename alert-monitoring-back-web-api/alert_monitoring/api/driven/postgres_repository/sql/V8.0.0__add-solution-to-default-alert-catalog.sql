ALTER TABLE public.default_alert_catalog
    ADD COLUMN IF NOT EXISTS solution VARCHAR(255) NULL;
