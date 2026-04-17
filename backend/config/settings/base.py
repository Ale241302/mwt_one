import os
from datetime import timedelta
import environ

env = environ.Env()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load .env file
environ.Env.read_env(os.path.join(BASE_DIR, '.env'))

SECRET_KEY = env('DJANGO_SECRET_KEY')
DEBUG = env.bool('DJANGO_DEBUG', default=False)
ALLOWED_HOSTS = env.list('DJANGO_ALLOWED_HOSTS', default=[
    '127.0.0.1',
    'localhost',
    'consola.mwt.one',
    'mwt.one',
    'go.ranawalk.com',
    'django',        # nombre del servicio Docker interno (Nginx → django:8000)
])

# --- Sprint 502: Proxy Handshake ---
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
USE_X_FORWARDED_HOST = True

# --- Sprint 8: Custom user model ---
AUTH_USER_MODEL = 'users.MWTUser'

# --- INSTALLED_APPS ---
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.postgres',
    'rest_framework',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',  # S24-01: JWT blacklist
    'django_celery_beat',
    'corsheaders',
    'apps.core',
    'apps.expedientes',
    'apps.sizing',   # Sprint 18
    # Sprint 5
    'apps.transfers',
    'apps.liquidations',
    # Sprint 6
    'apps.brands',
    'apps.qr',
    # Sprint 8
    'apps.users',
    'apps.knowledge',
    # Clientes
    'apps.clientes',
    'apps.productos',
    'apps.portal',
    'apps.inventario',
    'apps.agreements',
    'apps.pricing',
    'apps.audit',
    'apps.orders',
    'apps.suppliers',
    # Sprint 23
    'apps.commercial',
    # Sprint 26
    'apps.notifications',
    # Refactor: Modulárizado
    'apps.historial',
    'apps.dashboard',
    'drf_spectacular',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'apps.core.middleware.DataAccessAuditMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# --- DATABASE: PostgreSQL 16 ---
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': env('POSTGRES_DB', default='mwt'),
        'USER': env('POSTGRES_USER', default='mwt'),
        'PASSWORD': env('POSTGRES_PASSWORD'),
        'HOST': env('POSTGRES_HOST', default='postgres'),
        'PORT': env.int('POSTGRES_PORT', default=5432),
    }
}

# --- CACHES: Redis 7 ---
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': env('REDIS_URL'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}

# --- CELERY ---
CELERY_BROKER_URL = env('CELERY_BROKER_URL')
CELERY_RESULT_BACKEND = env('CELERY_RESULT_BACKEND')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'America/Costa_Rica'

CELERY_BEAT_SCHEDULE = {
    'daily_automated_collections': {
        'task': 'apps.expedientes.tasks.automated_collection_sweep', 
        'schedule': 86400.0, # Every 24 hours, conceptually or crontab(hour=8, minute=0)
    },
}

# --- MINIO ---
MINIO_ENDPOINT = env('MINIO_ENDPOINT', default='minio:9000')
MINIO_ACCESS_KEY = env('MINIO_ROOT_USER', default='admin')
MINIO_SECRET_KEY = env('MINIO_ROOT_PASSWORD')
MINIO_SECURE = False
MINIO_BUCKET_NAME = 'mwt-documents'

# --- STATIC / MEDIA ---
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# --- LOGGING: S24-14 structured logging ---
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
        'json': {
            'format': '%(asctime)s %(levelname)s %(name)s %(message)s',
            # Usar python-json-logger si disponible; fallback a verbose
            '()': 'pythonjsonlogger.jsonlogger.JsonFormatter' if __import__('importlib').util.find_spec('pythonjsonlogger') else 'logging.Formatter',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        # S24-14: observability logger
        'mwt.observability': {
            'handlers': ['console'],
            'level': env.str('LOG_LEVEL', default='INFO'),
            'propagate': False,
        },
        'mwt.audit': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'apps.knowledge': {
            'handlers': ['console'],
            'level': env.str('LOG_LEVEL', default='INFO'),
            'propagate': False,
        },
    },
}

# --- AUTH ---
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'es'
TIME_ZONE = 'America/Costa_Rica'
USE_I18N = True
USE_TZ = True

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

LOGIN_REDIRECT_URL = '/api/portal/ceo-dashboard/'
LOGIN_URL = '/api/core/login/'

# --- CSRF / Proxy ---
CSRF_TRUSTED_ORIGINS = [
    'http://187.77.218.102:8080',
    'http://187.77.218.102:8000',
    'http://localhost:3000',
    'http://localhost:8080',
    'http://consola.mwt.one:8080',
    'https://consola.mwt.one',
    'https://mwt.one',
    'https://www.mwt.one',
    'https://go.ranawalk.com',
    'http://go.ranawalk.com',
]

