# Generated for Sprint 8 - MWTUser + UserPermission
from django.db import migrations, models
import django.contrib.auth.models
import django.contrib.auth.validators
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
        ('expedientes', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='MWTUser',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('is_superuser', models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status')),
                ('username', models.CharField(error_messages={'unique': 'A user with that username already exists.'}, help_text='Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.', max_length=150, unique=True, validators=[django.contrib.auth.validators.UnicodeUsernameValidator()], verbose_name='username')),
                ('first_name', models.CharField(blank=True, max_length=150, verbose_name='first name')),
                ('last_name', models.CharField(blank=True, max_length=150, verbose_name='last name')),
                ('email', models.EmailField(blank=True, max_length=254, verbose_name='email address')),
                ('is_staff', models.BooleanField(default=False, help_text='Designates whether the user can log into this admin site.', verbose_name='staff status')),
                ('is_active', models.BooleanField(default=True, help_text='Designates whether this user should be treated as active. Unselect this instead of deleting accounts.', verbose_name='active')),
                ('date_joined', models.DateTimeField(default=django.utils.timezone.now, verbose_name='date joined')),
                ('role', models.CharField(choices=[('CEO', 'CEO'), ('INTERNAL', 'Interno'), ('CLIENT_MARLUVAS', 'Cliente Marluvas'), ('CLIENT_TECMATER', 'Cliente Tecmater'), ('ANONYMOUS', 'An\u00f3nimo')], default='CEO', max_length=20)),
                ('whatsapp_number', models.CharField(blank=True, max_length=20, null=True)),
                ('is_api_user', models.BooleanField(default=False)),
                ('legal_entity', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='expedientes.legalentity')),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_users', to='users.mwtuser')),
                ('groups', models.ManyToManyField(blank=True, help_text='The groups this user belongs to.', related_name='user_set', related_query_name='user', to='auth.group', verbose_name='groups')),
                ('user_permissions', models.ManyToManyField(blank=True, help_text='Specific permissions for this user.', related_name='user_set', related_query_name='user', to='auth.permission', verbose_name='user permissions')),
            ],
            options={
                'verbose_name': 'Usuario MWT',
                'verbose_name_plural': 'Usuarios MWT',
            },
            managers=[
                ('objects', django.contrib.auth.models.UserManager()),
            ],
        ),
        migrations.CreateModel(
            name='UserPermission',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('permission', models.CharField(choices=[('ask_knowledge_ops', 'Ask Knowledge Ops'), ('ask_knowledge_products', 'Ask Knowledge Products'), ('ask_knowledge_pricing', 'Ask Knowledge Pricing'), ('view_expedientes_own', 'View Expedientes Own'), ('view_expedientes_all', 'View Expedientes All'), ('view_costos', 'View Costos'), ('download_documents', 'Download Documents'), ('manage_users', 'Manage Users')], max_length=50)),
                ('granted_at', models.DateTimeField(auto_now_add=True)),
                ('granted_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='granted_permissions', to='users.mwtuser')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='permissions_set', to='users.mwtuser')),
            ],
            options={
                'verbose_name': 'Permiso de Usuario',
                'verbose_name_plural': 'Permisos de Usuarios',
                'unique_together': {('user', 'permission')},
            },
        ),
    ]
