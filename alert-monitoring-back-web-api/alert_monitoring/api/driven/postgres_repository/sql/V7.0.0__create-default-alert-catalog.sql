CREATE TABLE public.default_alert_catalog (
    id                   BIGSERIAL       NOT NULL,
    cluster              VARCHAR(255)    NOT NULL,
    name                 VARCHAR(255)    NOT NULL,
    display_name         VARCHAR(255)    NOT NULL,
    description          TEXT            NOT NULL,
    severity             VARCHAR(50)     NOT NULL,
    condition            TEXT            NOT NULL,
    environments         JSONB           NOT NULL DEFAULT '[]',
    notification_channel VARCHAR(255)    NULL,
    CONSTRAINT default_alert_catalog_pkey PRIMARY KEY (id)
);
CREATE INDEX ix_default_alert_catalog_cluster ON public.default_alert_catalog (cluster);
CREATE INDEX ix_default_alert_catalog_name ON public.default_alert_catalog (name);
