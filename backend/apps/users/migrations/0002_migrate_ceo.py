# Sprint 8 - Data migration: migrar CEO a MWTUser
# IMPORTANTE: lista congelada — NO importar constantes del app
from django.db import migrations, connection, utils

CEO_PERMISSIONS = [
    'ask_knowledge_ops', 'ask_knowledge_products', 'ask_knowledge_pricing',
    'view_expedientes_own', 'view_expedientes_all', 'view_costos',
    'download_documents', 'manage_users',
]


def migrate_ceo(apps, schema_editor):
    OldUser = apps.get_model('auth', 'User')
    MWTUser = apps.get_model('users', 'MWTUser')
    UserPermission = apps.get_model('users', 'UserPermission')

    # Si la tabla auth_user no existe (porque el proyecto empezó con MWTUser), salimos
    from django.db import connection
    if 'auth_user' not in connection.introspection.table_names():
        return

    try:
        old = OldUser.objects.get(is_superuser=True)
    except OldUser.DoesNotExist:
        # No hay superuser previo, nada que migrar
        return
    except (OldUser.MultipleObjectsReturned, utils.ProgrammingError):
        old = OldUser.objects.filter(is_superuser=True).order_by('id').first()

    # Si ya existe el MWTUser con ese PK, no duplicar
    if MWTUser.objects.filter(id=old.id).exists():
        return

    MWTUser.objects.create(
        id=old.id,
        username=old.username,
        email=old.email,
        password=old.password,
        is_superuser=old.is_superuser,
        is_staff=old.is_staff,
        is_active=old.is_active,
        date_joined=old.date_joined,
        role='CEO',
        is_api_user=True,
    )

    for perm in CEO_PERMISSIONS:
        UserPermission.objects.get_or_create(
            user_id=old.id,
            permission=perm,
            defaults={'granted_by_id': old.id},
        )


class Migration(migrations.Migration):
    dependencies = [('users', '0001_initial')]
    operations = [migrations.RunPython(migrate_ceo, migrations.RunPython.noop)]
