from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('clientes', '0003_clientsubsidiary_address_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='clientsubsidiary',
            name='payment_grace_days',
            field=models.PositiveIntegerField(default=0),
        ),
    ]
