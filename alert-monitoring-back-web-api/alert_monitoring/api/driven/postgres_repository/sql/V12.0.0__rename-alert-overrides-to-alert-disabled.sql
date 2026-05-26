ALTER TABLE public.alert_overrides RENAME TO alert_disabled;

COMMENT ON TABLE alert_disabled IS 'Tabla que contiene las alertas por defecto deshabilitadas o parcialmente excluidas por solución';
