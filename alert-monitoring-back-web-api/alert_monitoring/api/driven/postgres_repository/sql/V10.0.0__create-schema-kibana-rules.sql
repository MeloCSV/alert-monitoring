CREATE TABLE kibana_rules (
    id                     BIGSERIAL       NOT NULL,
    rule_id                VARCHAR(100)    NOT NULL,
    name                   VARCHAR(500)    NOT NULL,
    enabled                BOOLEAN         NOT NULL DEFAULT FALSE,
    tags                   JSONB           NOT NULL DEFAULT '[]',
    schedule_interval      VARCHAR(50),
    severity               VARCHAR(50),
    notification_channels  JSONB           NOT NULL DEFAULT '[]',
    apis                   JSONB           NOT NULL DEFAULT '[]',
    is_global              BOOLEAN         NOT NULL DEFAULT FALSE,
    last_execution_date    TIMESTAMP,
    last_execution_status  VARCHAR(50),
    kibana_url             TEXT,
    kibana_name            VARCHAR(100),
    CONSTRAINT kibana_rules_pkey PRIMARY KEY (id),
    CONSTRAINT kibana_rules_rule_id_kibana_name_key UNIQUE (rule_id, kibana_name)
);

CREATE INDEX kibana_rules_is_global_idx ON kibana_rules (is_global);

COMMENT ON TABLE kibana_rules IS 'Reglas de alerting expuestas por las APIs de Kibana (/api/alerting/rules/_find). Se pueblan en el sync de Kibana y se consultan agrupadas por API.';
COMMENT ON COLUMN kibana_rules.rule_id IS 'ID original de la regla en Kibana';
COMMENT ON COLUMN kibana_rules.apis IS 'Lista de APIs (transactionElement.serviceName) detectadas en el KQL o termField de la regla';
COMMENT ON COLUMN kibana_rules.is_global IS 'True si no se identifica una API concreta o la regla aplica de forma global';
