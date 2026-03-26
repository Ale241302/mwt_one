# Sprint 8 S8-06 — ConversationLog
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('expedientes', '0001_initial'),
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='ConversationLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('session_id', models.CharField(db_index=True, max_length=100)),
                ('user_role', models.CharField(max_length=20)),
                ('question', models.TextField()),
                ('answer', models.TextField()),
                ('chunks_used', models.JSONField(default=list)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('retain_until', models.DateField(blank=True, null=True)),
                ('expediente_ref', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='conversation_logs', to='expedientes.expediente')),
                ('user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='conversation_logs', to='users.mwtuser')),
            ],
            options={
                'verbose_name': 'Conversation Log',
                'verbose_name_plural': 'Conversation Logs',
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='conversationlog',
            index=models.Index(fields=['retain_until', 'created_at'], name='idx_convlog_retain_created'),
        ),
    ]
