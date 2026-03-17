# Kept for migration history continuity — no-op now that transfers/0001 handles everything.
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('transfers', '0001_initial'),
        ('expedientes', '0009_retarget_legalentity_fks_to_core'),
        ('core', '0002_legalentity'),
    ]

    operations = []
