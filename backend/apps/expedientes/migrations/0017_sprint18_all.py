from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('expedientes', '0016_reopen_tracking'),
    ]
    operations = [
        migrations.AddField(
            model_name='eventlog',
            name='new_status',
            field=models.CharField(blank=True, max_length=30, null=True),
        ),
        migrations.AddField(
            model_name='eventlog',
            name='previous_status',
            field=models.CharField(blank=True, max_length=30, null=True),
        ),
        migrations.AddField(
            model_name='expediente',
            name='credit_released',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='expediente',
            name='credit_exposure',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True),
        ),
        migrations.AddField(
            model_name='expediente',
            name='incoterms',
            field=models.CharField(blank=True, max_length=32, null=True),
        ),
        migrations.AddField(
            model_name='expediente',
            name='cargo_manager',
            field=models.CharField(blank=True, max_length=20, null=True),
        ),
    ]
