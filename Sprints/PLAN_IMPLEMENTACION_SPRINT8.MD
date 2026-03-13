# PLAN DE IMPLEMENTACIÓN — SPRINT 8
# Auth + Knowledge Container
**Fecha:** 2026-03-13
**Autor:** Generado por Arquitecto (Claude/Perplexity) — para ejecución de Alejandro
**Repositorio:** https://github.com/Ale241302/mwt_one
**Fuentes:** LOTE_SM_SPRINT8_v3_15.md · GUIA_SPRINT8_ALEJANDRO.md · ASANA_TASK_SPRINT8.md
**Estado:** LISTO PARA EJECUCIÓN

---

## Resumen ejecutivo

Sprint 8 tiene **dos pilares en secuencia estricta A → B**. No se puede iniciar Pilar B sin que Pilar A esté 100% done.

| Pilar | Alcance | Items |
|-------|---------|-------|
| **A — Identidad** | MWTUser, permisos granulares, JWT extendido, ConversationLog | 1–6 |
| **B — Knowledge** | Docker `mwt-knowledge`, pgvector, indexer, FastAPI, Redis multi-turn | 7–13 |
| **Soporte** | DevOps docker-compose, QA tests, Verificaciones arquitectura | 11, 12–13, 14 |

**El frontend de Sprint 7 NO se toca. Knowledge es API-only en Sprint 8.**

---

## ANTES DE EMPEZAR — 3 verificaciones obligatorias

> ⚠️ Ejecutar **antes de escribir una sola línea de código**. Si alguna falla, parar y reportar al CEO.

### ✅ Verificación 1: Inventario FKs a `auth.User`
```bash
grep -rn "ForeignKey.*User\|auth.User" apps/
```
Lista esperada (mínimo):
- `EventLog.triggered_by` (Sprint 1)
- `ArtifactInstance.created_by` (Sprint 1–2)
- `Transfer.created_by` (Sprint 5)

Si aparecen campos adicionales en apps propias → agregarlos a la lista de migraciones del **Paso 7 de Item 1**, **nunca** a `users/0002_migrate_ceo.py`.

### ✅ Verificación 2: FKs contrib de Django
```bash
grep -rn "ForeignKey.*User\|auth.User" $(python -c "import django; print(django.__path__[0])")/contrib/
```
La única relevante: `django.contrib.admin` → `LogEntry.user`. **No migrar** el histórico de `django_admin_log` — queda fuera de alcance Sprint 8.

### ✅ Verificación 3: Celery Beat scheduler
Verificar `docker-compose.yml`. Si tiene `--scheduler django_celery_beat.schedulers:DatabaseScheduler` → **eliminarlo**:

```yaml
# ANTES (si existe):
celery-beat:
  command: celery -A config beat --scheduler django_celery_beat.schedulers:DatabaseScheduler

# DESPUÉS:
celery-beat:
  command: celery -A config beat -l info
```

Sin este cambio, las tasks de `app.conf.beat_schedule` se ignoran silenciosamente (D-04).

---

## Árbol de dependencias

```
[V1, V2, V3] Verificaciones obligatorias
       │
       ▼
Item 1: MWTUser (modelo + migración CEO)           → branch: feature/s8-01-mwtuser
  ├── Item 2: UserPermission (mismo branch)
  ├── Item 3: JWT extendido                         → branch: feature/s8-03-jwt-extended
  │     └── Item 4: Decoradores @require_permission
  │           └── Item 5: API Admin Usuarios        → branch: feature/s8-05-admin-users-api
  └── Item 6: ConversationLog + retención           → branch: feature/s8-06-conversation-log
          │
          ▼
Item 7: Schema PostgreSQL (pgvector + tablas)       → branch: feature/s8-07-knowledge-service
  └── Item 8: Docker service mwt-knowledge
        ├── Item 9:  Watcher (watchdog)
        ├── Item 10: Indexer (chunking + embeddings)
        ├── Item 11: FastAPI endpoints internos
        └── Item 12: Sesiones Redis
              └── Item 13: Django proxy /api/knowledge/
                    ├── Item 14 QA Pilar A          → branch: feature/s8-12-tests-pilar-a
                    └── Item 15 QA Pilar B          → branch: feature/s8-13-tests-pilar-b
                          │
                          ▼
                    Item 16: Verificaciones Arquitectura Pre-Deploy
                             → branch: feature/s8-14-arch-verification
```

---

## PILAR A — IDENTIDAD

---

### Item 1: MWTUser — Modelo + Migración CEO
**Branch:** `feature/s8-01-mwtuser`
**Dependencia:** Verificaciones 1, 2, 3 aprobadas

#### Archivos a crear:
- `apps/users/__init__.py`
- `apps/users/apps.py`
- `apps/users/models.py`
- `apps/users/migrations/0001_initial.py` (autogenerado)
- `apps/users/migrations/0002_migrate_ceo.py` (manual)

#### Archivos a modificar:
- `config/settings.py` → agregar `AUTH_USER_MODEL = 'users.MWTUser'` y añadir `'apps.users'` a `INSTALLED_APPS`

#### Código `apps/users/models.py`:

