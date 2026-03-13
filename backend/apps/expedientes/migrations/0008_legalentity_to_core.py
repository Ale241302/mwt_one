# Sprint 8 fix: LegalEntity moved to core app.
# This migration handles the DB-level rename via SeparateDatabaseAndState
# so existing data in expedientes_legalentity is preserved.
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
                # Rename the physical table from expedientes_legalentity to core_legalentity
                migrations.RunSQL(
                    'ALTER TABLE expedientes_legalentity RENAME TO core_legalentity;',
                    reverse_sql='ALTER TABLE core_legalentity RENAME TO expedientes_legalentity;',
                ),
            ],
            state_operations=[
                migrations.DeleteModel(name='LegalEntity'),
            ],
        ),
    ]
