CREATE TABLE public.alert_overrides (
    id          BIGSERIAL       NOT NULL,
    alert_name  VARCHAR(255)    NOT NULL,
    microservice VARCHAR(255)   NULL,
    is_disabled BOOLEAN         NOT NULL DEFAULT FALSE,
    CONSTRAINT alert_overrides_pkey PRIMARY KEY (id)
);

COMMENT ON TABLE alert_overrides IS 'Tabla que contiene los overrides de alertas';
COMMENT ON COLUMN alert_overrides.id IS 'Identificador del override';
COMMENT ON COLUMN alert_overrides.alert_name IS 'Nombre de la alerta';
COMMENT ON COLUMN alert_overrides.microservice IS 'Microservicio al que aplica el override';
COMMENT ON COLUMN alert_overrides.is_disabled IS 'Indica si la alerta está deshabilitada';