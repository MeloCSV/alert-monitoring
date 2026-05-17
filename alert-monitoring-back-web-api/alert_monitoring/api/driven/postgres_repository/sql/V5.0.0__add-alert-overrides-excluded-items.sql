ALTER TABLE public.alert_overrides
    ADD COLUMN excluded_items JSONB NOT NULL DEFAULT '[]';

COMMENT ON COLUMN alert_overrides.excluded_items IS 'Lista de jobs o namespaces concretos de la aplicación excluidos del alarmado por defecto (chips de parcialidad)';
