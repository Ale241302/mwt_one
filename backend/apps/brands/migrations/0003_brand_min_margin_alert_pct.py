# Generated manually for S22-04
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('brands', '0002_brandconfigversion_catalogversion'),
    ]

    operations = [
        migrations.AddField(
            model_name='brand',
            name='min_margin_alert_pct',
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                help_text='Porcentaje mínimo de margen. Si el CPA cacheado cae por debajo, se genera una alerta.',
                max_digits=5,
                null=True,
            ),
        ),
    ]
