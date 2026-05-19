CREATE TABLE public.catalog_apps (
    id           SERIAL PRIMARY KEY,
    object_id    VARCHAR(50)  NOT NULL UNIQUE,
    object_key   VARCHAR(100) NOT NULL,
    name         VARCHAR(500) NOT NULL,
    csw_code     VARCHAR(100) NULL,
    platform     VARCHAR(500) NULL,
    synced_at    TIMESTAMP    NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_catalog_apps_name ON public.catalog_apps (name);
CREATE INDEX idx_catalog_apps_csw_code ON public.catalog_apps (csw_code);
