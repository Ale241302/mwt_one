"""
S26-0001: Migración inicial para apps.notifications.
Crea: NotificationTemplate, NotificationAttempt, NotificationLog, CollectionEmailLog.
"""
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('expedientes', '0001_initial'),
        ('brands', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='NotificationTemplate',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=100)),
                ('template_key', models.CharField(db_index=True, max_length=50)),
                ('subject_template', models.TextField()),
                ('body_template', models.TextField()),
                ('is_active', models.BooleanField(default=True)),
                ('language', models.CharField(default='es', max_length=5)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('brand', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='notification_templates',
                    to='brands.brand'
                )),
                ('created_by', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='created_notification_templates',
                    to=settings.AUTH_USER_MODEL
                )),
            ],
            options={
                'verbose_name': 'Notification Template',
                'verbose_name_plural': 'Notification Templates',
            },
        ),
        migrations.AddConstraint(
            model_name='notificationtemplate',
            constraint=models.UniqueConstraint(
                condition=models.Q(brand__isnull=True),
                fields=['template_key', 'language'],
                name='uniq_default_template_per_key_lang'
            ),
        ),
        migrations.AddConstraint(
            model_name='notificationtemplate',
            constraint=models.UniqueConstraint(
                condition=models.Q(brand__isnull=False),
                fields=['template_key', 'brand', 'language'],
                name='uniq_brand_template_per_key_lang'
            ),
        ),
        migrations.CreateModel(
            name='NotificationAttempt',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('correlation_id', models.UUIDField(db_index=True)),
                ('recipient_email', models.EmailField()),
                ('template_key', models.CharField(blank=True, default='', max_length=50)),
                ('trigger_action_source', models.CharField(blank=True, default='', max_length=32)),
                ('status', models.CharField(choices=[
                    ('sent', 'Sent'), ('failed', 'Failed'),
                    ('skipped', 'Skipped'), ('disabled', 'Disabled')
                ], max_length=20)),
                ('error', models.TextField(blank=True, default='')),
                ('attempted_at', models.DateTimeField(auto_now_add=True)),
                ('event_log', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='notification_attempts',
                    to='expedientes.eventlog'
                )),
                ('expediente', models.ForeignKey(
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='notification_attempts',
                    to='expedientes.expediente'
                )),
                ('proforma', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='notification_attempts',
                    to='expedientes.artifactinstance'
                )),
            ],
            options={
                'verbose_name': 'Notification Attempt',
                'verbose_name_plural': 'Notification Attempts',
            },
        ),
        migrations.AddIndex(
            model_name='notificationattempt',
            index=models.Index(fields=['event_log', '-attempted_at'], name='notif_attempt_event_log_idx'),
        ),
        migrations.AddIndex(
            model_name='notificationattempt',
            index=models.Index(fields=['correlation_id'], name='notif_attempt_correlation_idx'),
        ),
        migrations.CreateModel(
            name='NotificationLog',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('correlation_id', models.UUIDField(db_index=True)),
                ('recipient_email', models.EmailField()),
                ('subject', models.TextField(default='')),
                ('body_preview', models.TextField(default='', max_length=500)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('completed_at', models.DateTimeField(blank=True, null=True)),
                ('status', models.CharField(choices=[
                    ('sent', 'Sent'), ('skipped', 'Skipped'),
                    ('disabled', 'Disabled'), ('exhausted', 'Exhausted')
                ], max_length=20)),
                ('error', models.TextField(blank=True, default='')),
                ('trigger_action_source', models.CharField(blank=True, default='', max_length=32)),
                ('template_key', models.CharField(blank=True, default='', max_length=50)),
                ('attempt_count', models.IntegerField(default=1)),
                ('event_log', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='notification_logs',
                    to='expedientes.eventlog'
                )),
                ('expediente', models.ForeignKey(
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='notification_logs',
                    to='expedientes.expediente'
                )),
                ('proforma', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='notification_logs',
                    to='expedientes.artifactinstance'
                )),
                ('template', models.ForeignKey(
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='notification_logs',
                    to='notifications.notificationtemplate'
                )),
            ],
            options={
                'verbose_name': 'Notification Log',
                'verbose_name_plural': 'Notification Logs',
            },
        ),
        migrations.AddIndex(
            model_name='notificationlog',
            index=models.Index(fields=['expediente', '-created_at'], name='notif_log_exp_idx'),
        ),
        migrations.AddIndex(
            model_name='notificationlog',
            index=models.Index(fields=['recipient_email', '-created_at'], name='notif_log_email_idx'),
        ),
        migrations.AddIndex(
            model_name='notificationlog',
            index=models.Index(fields=['correlation_id'], name='notif_log_correlation_idx'),
        ),
        migrations.AddConstraint(
            model_name='notificationlog',
            constraint=models.UniqueConstraint(
                condition=models.Q(event_log__isnull=False),
                fields=['event_log', 'recipient_email'],
                name='uniq_notification_per_event_recipient'
            ),
        ),
        migrations.CreateModel(
            name='CollectionEmailLog',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('grace_days_used', models.IntegerField()),
                ('amount_overdue', models.DecimalField(decimal_places=2, max_digits=12)),
                ('recipient_email', models.EmailField()),
                ('status', models.CharField(choices=[('sent', 'Sent'), ('failed', 'Failed')], max_length=20)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('completed_at', models.DateTimeField(blank=True, null=True)),
                ('error', models.TextField(blank=True, default='')),
                ('expediente', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='collection_email_logs',
                    to='expedientes.expediente'
                )),
                ('pago', models.ForeignKey(
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='collection_email_logs',
                    to='expedientes.expedientepago'
                )),
                ('proforma', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='collection_email_logs',
                    to='expedientes.artifactinstance'
                )),
            ],
            options={
                'verbose_name': 'Collection Email Log',
                'verbose_name_plural': 'Collection Email Logs',
                'ordering': ['-created_at'],
            },
        ),
    ]