```python
from django.contrib.auth.models import AbstractUser
from django.db import models


class UserRole(models.TextChoices):
    CEO             = 'CEO',             'CEO'
    INTERNAL        = 'INTERNAL',        'Interno'
    CLIENT_MARLUVAS = 'CLIENT_MARLUVAS', 'Cliente Marluvas'
    CLIENT_TECMATER = 'CLIENT_TECMATER', 'Cliente Tecmater'
    ANONYMOUS       = 'ANONYMOUS',       'Anónimo'


class Permission(models.TextChoices):
    ASK_KNOWLEDGE_OPS      = 'ask_knowledge_ops',      'Ask Knowledge Ops'
    ASK_KNOWLEDGE_PRODUCTS = 'ask_knowledge_products', 'Ask Knowledge Products'
    ASK_KNOWLEDGE_PRICING  = 'ask_knowledge_pricing',  'Ask Knowledge Pricing'
    VIEW_EXPEDIENTES_OWN   = 'view_expedientes_own',   'Ver Expedientes Propios'
    VIEW_EXPEDIENTES_ALL   = 'view_expedientes_all',   'Ver Todos los Expedientes'
    VIEW_COSTOS            = 'view_costos',            'Ver Costos'
    DOWNLOAD_DOCUMENTS     = 'download_documents',     'Descargar Documentos'
    MANAGE_USERS           = 'manage_users',           'Gestionar Usuarios'


ROLE_PERMISSION_CEILING = {
    UserRole.CEO: [
        Permission.ASK_KNOWLEDGE_OPS, Permission.ASK_KNOWLEDGE_PRODUCTS,
        Permission.ASK_KNOWLEDGE_PRICING, Permission.VIEW_EXPEDIENTES_OWN,
        Permission.VIEW_EXPEDIENTES_ALL, Permission.VIEW_COSTOS,
        Permission.DOWNLOAD_DOCUMENTS, Permission.MANAGE_USERS,
    ],
    UserRole.INTERNAL: [
        Permission.ASK_KNOWLEDGE_OPS, Permission.ASK_KNOWLEDGE_PRODUCTS,
        Permission.VIEW_EXPEDIENTES_ALL, Permission.VIEW_COSTOS,
        Permission.DOWNLOAD_DOCUMENTS,
    ],
    UserRole.CLIENT_MARLUVAS: [
        Permission.ASK_KNOWLEDGE_OPS, Permission.ASK_KNOWLEDGE_PRODUCTS,
        Permission.VIEW_EXPEDIENTES_OWN, Permission.DOWNLOAD_DOCUMENTS,
    ],
    UserRole.CLIENT_TECMATER: [
        Permission.ASK_KNOWLEDGE_OPS, Permission.ASK_KNOWLEDGE_PRODUCTS,
        Permission.VIEW_EXPEDIENTES_OWN, Permission.DOWNLOAD_DOCUMENTS,
    ],
    UserRole.ANONYMOUS: [],
}


class MWTUser(AbstractUser):
    role            = models.CharField(max_length=20, choices=UserRole.choices, default=UserRole.CEO)
    # D-01: FK directa a LegalEntity existente (Sprint 5) — nunca crear LegalEntityRef
    legal_entity    = models.ForeignKey(
        'core.LegalEntity', null=True, blank=True, on_delete=models.SET_NULL
    )
    whatsapp_number = models.CharField(max_length=20, null=True, blank=True)
    is_api_user     = models.BooleanField(default=False)
    created_by      = models.ForeignKey(
        'self', null=True, blank=True, on_delete=models.SET_NULL, related_name='created_users'
    )

    def has_permission(self, perm: str) -> bool:
        ceiling = ROLE_PERMISSION_CEILING.get(self.role, [])
        if perm not in ceiling:
            return False
        return self.permissions_set.filter(permission=perm).exists()

    class Meta:
        db_table = 'users_mwtuser'


class UserPermission(models.Model):
    user       = models.ForeignKey(MWTUser, on_delete=models.CASCADE, related_name='permissions_set')
    permission = models.CharField(max_length=50, choices=Permission.choices)
    granted_by = models.ForeignKey(MWTUser, on_delete=models.SET_NULL, null=True, related_name='granted_permissions')
    granted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'permission')

    def save(self, *args, **kwargs):
        from django.core.exceptions import ValidationError
        ceiling = ROLE_PERMISSION_CEILING.get(self.user.role, [])
        if self.permission not in ceiling:
            raise ValidationError(
                f"Permiso '{self.permission}' excede el techo del rol '{self.user.role}'"
            )
        super().save(*args, **kwargs)
```

#### Secuencia de migración (orden estricto):
1. `python manage.py startapp users` → mover a `apps/users/`
2. Definir ambos modelos `MWTUser` + `UserPermission` en `apps/users/models.py`
3. Activar `AUTH_USER_MODEL = 'users.MWTUser'` en `settings.py` **en el mismo commit** que la definición del modelo — antes de cualquier migración
4. `python manage.py makemigrations users` → genera `0001_initial`
5. `python manage.py migrate users` → aplica `0001_initial`
6. Crear `apps/users/migrations/0002_migrate_ceo.py`:

```python
# apps/users/migrations/0002_migrate_ceo.py
# IMPORTANTE: lista congelada — NO importar constantes del app
# Si ROLE_PERMISSION_CEILING cambia en el futuro, esta migración debe quedar intacta
CEO_PERMISSIONS = [
    'ask_knowledge_ops', 'ask_knowledge_products', 'ask_knowledge_pricing',
    'view_expedientes_own', 'view_expedientes_all', 'view_costos',
    'download_documents', 'manage_users',
]

from django.db import migrations


def migrate_ceo(apps, schema_editor):
    OldUser = apps.get_model('auth', 'User')
    MWTUser = apps.get_model('users', 'MWTUser')
    UserPermission = apps.get_model('users', 'UserPermission')
    old = OldUser.objects.get(is_superuser=True)
    MWTUser.objects.create(
        id=old.id,              # preservar PK — crítico (D-08)
        username=old.username,
        email=old.email,
        password=old.password,
        is_superuser=old.is_superuser,
        is_staff=old.is_staff,
        is_active=old.is_active,
        date_joined=old.date_joined,
        role='CEO',
        is_api_user=True,       # D-08: CEO siempre is_api_user=True
    )
    for perm in CEO_PERMISSIONS:
        UserPermission.objects.create(
            user_id=old.id,
            permission=perm,
            granted_by_id=old.id,
        )


class Migration(migrations.Migration):
    dependencies = [('users', '0001_initial')]
    operations = [migrations.RunPython(migrate_ceo, migrations.RunPython.noop)]
```

7. `python manage.py migrate users` → aplica `0002_migrate_ceo`
8. Generar y aplicar migraciones de apps con FK a `auth.User` (Verificación 1):
   `python manage.py makemigrations` → `python manage.py migrate`
9. `python manage.py check` sin errores → login CEO funciona → Django Admin accesible

#### Criterios de DONE:
- [ ] App `users` creada y en `INSTALLED_APPS`
- [ ] `MWTUser` con todos los campos incluyendo FK a `LegalEntity`
- [ ] `AUTH_USER_MODEL = 'users.MWTUser'` activo
- [ ] CEO migrado con `role=CEO`, `is_api_user=True`, 8 `UserPermission`
- [ ] **PK preservado:** `MWTUser.objects.get(username=CEO_USERNAME).id == old_auth_user.id`
- [ ] Migraciones de FKs en apps existentes aplicadas
- [ ] `python manage.py check` sin errores
- [ ] Login CEO en consola funciona post-migración
- [ ] Admin login funciona con `MWTUser`

---

### Item 2: UserPermission — Modelo + Validación Techo
**Branch:** `feature/s8-01-mwtuser` (mismo PR que Item 1)
**Dependencia:** Item 1 aprobado

El modelo `UserPermission` ya se define en `apps/users/models.py` junto con `MWTUser` (Paso 2 de Item 1). Solo verificar que:
- `save()` implementa validación de techo
- `unique_together = ('user', 'permission')` presente
- CEO tiene sus 8 permisos pre-asignados por `users/0002`

#### Criterios de DONE:
- [ ] Modelo creado y migrado (en `0001_initial` con MWTUser)
- [ ] `save()` valida techo: permiso fuera del techo del rol → `ValidationError`
- [ ] CEO tiene todos sus permisos (creados por `users/0002`)

---

### Item 3: JWT Extendido — Serializer + Guardia `is_api_user`
**Branch:** `feature/s8-03-jwt-extended`
**Dependencia:** Item 1 aprobado

> ⚠️ D-03: El endpoint `POST /api/auth/token/` **ya existe** (Sprint 0). Solo modificar el serializer — no crear endpoint nuevo.

#### Archivos a crear:
- `apps/users/serializers.py`

#### Archivos a modificar:
- `config/settings.py` → actualizar `SIMPLE_JWT` y apuntar `TOKEN_OBTAIN_SERIALIZER`
- `apps/users/urls.py` (o el archivo donde está registrado el endpoint de token)

