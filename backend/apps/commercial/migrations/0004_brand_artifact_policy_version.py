# Generated manually — Sprint 23, S23-04
import uuid
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('commercial', '0003_commission_rule'),
        ('brands', '__first__'),
    ]

    operations = [
        migrations.CreateModel(
            name='BrandArtifactPolicyVersion',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('version', models.PositiveIntegerField()),
                ('artifact_policy', models.JSONField(help_text='Snapshot completo de la política de artefactos para esta versión.')),
                ('is_active', models.BooleanField(default=False)),
                ('notes', models.TextField(blank=True, help_text='Notas opcionales sobre el cambio realizado en esta versión.')),
                ('brand', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='artifact_policy_versions', to='brands.brand')),
                ('superseded_by', models.ForeignKey(blank=True, help_text='Versión que reemplazó a esta.', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='supersedes', to='commercial.brandartifactpolicyversion')),
            ],
            options={'db_table': 'commercial_brand_artifact_policy_version', 'ordering': ['-version']},
        ),
        migrations.AddConstraint(
            model_name='brandartifactpolicyversion',
            constraint=models.UniqueConstraint(
                condition=models.Q(is_active=True),
                fields=['brand'],
                name='artifact_policy_unique_active_per_brand',
            ),
        ),
        migrations.AddConstraint(
            model_name='brandartifactpolicyversion',
            constraint=models.UniqueConstraint(
                fields=['brand', 'version'],
                name='artifact_policy_unique_version_per_brand',
            ),
        ),
    ]
