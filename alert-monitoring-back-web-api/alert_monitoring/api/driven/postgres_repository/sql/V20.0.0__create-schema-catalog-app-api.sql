CREATE TABLE catalog_app_api (
    id           SERIAL       NOT NULL,
    app          VARCHAR(500) NOT NULL,
    microservice VARCHAR(500) NOT NULL,
    apis         JSONB        NOT NULL DEFAULT '[]',
    synced_at    TIMESTAMP    NOT NULL DEFAULT NOW(),
    CONSTRAINT catalog_app_api_pkey PRIMARY KEY (id),
    CONSTRAINT catalog_app_api_microservice_key UNIQUE (microservice)
);

CREATE INDEX idx_catalog_app_api_app ON catalog_app_api (app);

COMMENT ON TABLE catalog_app_api IS 'Correlación entre aplicaciones CNA y las APIs que producen sus microservicios. Se puebla a partir del JSON de correlación app-api.';
COMMENT ON COLUMN catalog_app_api.app IS 'Nombre canónico de la aplicación (de catalog_apps)';
COMMENT ON COLUMN catalog_app_api.microservice IS 'Nombre completo del microservicio/despliegue (child del JSON de origen)';
COMMENT ON COLUMN catalog_app_api.apis IS 'Lista de APIs producidas por este microservicio (parent del JSON de origen)';