#### Código `apps/users/serializers.py`:

```python
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework.exceptions import AuthenticationFailed


class MWTTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        # Preserva: user_id (Sprint 0). Añade: role, legal_entity_id, permissions[]
        token['role'] = user.role
        token['legal_entity_id'] = str(user.legal_entity_id) if user.legal_entity_id else None
        token['permissions'] = list(user.permissions_set.values_list('permission', flat=True))
        return token

    def validate(self, attrs):
        # Paso 1: autenticar credenciales — super().validate() autentica y asigna self.user
        data = super().validate(attrs)
        # Paso 2: guardia is_api_user — rechazar ANTES de devolver tokens
        if not self.user.is_api_user:
            raise AuthenticationFailed({
                'error': 'api_access_not_enabled',
                'detail': 'Este usuario no tiene acceso JWT habilitado.'
            })
        # Paso 3: devolver tokens solo si la guardia pasó
        return data
```

#### Configuración en `settings.py`:
```python
from datetime import timedelta

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=8),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=30),
    'ALGORITHM': 'HS256',
}

# Apuntar la view de token al nuevo serializer
REST_FRAMEWORK = {
    ...
}
```

#### Criterios de DONE:
- [ ] View `POST /api/auth/token/` usa `MWTTokenObtainPairSerializer`
- [ ] JWT payload incluye `user_id` (Sprint 0, preservado), `role`, `legal_entity_id`, `permissions[]`
- [ ] `is_api_user=False` → 401 `AuthenticationFailed`
- [ ] Test: access token emitido contiene todos los claims
- [ ] Sesión web CEO no se toca

---

### Item 4: Decoradores `@require_permission` (Session + JWT)
**Branch:** `feature/s8-03-jwt-extended`
**Dependencia:** Items 1–3 aprobados

#### Archivos a crear:
- `apps/users/decorators.py`
- `apps/users/mixins.py`

#### Código `apps/users/decorators.py`:

```python
from django.http import JsonResponse
from .models import Permission


# Camino A — Session (consola, endpoints /api/admin/)
def require_permission(perm: str):
    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return JsonResponse({'error': 'auth_required'}, status=401)
            if not request.user.has_permission(perm):
                return JsonResponse({'error': 'permission_denied', 'required': perm}, status=403)
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


# Camino B — JWT (endpoints /api/knowledge/ — sin DB lookup)
# D-JWT: request.auth es el payload decodificado como dict.
# SIEMPRE usar request.auth.get() — NUNCA getattr(request.auth, 'payload', {})
def require_permission_jwt(perm: str):
    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return JsonResponse({'error': 'auth_required'}, status=401)
            token_permissions = request.auth.get('permissions', [])
            if perm not in token_permissions:
                return JsonResponse({'error': 'permission_denied', 'required': perm}, status=403)
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator
```

#### Código `apps/users/mixins.py`:

```python
from django.http import JsonResponse
from .models import Permission


class PermissionRequiredMixin:
    """Mixin class-based — Session auth (para /api/admin/)"""
    required_permission = None

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'auth_required'}, status=401)
        if self.required_permission and not request.user.has_permission(self.required_permission):
            return JsonResponse({'error': 'permission_denied', 'required': self.required_permission}, status=403)
        return super().dispatch(request, *args, **kwargs)


class JWTPermissionRequiredMixin:
    """Mixin class-based — JWT auth (para /api/knowledge/)"""
    required_permission = None

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'auth_required'}, status=401)
        if self.required_permission:
            token_permissions = request.auth.get('permissions', [])
            if self.required_permission not in token_permissions:
                return JsonResponse({'error': 'permission_denied', 'required': self.required_permission}, status=403)
        return super().dispatch(request, *args, **kwargs)
```

#### Criterios de DONE:
- [ ] Ambos decoradores implementados en `apps/users/decorators.py`
- [ ] Mixins class-based en `apps/users/mixins.py`
- [ ] Endpoints `/api/knowledge/` usan exclusivamente `require_permission_jwt`

---

### Item 5: API Admin Usuarios — CRUD + Permisos
**Branch:** `feature/s8-05-admin-users-api`
**Dependencia:** Items 1–4 aprobados

#### Archivos a crear:
- `apps/users/views.py` (endpoints admin)
- `apps/users/urls.py` (si no existe)

#### Archivos a modificar:
- `config/urls.py` → incluir `apps/users/urls.py` bajo `/api/admin/`

#### Endpoints a implementar:

| Método | Path | Auth | Descripción |
|--------|------|------|-------------|
| POST | `/api/admin/users/` | Session + MANAGE_USERS | Crear usuario (cero permisos) |
| GET | `/api/admin/users/` | Session + MANAGE_USERS | Listar todos |
| GET | `/api/admin/users/{id}/` | Session + MANAGE_USERS | Detalle con permisos |
| GET | `/api/admin/users/{id}/permissions/` | Session + MANAGE_USERS | Ver permisos |
| PATCH | `/api/admin/users/{id}/permissions/` | Session + MANAGE_USERS | Reemplazar permisos |

#### Contrato PATCH permisos:
1. `ceiling = ROLE_PERMISSION_CEILING[user.role]`
2. `accepted = requested ∩ ceiling`
3. `rejected = requested - ceiling`
4. **Guardia last admin:** si el reemplazo dejaría la plataforma sin ningún usuario activo con `MANAGE_USERS` → **400** `cannot_remove_last_manage_users`
5. DELETE todos los `UserPermission` del usuario → INSERT atómico de `accepted` con `granted_by=request.user`
6. Response 200:
```json
{
  "permissions_applied": ["ask_knowledge_ops", "view_expedientes_own"],
  "permissions_rejected": ["view_costos"]
}
```

#### Criterios de DONE:
- [ ] CRUD usuarios funcionando
- [ ] Password hasheado con `make_password()`
- [ ] `legal_entity_id` valida contra `LegalEntity` existente
- [ ] Usuario nuevo creado con cero `UserPermission`
- [ ] Cada `UserPermission` insertado tiene `granted_by=request.user`
- [ ] Self-patch CEO quitando `MANAGE_USERS` → 400
- [ ] Patch a tercero que dejaría plataforma sin `MANAGE_USERS` → 400
- [ ] Response PATCH incluye `permissions_applied` y `permissions_rejected`
- [ ] PATCH es transacción atómica (DELETE todos + INSERT accepted)

---

### Item 6: ConversationLog + Retención + Signal + Beat Task
**Branch:** `feature/s8-06-conversation-log`
**Dependencia:** Item 1 aprobado

> ⚠️ D-09: ConversationLog en expediente BLOQUEADO (C17) **es permitido**. No verificar estado del expediente antes de crear el log.
> ⚠️ D-10: Signal `retain_until` usa `transaction.on_commit()` obligatoriamente.

#### Archivos a crear:
- `apps/knowledge/__init__.py`
- `apps/knowledge/apps.py`
- `apps/knowledge/models.py`
- `apps/knowledge/utils.py`
- `apps/knowledge/signals.py`
- `apps/knowledge/tasks.py`
- `apps/knowledge/migrations/0001_initial.py` (autogenerado)

#### Archivos a modificar:
- `config/settings.py` → añadir `'apps.knowledge'` a `INSTALLED_APPS`
- `config/celery.py` → añadir `purge_expired_logs` a `app.conf.beat_schedule`
- `docker-compose.yml` → eliminar `--scheduler DatabaseScheduler` de `celery-beat` (si existe)

#### Código `apps/knowledge/models.py`:

```python
from django.db import models
from apps.users.models import MWTUser


RETENTION_DAYS = {
    'CEO': 365,
    'CLIENT_MARLUVAS': 365,
    'CLIENT_TECMATER': 365,
    'INTERNAL': 90,
    'ANONYMOUS': 30,
}


class ConversationLog(models.Model):
    session_id     = models.CharField(max_length=64, db_index=True)
    user           = models.ForeignKey(MWTUser, null=True, on_delete=models.SET_NULL)
    user_role      = models.CharField(max_length=20)
    expediente_ref = models.ForeignKey(
        'expedientes.Expediente', null=True, blank=True, on_delete=models.SET_NULL
    )
    question       = models.TextField()
    answer         = models.TextField()
    chunks_used    = models.JSONField(default=list)
    created_at     = models.DateTimeField(auto_now_add=True)
    retain_until   = models.DateField(null=True)

    class Meta:
        db_table = 'knowledge_conversation_log'
        indexes = [
            models.Index(fields=['retain_until', 'created_at']),
        ]
```

#### Código `apps/knowledge/utils.py`:

```python
from datetime import timedelta
from .models import RETENTION_DAYS


def calculate_retention(user_role, expediente_ref=None, as_of_date=None):
    """
    Única fuente de verdad para el cálculo de retención.
    as_of_date es OBLIGATORIO — no usar timezone.now() implícito.
    """
    if as_of_date is None:
        raise ValueError("calculate_retention: as_of_date es obligatorio")

    if expediente_ref is None:
        return as_of_date + timedelta(days=RETENTION_DAYS.get(user_role, 30))

    if expediente_ref.status != 'CERRADO':
        return None  # Retención pendiente hasta que se cierre el expediente

    if expediente_ref.closed_at is None:
        raise ValueError(
            f"calculate_retention: Expediente {expediente_ref.pk} tiene status=CERRADO pero closed_at es None"
        )

    return expediente_ref.closed_at.date() + timedelta(days=365)
```

#### Código `apps/knowledge/signals.py`:

```python
from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver
from datetime import timedelta


@receiver(post_save, sender='expedientes.Expediente')
def update_conversation_retention(sender, instance, **kwargs):
    """
    D-10: Obligatoriamente usa transaction.on_commit()
    D-09: Solo actualiza logs existentes — nunca bloquea la creación de nuevos
    """
    if instance.status == 'CERRADO':
        if instance.closed_at is None:
            raise ValueError(
                f"calculate_retention: Expediente {instance.pk} tiene status=CERRADO pero closed_at es None"
            )

        def _update():
            from .models import ConversationLog
            ConversationLog.objects.filter(
                expediente_ref=instance,
                retain_until__isnull=True
            ).update(retain_until=instance.closed_at.date() + timedelta(days=365))

        transaction.on_commit(_update)  # OBLIGATORIO — nunca sin on_commit
```

#### Código `apps/knowledge/tasks.py`:

```python
from celery import shared_task
from django.utils import timezone


@shared_task
def purge_expired_logs():
    """Elimina logs de conversación con retain_until pasado. Corre a las 3am diario."""
    from .models import ConversationLog
    today = timezone.now().date()
    deleted, _ = ConversationLog.objects.filter(
        retain_until__isnull=False,
        retain_until__lt=today
    ).delete()
    return {'deleted': deleted}
```

#### Actualización `config/celery.py`:

```python
# Agregar a app.conf.beat_schedule (preservar tasks existentes de Sprint 2)
app.conf.beat_schedule = {
    # Existentes Sprint 2 — NO TOCAR
    'evaluate_credit_clocks': { ... },    # preservar exacto
    'process_pending_events': { ... },    # preservar exacto
    # Nuevo Sprint 8
    'purge_expired_logs': {
        'task': 'apps.knowledge.tasks.purge_expired_logs',
        'schedule': crontab(hour=3, minute=0),  # 3am diario
    },
}
```

#### Criterios de DONE:
- [ ] Modelo `ConversationLog` creado y migrado
- [ ] `calculate_retention()` en `apps/knowledge/utils.py` como única fuente de verdad
- [ ] Signal con `transaction.on_commit()` — no sin él
- [ ] `purge_expired_logs` en `app.conf.beat_schedule` junto a tasks existentes Sprint 2
- [ ] `--scheduler DatabaseScheduler` eliminado de `docker-compose.yml`
- [ ] `docker compose logs celery-beat` muestra 3 tasks
- [ ] Índice `(retain_until, created_at)` creado

---

## PILAR B — KNOWLEDGE CONTAINER

---

### Item 7: Schema PostgreSQL — pgvector + Tablas
**Branch:** `feature/s8-07-knowledge-service`
**Dependencia:** Item 6 aprobado (ConversationLog existe)

> ✅ D-06: `CREATE EXTENSION vector` en DB `mwt` — no afecta DB `paperless`.

#### Archivos a crear:
- `apps/knowledge/migrations/0002_knowledge_schema.py` (migración Django con RunSQL)

#### SQL a ejecutar (vía migración Django):

```sql
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS knowledge_chunks (
  id              SERIAL PRIMARY KEY,
  source_file     VARCHAR(255) NOT NULL,
  section         VARCHAR(100),
  chunk_index     INTEGER NOT NULL,
  content         TEXT NOT NULL,
  embedding       vector(1536),
  doc_type        VARCHAR(10),
  domain          VARCHAR(50),
  visibility      VARCHAR(20) NOT NULL,
  stamp           VARCHAR(20) NOT NULL,
  version         VARCHAR(10),
  is_pricing      BOOLEAN NOT NULL DEFAULT false,
  embedding_model VARCHAR(50) NOT NULL,
  source_hash     VARCHAR(64) NOT NULL,
  indexed_at      TIMESTAMPTZ DEFAULT now(),
  UNIQUE (source_file, chunk_index)
);

CREATE INDEX IF NOT EXISTS knowledge_chunks_embedding_hnsw
  ON knowledge_chunks USING hnsw (embedding vector_cosine_ops)
  WITH (m=16, ef_construction=64);

CREATE INDEX IF NOT EXISTS knowledge_chunks_filters
  ON knowledge_chunks (visibility, stamp, domain, is_pricing);

CREATE INDEX IF NOT EXISTS knowledge_chunks_source
  ON knowledge_chunks (source_file, source_hash);

CREATE TABLE IF NOT EXISTS indexation_log (
  id              SERIAL PRIMARY KEY,
  source_file     VARCHAR(255) NOT NULL,
  status          VARCHAR(20) NOT NULL,
  reason          TEXT,
  chunks_created  INTEGER DEFAULT 0,
  embedding_model VARCHAR(50),
  indexed_at      TIMESTAMPTZ DEFAULT now()
);
```

#### Criterios de DONE:
- [ ] Extensión `vector` activa en DB `mwt`
- [ ] Tabla `knowledge_chunks` con índice HNSW
- [ ] Tabla `indexation_log` creada
- [ ] Migración aplica sin tocar tablas de expedientes

---

### Item 8: Docker Service `mwt-knowledge`
**Branch:** `feature/s8-07-knowledge-service`
**Dependencia:** Item 7 aprobado

#### Archivos a crear:
```
services/mwt-knowledge/
├── Dockerfile
├── entrypoint.sh
├── requirements.txt
├── main.py          (FastAPI — Item 11)
├── watcher.py       (Watcher — Item 9)
├── indexer.py       (Indexer — Item 10)
└── sessions.py      (Sesiones Redis — Item 12)
knowledge-docs/
└── .gitkeep
```

#### `services/mwt-knowledge/Dockerfile`:

```dockerfile
FROM python:3.12-slim
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev gcc curl && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN chmod +x entrypoint.sh
ENTRYPOINT ["./entrypoint.sh"]
```

#### `services/mwt-knowledge/entrypoint.sh`:

```bash
#!/bin/bash
set -e
echo "[mwt-knowledge] Iniciando watcher en background..."
python watcher.py &
echo "[mwt-knowledge] Iniciando FastAPI en :8001..."
exec uvicorn main:app --host 0.0.0.0 --port 8001 --workers 1
```

#### `services/mwt-knowledge/requirements.txt`:

```
fastapi
uvicorn
watchdog
psycopg2-binary>=2.9
pgvector
openai
anthropic
redis
tiktoken
httpx
```

#### Bloque a agregar en `docker-compose.yml`:

```yaml
  mwt-knowledge:
    build: ./services/mwt-knowledge
    container_name: mwt-knowledge
    restart: unless-stopped
    volumes:
      - ./knowledge-docs:/docs:ro
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - EMBEDDING_MODEL=text-embedding-3-small
      - KNOWLEDGE_INTERNAL_TOKEN=${KNOWLEDGE_INTERNAL_TOKEN}
      - MIN_SIMILARITY=0.5
      - LOG_LEVEL=INFO
    networks:
      - mwt-internal
    depends_on:
      - db
      - redis
    # Sin ports — no expuesto al exterior (solo red Docker interna)
```

#### Variables nuevas en `.env` y `.env.template`:

```
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
KNOWLEDGE_INTERNAL_TOKEN=<32 chars aleatorio>
KNOWLEDGE_SERVICE_URL=http://mwt-knowledge:8001
MIN_SIMILARITY=0.5
```

#### Criterios de DONE:
- [ ] Dockerfile y entrypoint.sh creados
- [ ] Servicio en `docker-compose.yml`
- [ ] `./knowledge-docs/.gitkeep` creado
- [ ] `docker compose up mwt-knowledge` → logs: "Iniciando watcher..." + "Iniciando FastAPI en :8001"

---

### Item 9: Watcher (`watchdog`)
**Branch:** `feature/s8-07-knowledge-service`

#### Archivo: `services/mwt-knowledge/watcher.py`

Comportamiento:
- Monitorea `/docs/` recursivamente con `watchdog`
- Solo archivos `.md`
- Eventos `FileCreatedEvent`, `FileModifiedEvent` → llama `indexer.index_file(path)`
- `FileDeletedEvent` → DELETE chunks del archivo + log REJECTED con `reason: archivo eliminado`
- Debounce 2s por archivo (evitar doble indexación)
- Al iniciar: scan inicial de todos los `.md` en `/docs/`

```python
import time
import os
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import indexer


class KBHandler(FileSystemEventHandler):
    def __init__(self):
        self._debounce = {}

    def _should_process(self, path: str) -> bool:
        if not path.endswith('.md'):
            return False
        now = time.time()
        last = self._debounce.get(path, 0)
        if now - last < 2.0:
            return False
        self._debounce[path] = now
        return True

    def on_created(self, event):
        if not event.is_directory and self._should_process(event.src_path):
            indexer.index_file(event.src_path)

    def on_modified(self, event):
        if not event.is_directory and self._should_process(event.src_path):
            indexer.index_file(event.src_path)

    def on_deleted(self, event):
        if not event.is_directory and event.src_path.endswith('.md'):
            indexer.delete_file(event.src_path)


def initial_scan(docs_path: str):
    for root, _, files in os.walk(docs_path):
        for f in files:
            if f.endswith('.md'):
                indexer.index_file(os.path.join(root, f))


if __name__ == '__main__':
    docs_path = '/docs'
    print(f"[watcher] Scan inicial de {docs_path}...")
    initial_scan(docs_path)
    print("[watcher] Iniciando monitoreo continuo...")
    observer = Observer()
    observer.schedule(KBHandler(), docs_path, recursive=True)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
```

---

### Item 10: Indexer (Chunking + Embeddings)
**Branch:** `feature/s8-07-knowledge-service`

#### Archivo: `services/mwt-knowledge/indexer.py`

**Reglas de validación del header canónico** (primeras 10 líneas del `.md`):

| Campo | Válido | Si falla |
|-------|--------|----------|
| `status` | `VIGENTE` | REJECTED: `invalid_status:{valor}` |
| `stamp` | `VIGENTE` | REJECTED: `stamp_not_vigente` |
| `visibility` | `PUBLIC`, `INTERNAL`, `CEO-ONLY` | REJECTED: `invalid_visibility:{valor}` |
| `domain` | cualquier string no vacío | REJECTED: `domain_empty` |
| `version` | semver o string no vacío | REJECTED: `version_empty` |

Post-validación: `visibility=CEO-ONLY` → REJECTED `ceo_only_excluded` (D-13).

**`is_pricing`** = `true` si `source_file` contiene `ENT_COMERCIAL_PRICING`, `ENT_COMERCIAL_COSTOS`, `ENT_COMERCIAL_FINANZAS`, o si `domain` es `Pricing` o `Costos`.

**Chunking:** secciones `##` → máx 600 tokens por chunk (tiktoken) → batches de 100 para embeddings.

**Persistencia — transacción atómica:**
```sql
-- SUCCESS (upsert seguro):
BEGIN;
DELETE FROM knowledge_chunks WHERE source_file = :source_file;
INSERT INTO knowledge_chunks (...) VALUES (...);
INSERT INTO indexation_log (..., status='SUCCESS');
COMMIT;

-- REJECTED (incluyendo re-index de archivo que antes era válido):
BEGIN;
DELETE FROM knowledge_chunks WHERE source_file = :source_file;  -- limpiar fantasmas
INSERT INTO indexation_log (..., status='REJECTED', reason=:reason);
COMMIT;
```

**Estados de salida:**

| Estado | Chunks en DB | indexation_log |
|--------|-------------|----------------|
| SUCCESS | Nuevos chunks | status=SUCCESS |
| REJECTED | 0 (previos borrados) | status=REJECTED + reason |
| SKIPPED | Sin cambio (hash igual) | status=SKIPPED |
| FAILED | Sin cambio (rollback) | status=FAILED |

