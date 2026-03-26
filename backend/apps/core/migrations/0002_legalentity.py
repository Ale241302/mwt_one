# Sprint 8 fix: move LegalEntity from expedientes to core
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='LegalEntity',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('entity_id', models.CharField(help_text='e.g. MWT-CR, SONDEL-CR', max_length=50, unique=True)),
                ('legal_name', models.CharField(max_length=255)),
                ('country', models.CharField(help_text='ISO 3166-1 alpha-2/3', max_length=3)),
                ('tax_id', models.CharField(blank=True, max_length=50, null=True)),
                ('role', models.CharField(choices=[('OWNER', 'Owner'), ('DISTRIBUTOR', 'Distributor'), ('SUBDISTRIBUTOR', 'Sub-distributor'), ('THREEPL', '3PL'), ('FACTORY', 'Factory')], max_length=20)),
                ('relationship_to_mwt', models.CharField(choices=[('SELF', 'Self'), ('FRANCHISE', 'Franchise'), ('DISTRIBUTION', 'Distribution'), ('SERVICE', 'Service')], max_length=20)),
                ('frontend', models.CharField(choices=[('MWT_ONE', 'MWT.ONE'), ('PORTAL_MWT_ONE', 'Portal MWT.ONE'), ('EXTERNAL', 'External')], max_length=20)),
                ('visibility_level', models.CharField(choices=[('FULL', 'Full'), ('PARTNER', 'Partner'), ('LIMITED', 'Limited')], max_length=20)),
                ('pricing_visibility', models.CharField(choices=[('INTERNAL', 'Internal'), ('CLIENT', 'Client'), ('NONE', 'None')], max_length=20)),
                ('status', models.CharField(choices=[('ACTIVE', 'Active'), ('ONBOARDING', 'Onboarding'), ('INACTIVE', 'Inactive')], default='ONBOARDING', max_length=20)),
            ],
            options={
                'verbose_name': 'Legal Entity',
                'verbose_name_plural': 'Legal Entities',
                'ordering': ['legal_name'],
            },
        ),
    ]