# --- CORS ---
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOWED_ORIGINS = [
    'https://consola.mwt.one',
    'https://mwt.one',
    'https://www.mwt.one',
    'https://go.ranawalk.com',
    'http://go.ranawalk.com',
    'http://localhost:3000',
    'http://localhost:8080',
    'http://187.77.218.102:8080',
    'http://187.77.218.102:8000',
]

QR_SALT = env.str("QR_SALT", default="default-fallback-salt-do-not-use-in-prod-qwertyui")

# --- REST FRAMEWORK + JWT (Sprint 0 extendido en Sprint 8) ---
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        # CsrfExemptSessionAuthentication: igual que SessionAuthentication
        # pero sin enforce_csrf(), para que las API calls con session cookie
        # no fallen por CSRF token missing. El CSRF middleware de Django
        # sigue activo para /admin/ y vistas HTML normales.
        'apps.core.authentication.CsrfExemptSessionAuthentication',
    ],
    # S24-04: Rate limiting — user=60/min, anon=20/min
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '20/min',
        'user': '60/min',
        'knowledge_ask': '30/min',  # S24-04: throttle específico knowledge
    },
    'TEST_REQUEST_DEFAULT_FORMAT': 'json',
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    # S24-14: custom exception handler (loguea 429s + errores knowledge)
    'EXCEPTION_HANDLER': 'apps.knowledge.observability.custom_exception_handler',
}

SPECTACULAR_SETTINGS = {
    'TITLE': 'MWT ONE API',
    'DESCRIPTION': 'MWT Logistics Management System API',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
}

# --- S24-02: JWT Config — 30min access, 7d refresh, rotation + blacklist ---
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=30),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,
    'ALGORITHM': 'HS256',
    'AUTH_HEADER_TYPES': ('Bearer',),
    'TOKEN_OBTAIN_SERIALIZER': 'apps.users.serializers.MWTTokenObtainPairSerializer',
}

# --- S24-06: Cookie security ---
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_SAMESITE = 'Lax'
SESSION_COOKIE_AGE = 86400  # 24h
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_HTTPONLY = False
# 'None' es necesario para que el cookie CSRF se envíe en requests
# cross-origin (Next.js → Django) en HTTPS. Requiere CSRF_COOKIE_SECURE=True.
CSRF_COOKIE_SAMESITE = 'None'

# --- S24-14: Activar signal blacklist en apps ready ---
# (Ver apps/knowledge/apps.py — KnowledgeConfig.ready())

# --- Sprint 5 Tolerances ---
LIQUIDATION_AMOUNT_TOLERANCE_PCT = 0.01
LIQUIDATION_AMOUNT_TOLERANCE_ABS = 5.00
LIQUIDATION_COMMISSION_TOLERANCE_PP = 0.5

# --- Sprint 8 Knowledge ---
KNOWLEDGE_SERVICE_URL = env('KNOWLEDGE_SERVICE_URL', default='http://mwt-knowledge:8001')
KNOWLEDGE_INTERNAL_TOKEN = env('KNOWLEDGE_INTERNAL_TOKEN')

# --- Sprint 13 ---
DAI_RATES = {
    '6403.99.90': {
        'CR': 0.14,
        'CO': 0.15,
        'PE': 0.10,
    }
}
VIABILITY_FLETE_PCT = 0.05

# --- S24: Sentry (opcional, activar con SENTRY_DSN en .env) ---
_SENTRY_DSN = env.str('SENTRY_DSN', default='')
if _SENTRY_DSN:
    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration
    sentry_sdk.init(
        dsn=_SENTRY_DSN,
        integrations=[DjangoIntegration()],
        traces_sample_rate=0.1,
        send_default_pii=False,
    )

# --- S26: Email notifications settings ---
MWT_EMAIL_BACKEND = env('MWT_EMAIL_BACKEND', default='apps.notifications.backends.SMTPBackend')
DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL', default='info@mwt.one')
MWT_NOTIFICATION_ENABLED = env.bool('MWT_NOTIFICATION_ENABLED', default=False)
CEO_EMAIL = env('CEO_EMAIL', default='')
PORTAL_BASE_URL = env('PORTAL_BASE_URL', default='https://consola.mwt.one')
AWS_SES_REGION = env('AWS_SES_REGION', default='us-east-1')

# --- S26: SMTP Email Config ---
EMAIL_HOST = env('EMAIL_HOST', default='mail.mwt.one')
EMAIL_PORT = env.int('EMAIL_PORT', default=465)
EMAIL_USE_SSL = env.bool('EMAIL_USE_SSL', default=True)
EMAIL_HOST_USER = env('EMAIL_HOST_USER', default='info@mwt.one')
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD')
