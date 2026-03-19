import os
from .base import *

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': '/app/db_test.sqlite3',
    }
}

# Speed up tests
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]

CELERY_TASK_ALWAYS_EAGER = True
KNOWLEDGE_INTERNAL_TOKEN = 'test-token'

class DisableMigrations(object):
    def __contains__(self, item):
        return True

    def __getitem__(self, item):
        return None

MIGRATION_MODULES = DisableMigrations()
