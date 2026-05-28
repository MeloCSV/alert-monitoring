ALTER TABLE kibana_rules
    ADD COLUMN disabled_apis JSONB NOT NULL DEFAULT '[]'::JSONB;

COMMENT ON COLUMN kibana_rules.disabled_apis IS 'APIs excluidas de una regla global (cláusulas NOT transactionElement.serviceName en el KQL)';
