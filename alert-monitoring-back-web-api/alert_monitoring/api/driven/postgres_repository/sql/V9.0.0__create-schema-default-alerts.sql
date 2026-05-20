CREATE TABLE default_alerts (
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
    CONSTRAINT default_alerts_pkey PRIMARY KEY (id),
    CONSTRAINT default_alerts_raw_name_key UNIQUE (raw_name)
);

COMMENT ON TABLE default_alerts IS 'Catálogo canónico de alertas por defecto. Una fila por tipo de alerta, independientemente de la nube o fichero Prometheus de origen. Se puebla y actualiza durante el sync de Prometheus.';
COMMENT ON COLUMN default_alerts.raw_name IS 'Nombre original de la alerta en Prometheus (e.g. Default_Service_Status_KO)';
COMMENT ON COLUMN default_alerts.display_name IS 'Nombre legible para la UI. Viene de DEFAULT_ALERT_DISPLAY si existe, si no usa raw_name';
COMMENT ON COLUMN default_alerts.raw_description IS 'Mensaje de anotación original del fichero Prometheus con placeholders de labels';
COMMENT ON COLUMN default_alerts.display_description IS 'Descripción traducida para la UI. Viene de DEFAULT_ALERT_DISPLAY si existe, si no es NULL';
COMMENT ON COLUMN default_alerts.excluded_namespaces IS 'Unión de todos los patrones namespace!~ de todas las reglas Prometheus para esta alerta';
COMMENT ON COLUMN default_alerts.included_namespaces IS 'Unión de todos los patrones namespace=~ de las reglas criticas (re-inclusiones)';
COMMENT ON COLUMN default_alerts.excluded_jobs IS 'Unión de todos los patrones job/deployment!~ de todas las reglas Prometheus para esta alerta';