---

### Item 11: FastAPI Endpoints Internos
**Branch:** `feature/s8-07-knowledge-service`

#### Archivo: `services/mwt-knowledge/main.py`

**Auth:** Header `X-Internal-Token = KNOWLEDGE_INTERNAL_TOKEN`. Sin header o token incorrecto → 401.
**Excepción:** `GET /status/` no requiere token.

#### Endpoints FastAPI internos:

| Método | Path | Auth | Descripción |
|--------|------|------|-------------|
| GET | `/status/` | Sin auth | Health check |
| POST | `/search/` | X-Internal-Token | Búsqueda semántica pgvector |
| POST | `/ask/` | X-Internal-Token | Pregunta con Claude |
| POST | `/reindex/` | X-Internal-Token | Re-indexar KB completo |

#### Request `/search/`:
```json
{
  "query": "texto a buscar",
  "user_permissions": ["ask_knowledge_ops", "ask_knowledge_products"],
  "limit": 5
}
```

#### Request `/ask/`:
```json
{
  "question": "¿Cuál es el tiempo de producción estándar?",
  "session_id": "uuid-de-sesion",
  "user_id": "id-usuario",
  "user_permissions": ["ask_knowledge_ops"],
  "expediente_ref_id": null
}
```

#### Response `/ask/`:
```json
{
  "answer": "El tiempo de producción...",
  "session_id": "uuid-de-sesion",
  "chunks_used": [{"source_file": "...", "section": "...", "score": 0.92}]
}
```

**Modelo Claude:** `claude-3-5-haiku-20241022` — no cambiar sin aprobación.

---

### Item 12: Sesiones Redis (multi-turn)
**Branch:** `feature/s8-07-knowledge-service`

#### Archivo: `services/mwt-knowledge/sessions.py`

**D-05:** Prefijo `kw:` obligatorio en todas las keys:
- Messages: `kw:session:{user_id}:{session_id}`
- Metadata: `kw:session_meta:{user_id}:{session_id}`

**Configuración:**
- Sliding window: 20 mensajes (eliminar más antiguos si supera)
- TTL por mensaje: 2h
- TTL global de sesión: 2h (refresh en cada uso)

```python
import redis
import json
import os
from datetime import datetime

r = redis.from_url(os.environ['REDIS_URL'])

SESSION_TTL = 7200   # 2h en segundos
MAX_MESSAGES = 20


def get_session_key(user_id: str, session_id: str) -> str:
    return f"kw:session:{user_id}:{session_id}"


def get_history(user_id: str, session_id: str) -> list:
    key = get_session_key(user_id, session_id)
    data = r.get(key)
    if not data:
        return []
    return json.loads(data)


def save_message(user_id: str, session_id: str, role: str, content: str):
    key = get_session_key(user_id, session_id)
    history = get_history(user_id, session_id)
    history.append({'role': role, 'content': content, 'ts': datetime.utcnow().isoformat()})
    # Sliding window — máximo 20 mensajes
    if len(history) > MAX_MESSAGES:
        history = history[-MAX_MESSAGES:]
    r.setex(key, SESSION_TTL, json.dumps(history))


def clear_session(user_id: str, session_id: str):
    key = get_session_key(user_id, session_id)
    r.delete(key)
```

---

### Item 13: Django Proxy `/api/knowledge/`
**Branch:** `feature/s8-08-knowledge-ask` / `feature/s8-09-knowledge-index` / `feature/s8-10-knowledge-sessions`

#### Archivos a crear:
- `apps/knowledge/views.py` (proxy Django → FastAPI interno)
- `apps/knowledge/urls.py`

#### Archivos a modificar:
- `config/urls.py` → incluir `apps/knowledge/urls.py` bajo `/api/knowledge/`

#### Endpoints Django (proxy hacia FastAPI):

| Método | Path Django | Auth | Proxy hacia |
|--------|-------------|------|-------------|
| POST | `/api/knowledge/search/` | JWT + ASK_KNOWLEDGE_* | `http://mwt-knowledge:8001/search/` |
| POST | `/api/knowledge/ask/` | JWT + ASK_KNOWLEDGE_* | `http://mwt-knowledge:8001/ask/` |
| POST | `/api/knowledge/index/` | JWT + role=CEO | `http://mwt-knowledge:8001/reindex/` |
| GET | `/api/knowledge/sessions/` | JWT | `ConversationLog` DB (no proxy) |
| GET | `/api/knowledge/sessions/{id}/` | JWT | `ConversationLog` DB (no proxy) |

**Flujo `POST /api/knowledge/ask/`:**
1. Verificar JWT + permiso `ask_knowledge_*` via `require_permission_jwt`
2. Recuperar historial multi-turn Redis (`kw:session:{user_id}:{session_id}`)
3. Llamar `http://mwt-knowledge:8001/ask/` con `X-Internal-Token`
4. Guardar `ConversationLog` con el resultado
5. Devolver `{answer, session_id, chunks_used}`

**D-09:** Expediente BLOQUEADO (C17): `/ask/` funciona normalmente — NO verificar estado del expediente.

**`GET /api/knowledge/sessions/`:**
- Usuario ve solo sus propias sesiones
- CEO puede filtrar por `?user_id=`
- Paginado
- Excluir logs con `retain_until < hoy`

#### Criterios de DONE `POST /api/knowledge/ask/`:
- [ ] Auth JWT + permiso verificado
- [ ] Historial multi-turn funciona
- [ ] Filtro visibilidad por permisos del usuario
- [ ] `ConversationLog` guardado por cada request
- [ ] Redis actualizado con TTL
- [ ] Expediente BLOQUEADO: `/ask/` funciona normalmente (D-09)

---

## DEVOPS

---

### Item 11 (DevOps): Docker Compose + pgvector
**Branch:** `feature/s8-11-devops-knowledge`
**Agente:** AG-07
**Dependencia:** Item 7 aprobado

