# core app has no concrete models at this point (TimestampMixin and AppendOnlyModel are abstract).
# This migration exists solely as a dependency anchor for 0002_legalentity.
from django.db import migrations


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = []
