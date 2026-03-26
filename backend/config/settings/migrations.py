from .base import *
import os

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db_migrations_inventario.sqlite3'),
    }
}

if 'MIGRATION_MODULES' in globals():
    del MIGRATION_MODULES
