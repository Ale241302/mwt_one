from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('audit', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='EventLog',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('event_type', models.CharField(db_index=True, max_length=100)),
                ('action_source', models.CharField(blank=True, max_length=100)),
                ('payload', models.JSONField(default=dict)),
                ('related_model', models.CharField(blank=True, max_length=100)),
                ('related_id', models.CharField(blank=True, max_length=100)),
                ('actor', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='event_logs',
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={'db_table': 'audit_eventlog', 'ordering': ['-created_at']},
        ),
    ]
