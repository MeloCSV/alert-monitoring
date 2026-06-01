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

COMMENT ON TABLE default_alert_api IS 'Catálogo canónico de alertas por defecto para APIs. Una fila por tipo de alerta, equivalente a default_alert_app para el dominio de APIs.';
COMMENT ON COLUMN default_alert_api.raw_name IS 'Nombre técnico original de la alerta (e.g. nombre de la regla en Kibana)';
COMMENT ON COLUMN default_alert_api.display_name IS 'Nombre legible para la UI';
COMMENT ON COLUMN default_alert_api.excluded_apis IS 'APIs excluidas del alertado por defecto';
