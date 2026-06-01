CREATE TABLE alert_api_disabled (
    id             BIGSERIAL    NOT NULL,
    alert_name     VARCHAR(255) NOT NULL,
    api            VARCHAR(255) NOT NULL,
    is_disabled    BOOLEAN      NOT NULL DEFAULT FALSE,
    is_partial     BOOLEAN      NOT NULL DEFAULT FALSE,
    excluded_items JSONB        NOT NULL DEFAULT '[]',
    CONSTRAINT alert_api_disabled_pkey PRIMARY KEY (id)
);

CREATE INDEX alert_api_disabled_alert_name_idx ON alert_api_disabled (alert_name);
CREATE INDEX alert_api_disabled_api_idx ON alert_api_disabled (api);

COMMENT ON TABLE alert_api_disabled IS 'Estado de deshabilitación de alertas globales de API por cada API específica. Se puebla durante la lógica de correlación api-alerta.';
COMMENT ON COLUMN alert_api_disabled.alert_name IS 'Nombre de la alerta global de API (raw_name en default_alert_api)';
COMMENT ON COLUMN alert_api_disabled.api IS 'API para la que se evalúa el estado de la alerta';
COMMENT ON COLUMN alert_api_disabled.excluded_items IS 'Sub-elementos excluidos del alertado para esta API';
