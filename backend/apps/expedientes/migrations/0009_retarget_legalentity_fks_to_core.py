# Deletes LegalEntity from expedientes state now that transfers/0002
# has retargeted all transfers FKs to core.legalentity.
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('expedientes', '0008_legalentity_to_core'),
        ('transfers', '0002_retarget_legalentity_fks_to_core'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.DeleteModel(name='LegalEntity'),
            ],
        ),
    ]
