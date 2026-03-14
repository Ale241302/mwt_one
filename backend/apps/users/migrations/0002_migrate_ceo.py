# Sprint 8 - Data migration: migrar CEO a MWTUser
# IMPORTANTE: lista congelada — NO importar constantes del app
# FIX: auth.User está swapped por users.MWTUser — usar directamente MWTUser.
# En fresh-DB no hay superuser previo, la migración es no-op.
from django.db import migrations

CEO_PERMISSIONS = [
    'ask_knowledge_ops', 'ask_knowledge_products', 'ask_knowledge_pricing',
    'view_expedientes_own', 'view_expedientes_all', 'view_costos',
    'download_documents', 'manage_users',
]


def migrate_ceo(apps, schema_editor):
    # auth.User está swapped — acceder directo a MWTUser
    MWTUser = apps.get_model('users', 'MWTUser')
    UserPermission = apps.get_model('users', 'UserPermission')

    # En fresh-DB no hay superusers previos: no-op
    superusers = MWTUser.objects.filter(is_superuser=True)
    if not superusers.exists():
        return

    old = superusers.order_by('id').first()

    for perm in CEO_PERMISSIONS:
        UserPermission.objects.get_or_create(
            user_id=old.id,
            permission=perm,
            defaults={'granted_by_id': old.id},
        )


class Migration(migrations.Migration):
    dependencies = [('users', '0001_initial')]
    operations = [migrations.RunPython(migrate_ceo, migrations.RunPython.noop)]
