# Sprint 8 fix: LegalEntity moved to core app.
# Fresh-DB path:
#   - core.0002 already created core_legalentity
#   - expedientes_legalentity exists with FK constraints pointing to it
#   - We must retarget those FKs to core_legalentity, then drop expedientes_legalentity
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('expedientes', '0007_expediente_destination_alter_expediente_brand'),
        ('core', '0002_legalentity'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunSQL(
                    sql="""
                        DO $$
                        BEGIN
                            IF EXISTS (
                                SELECT 1 FROM information_schema.tables
                                WHERE table_schema = 'public'
                                AND table_name = 'expedientes_legalentity'
                            ) THEN
                                IF EXISTS (
                                    SELECT 1 FROM information_schema.tables
                                    WHERE table_schema = 'public'
                                    AND table_name = 'core_legalentity'
                                ) THEN
                                    -- Retarget FK: expedientes_expediente.client_id
                                    ALTER TABLE expedientes_expediente
                                        DROP CONSTRAINT IF EXISTS expedientes_expedien_client_id_c95ce8ea_fk_expedient,
                                        ADD CONSTRAINT expedientes_expedien_client_id_c95ce8ea_fk_core
                                            FOREIGN KEY (client_id) REFERENCES core_legalentity(id)
                                            DEFERRABLE INITIALLY DEFERRED;

                                    -- Retarget FK: expedientes_expediente.legal_entity_id
                                    ALTER TABLE expedientes_expediente
                                        DROP CONSTRAINT IF EXISTS expedientes_expedien_legal_entity_id_1e48adca_fk_expedient,
                                        ADD CONSTRAINT expedientes_expedien_legal_entity_id_1e48adca_fk_core
                                            FOREIGN KEY (legal_entity_id) REFERENCES core_legalentity(id)
                                            DEFERRABLE INITIALLY DEFERRED;

                                    -- Retarget FK: transfers_node.legal_entity_id
                                    ALTER TABLE transfers_node
                                        DROP CONSTRAINT IF EXISTS transfers_node_legal_entity_id_5591960f_fk_expedient,
                                        ADD CONSTRAINT transfers_node_legal_entity_id_5591960f_fk_core
                                            FOREIGN KEY (legal_entity_id) REFERENCES core_legalentity(id)
                                            DEFERRABLE INITIALLY DEFERRED;

                                    -- Retarget FK: transfers_transfer.ownership_after_id
                                    ALTER TABLE transfers_transfer
                                        DROP CONSTRAINT IF EXISTS transfers_transfer_ownership_after_id_9270eb8e_fk_expedient,
                                        ADD CONSTRAINT transfers_transfer_ownership_after_id_9270eb8e_fk_core
                                            FOREIGN KEY (ownership_after_id) REFERENCES core_legalentity(id)
                                            DEFERRABLE INITIALLY DEFERRED;

                                    -- Retarget FK: transfers_transfer.ownership_before_id
                                    ALTER TABLE transfers_transfer
                                        DROP CONSTRAINT IF EXISTS transfers_transfer_ownership_before_id_2c187f63_fk_expedient,
                                        ADD CONSTRAINT transfers_transfer_ownership_before_id_2c187f63_fk_core
                                            FOREIGN KEY (ownership_before_id) REFERENCES core_legalentity(id)
                                            DEFERRABLE INITIALLY DEFERRED;

                                    -- Now safe to drop
                                    DROP TABLE expedientes_legalentity;
                                ELSE
                                    -- No core_legalentity yet: simple rename (legacy path)
                                    ALTER TABLE expedientes_legalentity RENAME TO core_legalentity;
                                END IF;
                            END IF;
                        END
                        $$;
                    """,
                    reverse_sql=migrations.RunSQL.noop,
                ),
            ],
            state_operations=[
                migrations.DeleteModel(name='LegalEntity'),
            ],
        ),
    ]
