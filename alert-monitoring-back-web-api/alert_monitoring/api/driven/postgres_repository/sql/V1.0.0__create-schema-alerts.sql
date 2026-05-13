CREATE TABLE public.alerts (
    id                   BIGSERIAL       NOT NULL,
    name                 VARCHAR(255)    NOT NULL,
    description          TEXT            NOT NULL,
    source_tool          VARCHAR(255)    NULL,
    severity             VARCHAR(50)     NOT NULL,
    condition            TEXT            NOT NULL,
    environments         JSONB           NOT NULL DEFAULT '[]',
    microservice         VARCHAR(255)    NULL,
    solution             VARCHAR(255)    NULL,
    notification_channel VARCHAR(255)    NULL,
    alert_type           VARCHAR(255)    NULL,
    CONSTRAINT alerts_pkey PRIMARY KEY (id)
);

CREATE INDEX ix_alerts_name ON public.alerts (name);