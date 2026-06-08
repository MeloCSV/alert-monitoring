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

COMMENT ON TABLE default_alert_app IS 'Catálogo canónico de alertas por defecto. Una fila por tipo de alerta, independientemente de la nube o fichero Prometheus de origen. Se puebla y actualiza durante el sync de Prometheus.';
COMMENT ON COLUMN default_alert_app.raw_name IS 'Nombre original de la alerta en Prometheus (e.g. Default_Service_Status_KO)';
COMMENT ON COLUMN default_alert_app.display_name IS 'Nombre legible para la UI. Viene de DEFAULT_ALERT_DISPLAY si existe, si no usa raw_name';
COMMENT ON COLUMN default_alert_app.raw_description IS 'Mensaje de anotación original del fichero Prometheus con placeholders de labels';
COMMENT ON COLUMN default_alert_app.display_description IS 'Descripción traducida para la UI. Viene de DEFAULT_ALERT_DISPLAY si existe, si no es NULL';
COMMENT ON COLUMN default_alert_app.excluded_namespaces IS 'Unión de todos los patrones namespace!~ de todas las reglas Prometheus para esta alerta';
COMMENT ON COLUMN default_alert_app.included_namespaces IS 'Unión de todos los patrones namespace=~ de las reglas criticas (re-inclusiones)';
COMMENT ON COLUMN default_alert_app.excluded_jobs IS 'Unión de todos los patrones job/deployment!~ de todas las reglas Prometheus para esta alerta';


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
