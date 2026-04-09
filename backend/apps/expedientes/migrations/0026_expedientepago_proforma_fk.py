"""
S26-02b: Migración aditiva para ExpedientePago.
Agrega: proforma (FK nullable a ArtifactInstance tipo ART-02).
Permite resolve_collection_recipient() identificar el modo por proforma del pago.
"""
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('expedientes', '0025_add_deferred_parent_child'),
    ]

    operations = [
        migrations.AddField(
            model_name='expedientepago',
            name='proforma',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='payments',
                to='expedientes.artifactinstance',
                limit_choices_to={'artifact_type': 'ART-02'},
                help_text='S26-02b: Proforma (ART-02) asociada a este pago. Null para pagos legacy.'
            ),
        ),
    ]
