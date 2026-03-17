# Kept for migration history continuity — no-op now that 0008 handles everything.
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('expedientes', '0008_legalentity_to_core'),
        ('core', '0002_legalentity'),
    ]

    operations = []
