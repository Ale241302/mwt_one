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
    'rest_framework_simplejwt.token_blacklist',
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
    'drf_spectacular',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
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
        'PASSWORD': env('POSTGRES_PASSWORD', default=''),
        'HOST': env('POSTGRES_HOST', default='postgres'),
        'PORT': env.int('POSTGRES_PORT', default=5432),
    }
}

# --- CACHES: Redis 7 ---
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': env('REDIS_URL', default='redis://:mwt2024@redis:6379/0'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}

# --- CELERY ---
CELERY_BROKER_URL = env('CELERY_BROKER_URL', default='redis://:mwt2024@redis:6379/0')
CELERY_RESULT_BACKEND = env('CELERY_RESULT_BACKEND', default='redis://:mwt2024@redis:6379/1')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'America/Costa_Rica'

# --- MINIO ---
MINIO_ENDPOINT = env('MINIO_ENDPOINT', default='minio:9000')
MINIO_ACCESS_KEY = env('MINIO_ROOT_USER', default='admin')
MINIO_SECRET_KEY = env('MINIO_ROOT_PASSWORD', default='')
MINIO_SECURE = False
MINIO_BUCKET_NAME = 'mwt-documents'

# --- STATIC / MEDIA ---
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# --- LOGGING ---
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
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
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '30/min',
        'user': '120/min',
    },
    'TEST_REQUEST_DEFAULT_FORMAT': 'json',
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'EXCEPTION_HANDLER': 'core.exception_handler.mwt_exception_handler',
}

SPECTACULAR_SETTINGS = {
    'TITLE': 'MWT ONE API',
    'DESCRIPTION': 'MWT Logistics Management System API',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    # Otras configuraciones si se desea
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=15),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'ALGORITHM': 'HS256',
    'AUTH_HEADER_TYPES': ('Bearer',),
    'TOKEN_OBTAIN_SERIALIZER': 'apps.users.serializers.MWTTokenObtainPairSerializer',
}

# --- Sprint 5 Tolerances ---
LIQUIDATION_AMOUNT_TOLERANCE_PCT = 0.01   # +-1%
LIQUIDATION_AMOUNT_TOLERANCE_ABS = 5.00   # +-$5 USD
LIQUIDATION_COMMISSION_TOLERANCE_PP = 0.5 # +-0.5pp

# --- Sprint 8 Knowledge ---
KNOWLEDGE_SERVICE_URL = env('KNOWLEDGE_SERVICE_URL', default='http://mwt-knowledge:8001')
KNOWLEDGE_INTERNAL_TOKEN = env('KNOWLEDGE_INTERNAL_TOKEN', default='')

# --- Sprint 13 ---
DAI_RATES = {
    '6403.99.90': {
        'CR': 0.14,
        'CO': 0.15,
        'PE': 0.10,
    }
}
VIABILITY_FLETE_PCT = 0.05
