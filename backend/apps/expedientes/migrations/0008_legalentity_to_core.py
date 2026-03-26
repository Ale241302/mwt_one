# Sprint 8 fix: LegalEntity moved to core app.
# DB: RunSQL retargets FK constraints and drops expedientes_legalentity.
# State: We CANNOT delete LegalEntity from expedientes state here because
# transfers/0001_initial (which depends on expedientes/0004) still references
# expedientes.legalentity. Deletion happens in 0009 after transfers/0002 retargets.
import django.db.models.deletion
from django.db import migrations, models


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
                                    ALTER TABLE expedientes_expediente
                                        DROP CONSTRAINT IF EXISTS expedientes_expedien_client_id_c95ce8ea_fk_expedient,
                                        ADD CONSTRAINT expedientes_expedien_client_id_c95ce8ea_fk_core
                                            FOREIGN KEY (client_id) REFERENCES core_legalentity(id)
                                            DEFERRABLE INITIALLY DEFERRED;
                                    ALTER TABLE expedientes_expediente
                                        DROP CONSTRAINT IF EXISTS expedientes_expedien_legal_entity_id_1e48adca_fk_expedient,
                                        ADD CONSTRAINT expedientes_expedien_legal_entity_id_1e48adca_fk_core
                                            FOREIGN KEY (legal_entity_id) REFERENCES core_legalentity(id)
                                            DEFERRABLE INITIALLY DEFERRED;
                                    ALTER TABLE transfers_node
                                        DROP CONSTRAINT IF EXISTS transfers_node_legal_entity_id_5591960f_fk_expedient,
                                        ADD CONSTRAINT transfers_node_legal_entity_id_5591960f_fk_core
                                            FOREIGN KEY (legal_entity_id) REFERENCES core_legalentity(id)
                                            DEFERRABLE INITIALLY DEFERRED;
                                    ALTER TABLE transfers_transfer
                                        DROP CONSTRAINT IF EXISTS transfers_transfer_ownership_after_id_9270eb8e_fk_expedient,
                                        ADD CONSTRAINT transfers_transfer_ownership_after_id_9270eb8e_fk_core
                                            FOREIGN KEY (ownership_after_id) REFERENCES core_legalentity(id)
                                            DEFERRABLE INITIALLY DEFERRED;
                                    ALTER TABLE transfers_transfer
                                        DROP CONSTRAINT IF EXISTS transfers_transfer_ownership_before_id_2c187f63_fk_expedient,
                                        ADD CONSTRAINT transfers_transfer_ownership_before_id_2c187f63_fk_core
                                            FOREIGN KEY (ownership_before_id) REFERENCES core_legalentity(id)
                                            DEFERRABLE INITIALLY DEFERRED;
                                    DROP TABLE expedientes_legalentity;
                                ELSE
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
                # Retarget expediente FKs to core in state
                migrations.AlterField(
                    model_name='expediente',
                    name='client',
                    field=models.ForeignKey(
                        help_text='Cliente',
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name='expedientes_como_cliente',
                        to='core.legalentity',
                    ),
                ),
                migrations.AlterField(
                    model_name='expediente',
                    name='legal_entity',
                    field=models.ForeignKey(
                        help_text='Entidad emisora',
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name='expedientes_emitidos',
                        to='core.legalentity',
                    ),
                ),
                # NOTE: Do NOT delete LegalEntity from expedientes state here.
                # transfers/0001_initial still holds lazy refs to expedientes.legalentity.
                # Deletion is deferred to expedientes/0009 after transfers/0002 clears refs.
            ],
        ),
    ]