#### Checklist DevOps:
- [ ] Servicio `mwt-knowledge` agregado a `docker-compose.yml` (ver código Item 8)
- [ ] Verificar que `db` service usa `postgres:16` (NO `postgres:16-alpine` — compatibilidad pgvector)
- [ ] `CREATE EXTENSION vector` exitoso en DB `mwt` (no en `paperless`)
- [ ] Variables `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `KNOWLEDGE_INTERNAL_TOKEN` en `.env`
- [ ] `celery-beat` sin `--scheduler DatabaseScheduler`
- [ ] `docker compose up -d` levanta todos los servicios incluyendo `mwt-knowledge`
- [ ] `mwt-knowledge` puede conectar a DB `mwt` y Redis

---

## QA

---

### Item 12 (QA): Tests Pilar A — Identidad + JWT
**Branch:** `feature/s8-12-tests-pilar-a`
**Agente:** AG-06
**Dependencia:** Items 1–6 aprobados

#### Archivos a crear:
- `apps/users/tests/test_mwtuser.py`
- `apps/users/tests/test_permissions.py`
- `apps/users/tests/test_jwt.py`
- `apps/users/tests/test_admin_api.py`
- `apps/knowledge/tests/test_conversation_log.py`

#### Cobertura mínima (≥80% en `apps/users/` y `apps/knowledge/models.py`):

```
✅ MWTUser: creación con role e is_api_user
✅ UserPermission: validación techo (permiso fuera del techo → ValidationError)
✅ JWT payload contiene user_id + role + legal_entity_id + permissions[]
✅ is_api_user=False → POST /api/auth/token/ → 401
✅ Decorador require_permission: autenticado sin permiso → 403
✅ Decorador require_permission_jwt: token sin permiso → 403
✅ API Admin: crear usuario (cero permisos), listar, PATCH permisos
✅ Guardia last admin: self-patch CEO quitando MANAGE_USERS → 400
✅ ConversationLog: calculate_retention() para los 3 casos
✅ purge_expired_logs: solo purga logs con retain_until < hoy
✅ Redis namespace kw: no colisiona con Django sessions
```

**Nota:** Tests que importan constantes del app desde migraciones fallarán — usar listas locales.

---

### Item 13 (QA): Tests Pilar B — Knowledge Endpoints
**Branch:** `feature/s8-13-tests-pilar-b`
**Agente:** AG-06
**Dependencia:** Items 7–10 aprobados

#### Archivos a crear:
- `apps/knowledge/tests/test_ask_endpoint.py`
- `apps/knowledge/tests/test_index_endpoint.py`
- `apps/knowledge/tests/test_sessions_endpoint.py`
- `services/mwt-knowledge/tests/test_indexer.py`

#### Cobertura:

```
✅ POST /api/knowledge/ask/: flujo completo (mock OpenAI embed + mock Claude)
✅ Filtro visibilidad: usuario sin ask_knowledge_pricing no ve chunks pricing
✅ Historial multi-turn Redis: mensajes se acumulan correctamente
✅ ConversationLog guardado en cada /ask/
✅ POST /api/knowledge/index/: solo CEO puede llamarlo (role=CEO)
✅ Indexer: rechaza visibility=CEO-ONLY con reason: ceo_only_excluded
✅ Indexer: rechaza stamp≠VIGENTE
✅ GET /api/knowledge/sessions/: usuario ve solo sus sesiones
✅ CEO puede filtrar /sessions/?user_id=
✅ Expediente BLOQUEADO: /ask/ funciona normalmente
```

**Nota:** Tests requieren mock de OpenAI y Anthropic (pytest-mock / unittest.mock).

---

## VERIFICACIONES ARQUITECTURA PRE-DEPLOY

---

### Item 14: Checklist Verificaciones Pre-Deploy
**Branch:** `feature/s8-14-arch-verification`
**Agente:** AG-01 Architect
**Dependencia:** Todos los items anteriores aprobados

```bash
# V1: FKs a auth.User en apps propias — lista completa
grep -rn "ForeignKey.*User\|auth.User" apps/

# V2: FKs contrib adicionales
grep -rn "ForeignKey.*User\|auth.User" $(python -c "import django; print(django.__path__[0])")/contrib/

# V3: celery-beat sin --scheduler DatabaseScheduler
grep "DatabaseScheduler" docker-compose.yml  # debe retornar vacío

# V4: PK del CEO preservado
python manage.py shell -c "
from apps.users.models import MWTUser
from django.contrib.auth import get_user_model
print('CEO PK ok:', MWTUser.objects.get(is_superuser=True).id)
"

# V5: knowledge_chunks no tiene chunks CEO-ONLY
psql $DATABASE_URL -c "SELECT count(*) FROM knowledge_chunks WHERE visibility='CEO-ONLY';"
# Resultado esperado: 0

# V6: Redis kw: namespace — no colisiona con Django sessions
python manage.py shell -c "
import redis, os
r = redis.from_url(os.environ['REDIS_URL'])
keys = r.keys('kw:*')
session_keys = r.keys('django.contrib.sessions*')
print('kw: keys:', len(keys), '| session keys:', len(session_keys))
"

# V7: manage.py check sin errores
python manage.py check

