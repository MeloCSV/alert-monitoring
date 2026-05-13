ALTER TABLE public.alert_overrides
    ADD COLUMN is_partial BOOLEAN NOT NULL DEFAULT FALSE;

COMMENT ON COLUMN alert_overrides.is_partial IS 'Indica si la alerta por defecto está parcialmente excepcionada (algún job/deployment del microservicio excluido pero el namespace sigue activo)';
