# Generated manually — Sprint 20 FASE 0
# S20-01: AddField proforma FK on ExpedienteProductLine
# S20-02: AddField parent_proforma FK on ArtifactInstance
# IMPORTANT: Both are AddField ONLY — zero destructive operations
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        # Adjust to match your latest migration name in expedientes
        ('expedientes', '0019_auto_sprint19'),  # <-- UPDATE if your latest migration differs
    ]

    operations = [
        # S20-01 — FK proforma en ExpedienteProductLine
        migrations.AddField(
            model_name='expedienteproductline',
            name='proforma',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='proforma_lines',
                limit_choices_to={'artifact_type': 'ART-02'},
                to='expedientes.artifactinstance',
                help_text='S20-01: Proforma (ART-02) a la que pertenece esta línea. NULL en líneas legacy pre-S20.',
            ),
        ),
        # S20-02 — FK self-referential parent_proforma en ArtifactInstance
        migrations.AddField(
            model_name='artifactinstance',
            name='parent_proforma',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='child_artifacts',
                limit_choices_to={'artifact_type': 'ART-02'},
                to='expedientes.artifactinstance',
                help_text='S20-02 HR-11: Proforma (ART-02) a la que pertenece este artefacto.',
            ),
        ),
    ]
