"""
S26-02: Migración aditiva para ClientSubsidiary.
Agrega: contact_email (nullable) + preferred_language (nullable, default 'es').
"""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('clientes', '0004_clientsubsidiary_payment_grace_days'),
    ]

    operations = [
        migrations.AddField(
            model_name='clientsubsidiary',
            name='contact_email',
            field=models.EmailField(
                blank=True,
                null=True,
                help_text='Email de contacto para notificaciones. Si null, se salta notificación.'
            ),
        ),
        migrations.AddField(
            model_name='clientsubsidiary',
            name='preferred_language',
            field=models.CharField(
                max_length=5,
                null=True,
                blank=True,
                help_text='Idioma preferido para emails (ISO 639-1). Default: es.'
            ),
        ),
    ]
