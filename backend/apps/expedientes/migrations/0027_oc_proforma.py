"""
0027 — OC Vista: crea modelo OCProforma.

Modelo simple para almacenar proformas (número + URL de archivo PDF/XLSX)
asociadas a un Expediente en el contexto de la vista de Orden de Compra (OC).
Creado desde el botón '+ Añadir Proforma' en /oc/[expediente_id].
"""
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('expedientes', '0026_expedientepago_proforma_fk'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='OCProforma',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('proforma_number', models.CharField(
                    max_length=200,
                    help_text='Número de proforma ingresado por el usuario.'
                )),
                ('file_url', models.URLField(
                    blank=True,
                    null=True,
                    max_length=1000,
                    help_text='URL del archivo proforma (PDF o XLSX). Puede ser Google Drive, S3, etc.'
                )),
                ('filename', models.CharField(
                    blank=True,
                    null=True,
                    max_length=500,
                    help_text='Nombre original del archivo subido.'
                )),
                ('file_type', models.CharField(
                    blank=True,
                    null=True,
                    max_length=10,
                    choices=[('pdf', 'PDF'), ('xlsx', 'Excel'), ('other', 'Otro')],
                    help_text='Tipo de archivo: pdf o xlsx.'
                )),
                ('notes', models.TextField(
                    blank=True,
                    null=True,
                    help_text='Notas adicionales opcionales.'
                )),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('expediente', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='oc_proformas',
                    to='expedientes.expediente',
                    help_text='Expediente (OC) al que pertenece esta proforma.'
                )),
                ('created_by', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='oc_proformas_created',
                    to=settings.AUTH_USER_MODEL,
                    help_text='Usuario que creó esta proforma.'
                )),
            ],
            options={
                'verbose_name': 'OC Proforma',
                'verbose_name_plural': 'OC Proformas',
                'ordering': ['-created_at'],
            },
        ),
    ]
