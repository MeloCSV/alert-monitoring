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

COMMENT ON TABLE default_alerts IS 'Catálogo canónico de alertas por defecto. Una fila por tipo de alerta, independientemente de la nube o fichero Prometheus de origen.';
COMMENT ON COLUMN default_alerts.raw_name IS 'Nombre original de la alerta en Prometheus (e.g. Default_Service_Status_KO)';
COMMENT ON COLUMN default_alerts.display_name IS 'Nombre legible mostrado en la UI';
COMMENT ON COLUMN default_alerts.raw_description IS 'Mensaje de anotación original del fichero Prometheus con placeholders de labels';
COMMENT ON COLUMN default_alerts.display_description IS 'Descripción traducida y legible para la UI';
COMMENT ON COLUMN default_alerts.excluded_namespaces IS 'Unión de todos los patrones namespace!~ de todas las reglas Prometheus para esta alerta';
COMMENT ON COLUMN default_alerts.included_namespaces IS 'Unión de todos los patrones namespace=~ de las reglas criticas (re-inclusiones)';
COMMENT ON COLUMN default_alerts.excluded_jobs IS 'Unión de todos los patrones job/deployment!~ de todas las reglas Prometheus para esta alerta';

INSERT INTO default_alerts (raw_name, display_name, display_description, severity, notification_channel) VALUES
('Default_Service_Status_KO',
 'Servicio sin réplicas activas',
 'El microservicio no tiene ninguna réplica levantada. El servicio está completamente caído y no puede atender peticiones.',
 'critical', 'ServiceNow'),

('Default_Service_Status_Degraded',
 'Servicio con réplicas insuficientes',
 'El microservicio no tiene todas sus réplicas disponibles. El servicio funciona de forma degradada con menos instancias de las configuradas.',
 'principal', 'ServiceNow'),

('Default_Deployment_Status_Unavailable',
 'Deployment no disponible',
 'El deployment no está disponible según Kubernetes. La condición ''Available'' es false durante más de 10 minutos.',
 'critical', 'ServiceNow'),

('Default_High_4xx_Http_Requests_Principal',
 'Alto porcentaje de errores HTTP 4xx (>5%)',
 'Más del 5% de las peticiones HTTP están respondiendo con errores 4xx (p. ej. 404 Not Found, 401 Unauthorized). Puede indicar peticiones incorrectas o problemas de configuración.',
 'principal', 'ServiceNow'),

('Default_High_5xx_Http_Requests_Principal',
 'Alto porcentaje de errores HTTP 5xx (>5%)',
 'Más del 5% de las peticiones HTTP están respondiendo con errores 5xx (errores internos del servidor). El servicio está fallando al procesar las peticiones.',
 'principal', 'ServiceNow'),

('Default_High_4xx_Http_Requests_Critical',
 'Porcentaje crítico de errores HTTP 4xx (>10%)',
 'Más del 10% de las peticiones HTTP están respondiendo con errores 4xx. Nivel crítico de errores de cliente que requiere atención inmediata.',
 'critical', 'ServiceNow'),

('Default_High_5xx_Http_Requests_Critical',
 'Porcentaje crítico de errores HTTP 5xx (>10%)',
 'Más del 10% de las peticiones HTTP están respondiendo con errores 5xx (errores internos del servidor). Nivel crítico de fallos que requiere atención inmediata.',
 'critical', 'ServiceNow'),

('Default_JobFailed',
 'Job de Kubernetes finalizado con error',
 'Un job de Kubernetes ha terminado en estado fallido. Puede tratarse de un CronJob que no se ejecutó correctamente.',
 'critical', 'ServiceNow'),

('Default_JobSuspended',
 'Job de Kubernetes suspendido',
 'Un job de Kubernetes está en estado suspendido. No ejecutará ninguna tarea hasta que sea reanudado manualmente.',
 'critical', 'ServiceNow'),

('Default_JobExecutionMissed',
 'Job no ejecutado según su planificación',
 'Un job programado lleva más de 5 minutos en estado Pending o Unknown. El pod no se ha ejecutado en el tiempo esperado.',
 'critical', 'ServiceNow'),

('Default_CPURequestQuotaReached',
 'Cuota de CPU request al 90%',
 'El namespace ha consumido el 90% de su cuota de CPU (requests). Si se alcanza el 100%, Kubernetes no podrá programar nuevos pods en este namespace.',
 'principal', 'ServiceNow'),

('Default_MemoryLimitQuotaReached',
 'Cuota de memoria limit al 90%',
 'El namespace ha consumido el 90% de su cuota de memoria (limits). Superar el límite puede provocar que Kubernetes elimine pods por exceso de memoria.',
 'principal', 'ServiceNow'),

('Default_MemoryRequestQuotaReached',
 'Cuota de memoria request al 90%',
 'El namespace ha consumido el 90% de su cuota de memoria (requests). Si se alcanza el 100%, Kubernetes no podrá programar nuevos pods en este namespace.',
 'principal', 'ServiceNow'),

('Default_CpuUsageHigh',
 'Uso de CPU superior al 90% del límite',
 'El namespace está usando más del 90% de su límite de CPU. Esto puede causar throttling (ralentización) en los servicios y degradar el rendimiento.',
 'principal', 'ServiceNow'),

('Default_HPAMaximumReplicasForTooLong',
 'HPA en máximo de réplicas durante más de 1 hora',
 'El autoescalador horizontal (HPA) lleva más de 1 hora con el número máximo de réplicas activas. No puede escalar más y el sistema podría estar bajo una presión sostenida.',
 'principal', 'ServiceNow');
