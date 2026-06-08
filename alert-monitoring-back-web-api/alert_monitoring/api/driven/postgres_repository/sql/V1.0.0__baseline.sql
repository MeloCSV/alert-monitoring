CREATE TABLE alert_app (
    id                   BIGSERIAL       NOT NULL,
    name                 VARCHAR(255)    NOT NULL,
    description          TEXT            NOT NULL,
    source_tool          VARCHAR(255)    NULL,
    severity             VARCHAR(50)     NOT NULL,
    chips                JSONB           NOT NULL DEFAULT '[]',
    environments         JSONB           NOT NULL DEFAULT '[]',
    microservice         VARCHAR(255)    NULL,
    solution             VARCHAR(255)    NULL,
    notification_channel VARCHAR(255)    NULL,
    CONSTRAINT alert_app_pkey PRIMARY KEY (id)
);

CREATE INDEX ix_alert_app_name ON alert_app (name);


CREATE TABLE default_alert_app (
    id                   BIGSERIAL       NOT NULL,
    raw_name             VARCHAR(255)    NOT NULL,
    display_name         VARCHAR(500)    NOT NULL,
    raw_description      TEXT,
    display_description  TEXT,
    severity             VARCHAR(50),
    notification_channel VARCHAR(100),
    excluded_namespaces  JSONB           NOT NULL DEFAULT '[]',
    included_namespaces  JSONB           NOT NULL DEFAULT '[]',
    excluded_jobs        JSONB           NOT NULL DEFAULT '[]',
    CONSTRAINT default_alert_app_pkey PRIMARY KEY (id),
    CONSTRAINT default_alert_app_raw_name_key UNIQUE (raw_name)
);


CREATE TABLE catalog_apps (
    id        SERIAL          NOT NULL,
    object_id VARCHAR(50)     NOT NULL,
    name      VARCHAR(500)    NOT NULL,
    csw_code  VARCHAR(100)    NOT NULL,
    CONSTRAINT catalog_apps_pkey PRIMARY KEY (id),
    CONSTRAINT catalog_apps_object_id_key UNIQUE (object_id)
);

CREATE INDEX idx_catalog_apps_name ON catalog_apps (name);


CREATE TABLE catalog_app_api (
    id           SERIAL       NOT NULL,
    app          VARCHAR(500) NOT NULL,
    microservice VARCHAR(500) NOT NULL,
    apis         JSONB        NOT NULL DEFAULT '[]',
    CONSTRAINT catalog_app_api_pkey PRIMARY KEY (id),
    CONSTRAINT catalog_app_api_microservice_key UNIQUE (microservice)
);

CREATE INDEX idx_catalog_app_api_app ON catalog_app_api (app);

CREATE TABLE alert_api (
    id                   BIGSERIAL       NOT NULL,
    rule_id              VARCHAR(100)    NOT NULL,
    name                 VARCHAR(500)    NOT NULL,
    severity             VARCHAR(50),
    notification_channel VARCHAR(100),
    apis_alertadas       JSONB           NOT NULL DEFAULT '[]',
    message              TEXT,
    CONSTRAINT alert_api_pkey PRIMARY KEY (id),
    CONSTRAINT alert_api_rule_id_key UNIQUE (rule_id)
);


CREATE TABLE default_alert_api (
    id                   BIGSERIAL    NOT NULL,
    raw_name             VARCHAR(255) NOT NULL,
    display_name         VARCHAR(500) NOT NULL,
    raw_description      TEXT,
    display_description  TEXT,
    severity             VARCHAR(50),
    notification_channel VARCHAR(100),
    excluded_apis        JSONB        NOT NULL DEFAULT '[]',
    CONSTRAINT default_alert_api_pkey PRIMARY KEY (id),
    CONSTRAINT default_alert_api_raw_name_key UNIQUE (raw_name)
);