# V8: celery-beat muestra exactamente 3 tasks
docker compose logs celery-beat | grep -E "evaluate_credit_clocks|process_pending_events|purge_expired_logs"
# Debe mostrar las 3 tasks
```

#### Criterios de DONE:
- [ ] V1: Lista FKs confirmada
- [ ] V2: FKs contrib identificadas
- [ ] V3: `celery-beat` sin `--scheduler DatabaseScheduler`
- [ ] V4: PK CEO preservado
- [ ] V5: `knowledge_chunks WHERE visibility='CEO-ONLY'` = 0
- [ ] V6: Redis `kw:` namespace no colisiona
- [ ] V7: `python manage.py check` sin errores
- [ ] V8: `docker compose logs celery-beat` muestra exactamente 3 tasks

---

## Tabla de archivos: creación y modificación

### Archivos NUEVOS (crear):

| Archivo | Item | Descripción |
|---------|------|-------------|
| `apps/users/__init__.py` | 1 | App users |
| `apps/users/apps.py` | 1 | App config |
| `apps/users/models.py` | 1–2 | MWTUser + UserPermission + enums |
| `apps/users/serializers.py` | 3 | MWTTokenObtainPairSerializer |
| `apps/users/decorators.py` | 4 | require_permission + require_permission_jwt |
| `apps/users/mixins.py` | 4 | PermissionRequiredMixin + JWTPermissionRequiredMixin |
| `apps/users/views.py` | 5 | CRUD usuarios + PATCH permisos |
| `apps/users/urls.py` | 5 | URL routing /api/admin/users/ |
| `apps/users/migrations/0001_initial.py` | 1 | Migración inicial MWTUser |
| `apps/users/migrations/0002_migrate_ceo.py` | 1 | Data migration CEO |
| `apps/knowledge/__init__.py` | 6 | App knowledge |
| `apps/knowledge/apps.py` | 6 | App config |
| `apps/knowledge/models.py` | 6 | ConversationLog |
| `apps/knowledge/utils.py` | 6 | calculate_retention() |
| `apps/knowledge/signals.py` | 6 | Signal post_save Expediente |
| `apps/knowledge/tasks.py` | 6 | purge_expired_logs |
| `apps/knowledge/views.py` | 13 | Proxy Django → FastAPI |
| `apps/knowledge/urls.py` | 13 | URL routing /api/knowledge/ |
| `apps/knowledge/migrations/0001_initial.py` | 6 | ConversationLog |
| `apps/knowledge/migrations/0002_knowledge_schema.py` | 7 | pgvector + tables |
| `services/mwt-knowledge/Dockerfile` | 8 | Imagen Python 3.12 |
| `services/mwt-knowledge/entrypoint.sh` | 8 | Watcher + uvicorn |
| `services/mwt-knowledge/requirements.txt` | 8 | fastapi, uvicorn, pgvector, openai, etc |
| `services/mwt-knowledge/main.py` | 11 | FastAPI endpoints internos |
| `services/mwt-knowledge/watcher.py` | 9 | Watchdog /docs/ |
| `services/mwt-knowledge/indexer.py` | 10 | Chunking + embeddings + upsert |
| `services/mwt-knowledge/sessions.py` | 12 | Redis multi-turn kw: |
| `knowledge-docs/.gitkeep` | 8 | Directorio KB vacío |

### Archivos MODIFICADOS:

| Archivo | Item | Cambio |
|---------|------|--------|
| `config/settings.py` | 1, 3, 6 | AUTH_USER_MODEL, INSTALLED_APPS, SIMPLE_JWT |
| `config/urls.py` | 5, 13 | include /api/admin/users/ y /api/knowledge/ |
| `config/celery.py` | 6 | Añadir purge_expired_logs a beat_schedule |
| `docker-compose.yml` | 8, 11 | Agregar mwt-knowledge, fix celery-beat |
| `.env` | 8 | OPENAI_API_KEY, ANTHROPIC_API_KEY, KNOWLEDGE_INTERNAL_TOKEN |
| `.env.template` | 8 | Documentar nuevas variables |

---

## Tabla resumen Sprint 8 — Items y Branches

| # | Tarea | Agente | Branch |
|---|-------|--------|--------|
| 1 | MWTUser — Modelo + Migración CEO | AG-02 | `feature/s8-01-mwtuser` |
| 2 | UserPermission — Modelo + Validación Techo | AG-02 | `feature/s8-01-mwtuser` |
| 3 | JWT Extendido — Serializer + Guardia is_api_user | AG-02 | `feature/s8-03-jwt-extended` |
| 4 | Decoradores @require_permission (Session + JWT) | AG-02 | `feature/s8-03-jwt-extended` |
| 5 | API Admin Usuarios — CRUD + Permisos | AG-02 | `feature/s8-05-admin-users-api` |
| 6 | ConversationLog + Retención + Signal + Beat Task | AG-02 | `feature/s8-06-conversation-log` |
| 7 | Schema PostgreSQL — pgvector + Tablas | AG-02 | `feature/s8-07-knowledge-service` |
| 8 | Docker Service mwt-knowledge | AG-02 | `feature/s8-07-knowledge-service` |
| 9 | Watcher (watchdog) | AG-02 | `feature/s8-07-knowledge-service` |
| 10 | Indexer (chunking + embeddings) | AG-02 | `feature/s8-07-knowledge-service` |
| 11 | FastAPI Endpoints Internos | AG-02 | `feature/s8-07-knowledge-service` |
| 12 | Sesiones Redis (multi-turn) | AG-02 | `feature/s8-07-knowledge-service` |
| 13 | Django Proxy /api/knowledge/ | AG-02 | `feature/s8-08/09/10-knowledge-*` |
| 14 | Docker Compose + pgvector (DevOps) | AG-07 | `feature/s8-11-devops-knowledge` |
| 15 | Tests Pilar A — Identidad + JWT | AG-06 | `feature/s8-12-tests-pilar-a` |
| 16 | Tests Pilar B — Knowledge Endpoints | AG-06 | `feature/s8-13-tests-pilar-b` |
| 17 | Verificaciones Arquitectura Pre-Deploy | AG-01 | `feature/s8-14-arch-verification` |

---

## Decisiones arquitectónicas clave (D-01 a D-13)

| ID | Decisión |
|----|----------|
| D-01 | `legal_entity` es FK directa a `LegalEntity` existente — NO crear `LegalEntityRef` |
| D-02 | FKs a migrar: `EventLog`, `ArtifactInstance`, `Transfer` |
| D-03 | JWT extiende Sprint 0 — NO crear endpoint nuevo, solo modificar serializer |
| D-04 | Celery Beat usa `app.conf.beat_schedule` — eliminar `--scheduler DatabaseScheduler` |
| D-05 | Redis prefix `kw:` obligatorio para knowledge (zero colisión con sessions) |
| D-06 | pgvector en DB `mwt` — no afecta DB `paperless` |
| D-07 | `psycopg2-binary>=2.9` en `requirements.txt` de `mwt-knowledge` |
| D-08 | CEO migra con `is_api_user=True` y PK preservado |
| D-09 | ConversationLog en expediente BLOQUEADO es **permitido** — no verificar estado |
| D-10 | Signal `retain_until` usa `transaction.on_commit()` obligatoriamente |
| D-11 | Frontend Sprint 7 no se toca — knowledge es API-only en Sprint 8 |
| D-12 | Usuarios seed: solo CEO. Nuevos usuarios se crean post-deploy via API |
| D-13 | `visibility=CEO-ONLY` excluido del indexer intencionalmente (`ceo_only_excluded`) |

---

## LO QUE NO HACER

> Leer antes de empezar cada item.

- ❌ No tocar el frontend de Sprint 7
- ❌ No crear UI de knowledge (es Sprint 9)
- ❌ No migrar histórico de `django_admin_log`
- ❌ No crear usuarios seed — el CEO los crea post-deploy
- ❌ No usar `getattr(request.auth, 'payload', {})` — siempre `request.auth.get()`
- ❌ No importar constantes del app dentro de migraciones — usar listas congeladas
- ❌ No poner `--scheduler DatabaseScheduler` en celery-beat
- ❌ No crear endpoint `/api/auth/token/` — ya existe (Sprint 0)
- ❌ No crear `LegalEntityRef` — FK directa a `LegalEntity` (D-01)
- ❌ No exponer `mwt-knowledge` al exterior (sin `ports:` en docker-compose)
- ❌ No verificar estado del expediente antes de crear ConversationLog (D-09)
- ❌ No cambiar el modelo Claude `claude-3-5-haiku-20241022` sin aprobación

---

## Criterio SPRINT 8 DONE

1. ✅ `MWTUser` operativo, CEO migrado con todos sus permisos, login consola funcional
2. ✅ CEO puede crear usuarios y asignar permisos via API admin
3. ✅ JWT extendido funcional (extensión Sprint 0)
4. ✅ `mwt-knowledge` arranca, monitorea `/docs/`, indexa `.md` con stamp=VIGENTE
5. ✅ ~120 `.md` indexados en pgvector
6. ✅ `POST /api/knowledge/search/` < 1.5s end-to-end
7. ✅ `POST /api/knowledge/ask/` < 5s (embedding + pgvector + Claude)
8. ✅ Multi-turn funcional: Redis con prefijo `kw:`, sliding 20 msgs, TTL 2h
9. ✅ `ConversationLog` con retención diferenciada
10. ✅ Tests passing, regresión Sprints 1–7 limpia

---

## Lo que desbloquea este sprint

- **Sprint 9:** Canal WhatsApp — webhook llama `/api/knowledge/ask/` con JWT
- **Sprint 9:** Indexación PDFs MinIO + `document_index` operativos
- **n8n workflows:** pueden llamar `/api/knowledge/search/`
- **Portal B2B:** base de usuarios lista (roles INTERNAL, CLIENT_MARLUVAS, CLIENT_TECMATER)

---

*Generado: 2026-03-13 | Fuente: LOTE_SM_SPRINT8_v3_15.md + GUIA_SPRINT8_ALEJANDRO.md + ASANA_TASK_SPRINT8.md*
*Stamp: PLAN_IMPLEMENTACION v1.0 — Sprint 8*
