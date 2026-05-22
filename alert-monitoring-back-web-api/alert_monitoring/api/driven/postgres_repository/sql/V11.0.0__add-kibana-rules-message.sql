ALTER TABLE kibana_rules
    ADD COLUMN message TEXT;

COMMENT ON COLUMN kibana_rules.message IS 'Mensaje descriptivo de la regla extraído de annotations.message en Kibana';
