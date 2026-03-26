-- Borrar datos demo creados por seed_demo_data.py
-- Los datos demo son los expedientes vinculados a entidades: SONDEL-CR, UMMIE-GT, IMPORCOMP-CO, MWT-CR (sin brand)

BEGIN;

-- 1. Obtener IDs de expedientes demo
-- (los de clientes de las entidades demo con brand=null)
CREATE TEMP TABLE demo_exp_ids AS
SELECT e.id
FROM expedientes_expediente e
JOIN core_legalentity le ON e.client_id = le.id
WHERE le.entity_id IN ('SONDEL-CR', 'UMMIE-GT', 'IMPORCOMP-CO')
  AND e.brand_id IS NULL;

SELECT COUNT(*) as "Expedientes demo a borrar" FROM demo_exp_ids;

-- 2. Borrar event logs relacionados
DELETE FROM expedientes_eventlog
WHERE aggregate_type = 'EXPEDIENTE'
  AND aggregate_id::text IN (SELECT id::text FROM demo_exp_ids);

-- 3. Borrar payment lines
DELETE FROM expedientes_paymentline
WHERE expediente_id IN (SELECT id FROM demo_exp_ids);

-- 4. Borrar cost lines
DELETE FROM expedientes_costline
WHERE expediente_id IN (SELECT id FROM demo_exp_ids);

-- 5. Borrar artifact instances
DELETE FROM expedientes_artifactinstance
WHERE expediente_id IN (SELECT id FROM demo_exp_ids);

-- 6. Nullificar FK source_expediente en transfers antes de borrar expedientes
UPDATE transfers_transfer
SET source_expediente_id = NULL
WHERE source_expediente_id IN (SELECT id FROM demo_exp_ids);

-- 7. Borrar expedientes demo
DELETE FROM expedientes_expediente
WHERE id IN (SELECT id FROM demo_exp_ids);

-- 8. Borrar transfer lines de transfers demo
DELETE FROM transfers_transferline
WHERE transfer_id IN (
    SELECT id FROM transfers_transfer WHERE transfer_id LIKE 'TRF-DEMO%'
);

-- 9. Borrar transfers demo
DELETE FROM transfers_transfer
WHERE transfer_id LIKE 'TRF-DEMO%';

-- 10. Borrar nodos demo
DELETE FROM transfers_node
WHERE name LIKE 'DEMO %';

-- 11. Borrar liquidation lines asociadas a expedientes demo (si existen)
-- (puede que las tables se llamen diferente - intentamos las variantes)
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'liquidations_liquidationline') THEN
        DELETE FROM liquidations_liquidationline
        WHERE matched_expediente_id IN (SELECT id FROM demo_exp_ids);

        DELETE FROM liquidations_liquidation
        WHERE period LIKE 'DEMO-%';
    END IF;
END $$;

-- 12. Borrar entidades legales demo
DELETE FROM core_legalentity
WHERE entity_id IN ('SONDEL-CR', 'UMMIE-GT', 'IMPORCOMP-CO', 'MWT-CR');

-- Mostrar resultado
SELECT COUNT(*) as "Expedientes restantes" FROM expedientes_expediente;

COMMIT;

SELECT 'Datos demo borrados exitosamente' as resultado;
