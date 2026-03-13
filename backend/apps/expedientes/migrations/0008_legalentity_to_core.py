# Sprint 8 fix: LegalEntity moved to core app.
# Uses SeparateDatabaseAndState with IF EXISTS so it works on both:
#   - Fresh installs: expedientes_legalentity may not exist, core_legalentity already created by core.0002
#   - Existing installs: expedientes_legalentity exists and needs to be renamed
from django.db import migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('expedientes', '0007_expediente_destination_alter_expediente_brand'),
        ('core', '0002_legalentity'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunSQL(
                    # On fresh DB: core_legalentity already exists, just drop the empty expedientes one.
                    # On existing DB: rename expedientes_legalentity -> core_legalentity if it still exists
                    # and core_legalentity doesn't (shouldn't happen in normal flow but safe guard).
                    sql="""
                        DO $$
                        BEGIN
                            IF EXISTS (
                                SELECT 1 FROM information_schema.tables
                                WHERE table_schema = 'public'
                                AND table_name = 'expedientes_legalentity'
                            ) THEN
                                IF NOT EXISTS (
                                    SELECT 1 FROM information_schema.tables
                                    WHERE table_schema = 'public'
                                    AND table_name = 'core_legalentity'
                                ) THEN
                                    ALTER TABLE expedientes_legalentity RENAME TO core_legalentity;
                                ELSE
                                    DROP TABLE expedientes_legalentity;
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
