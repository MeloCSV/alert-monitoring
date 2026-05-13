ALTER TABLE public.alert_overrides
    RENAME COLUMN microservice TO solution;

COMMENT ON COLUMN alert_overrides.solution IS 'Aplicación (solution/PI) para la que se evalúa el override de la alerta por defecto';
