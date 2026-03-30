# Generated manually — Sprint 20 FASE 0
# S20-01: AddField proforma FK on ExpedienteProductLine
# S20-02: AddField parent_proforma FK on ArtifactInstance
# IMPORTANT: Both are AddField ONLY — zero destructive operations
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        # Ultima migracion existente en expedientes (verificado en repo)
        ('expedientes', '0018_sprint18_fields'),
    ]

    operations = [
        # S20-01 — FK proforma en ExpedienteProductLine
        # Apunta a ArtifactInstance con artifact_type='ART-02'
        # NULL = lineas legacy pre-S20 (correcto, no hay backfill automatico)
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
                help_text='S20-01: Proforma (ART-02) a la que pertenece esta linea. NULL en lineas legacy pre-S20.',
            ),
        ),
        # S20-02 — FK self-referential parent_proforma en ArtifactInstance
        # HR-11: ART-04, ART-05, ART-09, ART-10 se vinculan via este FK
        # Excepciones (NULL): ART-01, ART-11, ART-12 (nivel expediente)
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
