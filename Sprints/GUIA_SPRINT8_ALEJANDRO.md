# GUÍA SPRINT 8 — Alejandro
**Fecha:** 2026-03-12
**Ref técnica completa:** LOTE_SM_SPRINT8 v3.15 (pedir al CEO si necesitás detalle)

---

## Qué es Sprint 8

Dos bloques en secuencia estricta **A → B**:

**Bloque A — Identidad (Items 1–6):**
Extender `auth.User` a `MWTUser` con roles, permisos granulares, JWT extendido, y log de conversaciones con retención automática.

**Bloque B — Knowledge Container (Items 7–13):**
Contenedor Docker `mwt-knowledge` que indexa los `.md` del knowledge base en pgvector y expone búsqueda semántica + respuesta con Claude vía historial multi-turn en Redis.

**Item 14:** Tests de todo el sprint.

**El frontend de Sprint 7 NO se toca.** Knowledge es API-only en Sprint 8.

---

## Orden de ejecución

```
Item 1: MWTUser (modelo + migración CEO)
  ├── Item 2: UserPermission (modelo + validación techo)
  ├── Item 3: JWT extendido (serializer + guardia is_api_user)
  │     └── Item 4: Decoradores @require_permission
  │           └── Item 5: API admin usuarios (CRUD + permisos)
  └── Item 6: ConversationLog + retención + signal + Beat task
          │
          ▼
Item 7: Schema PostgreSQL (pgvector + tablas)
  └── Item 8: Docker service mwt-knowledge
        ├── Item 9: Watcher (watchdog)
        ├── Item 10: Indexer (chunking + embeddings)
        ├── Item 11: FastAPI endpoints internos
        └── Item 12: Sesiones Redis
              └── Item 13: Django proxy /api/knowledge/
                    └── Item 14: Tests
```

---

## ANTES DE EMPEZAR — 3 verificaciones obligatorias

Estas 3 verificaciones se hacen **antes de escribir una sola línea de código.** Si alguna falla, parar y reportar al CEO.

### Verificación 1: Inventario de FKs a auth.User
```bash
grep -rn "ForeignKey.*User\|auth.User" apps/
```
El arquitecto identificó 3: `EventLog.triggered_by`, `ArtifactInstance.created_by`, `Transfer.created_by`. Si aparecen más, agregarlas a la lista de migraciones del **Paso 7 de Item 1** — nunca a `users/0002_migrate_ceo.py`.

### Verificación 2: FKs contrib de Django
```bash
grep -rn "ForeignKey.*User\|auth.User" $(python -c "import django; print(django.__path__[0])")/contrib/
```
La única relevante es `django.contrib.admin` → `LogEntry.user`. **No migrar** el histórico de `django_admin_log` — queda fuera de alcance Sprint 8. Solo verificar que admin login funcione post-migración.

### Verificación 3: Celery Beat scheduler
Verificar el comando del servicio `celery-beat` en `docker-compose.yml`. Si tiene `--scheduler django_celery_beat.schedulers:DatabaseScheduler`, **eliminarlo**:

```yaml
# ANTES (si existe):
celery-beat:
  command: celery -A config beat --scheduler django_celery_beat.schedulers:DatabaseScheduler

# DESPUÉS:
celery-beat:
  command: celery -A config beat -l info
```

Sin este cambio, las tasks de `app.conf.beat_schedule` se ignoran silenciosamente.

---

## Bloque A — Identidad

### Item 1: MWTUser

**App nueva:** `users`

**Modelo:**
```python
from django.contrib.auth.models import AbstractUser

class UserRole(models.TextChoices):
    CEO             = 'CEO',             'CEO'
    INTERNAL        = 'INTERNAL',        'Interno'
    CLIENT_MARLUVAS = 'CLIENT_MARLUVAS', 'Cliente Marluvas'
    CLIENT_TECMATER = 'CLIENT_TECMATER', 'Cliente Tecmater'
    ANONYMOUS       = 'ANONYMOUS',       'Anónimo'

class Permission(models.TextChoices):
    ASK_KNOWLEDGE_OPS      = 'ask_knowledge_ops'
    ASK_KNOWLEDGE_PRODUCTS = 'ask_knowledge_products'
    ASK_KNOWLEDGE_PRICING  = 'ask_knowledge_pricing'
    VIEW_EXPEDIENTES_OWN   = 'view_expedientes_own'
    VIEW_EXPEDIENTES_ALL   = 'view_expedientes_all'
    VIEW_COSTOS            = 'view_costos'
    DOWNLOAD_DOCUMENTS     = 'download_documents'
    MANAGE_USERS           = 'manage_users'

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
    legal_entity    = models.ForeignKey('core.LegalEntity', null=True, blank=True, on_delete=models.SET_NULL)
    whatsapp_number = models.CharField(max_length=20, null=True, blank=True)
    is_api_user     = models.BooleanField(default=False)
    created_by      = models.ForeignKey('self', null=True, on_delete=models.SET_NULL, related_name='created_users')

    def has_permission(self, perm: Permission) -> bool:
        ceiling = ROLE_PERMISSION_CEILING.get(self.role, [])
        if perm not in ceiling:
            return False
        return self.permissions_set.filter(permission=perm).exists()
```

**Nota:** `legal_entity` es FK a `LegalEntity` existente (Sprint 5). Usá el `app_label` correcto según donde vive ese modelo. No crear modelo nuevo.

**Secuencia de migración (orden estricto — no saltear pasos):**

1. `python manage.py startapp users`
2. Definir **ambos** modelos `MWTUser` + `UserPermission` en `users/models.py`
3. Activar `AUTH_USER_MODEL = 'users.MWTUser'` en `settings.py` **en el mismo commit** que la definición del modelo — antes de cualquier migración
4. `python manage.py makemigrations users` → genera `0001_initial`
5. `python manage.py migrate users` → aplica `0001_initial`
6. Crear `users/0002_migrate_ceo.py` — data migration:

```python
# users/0002_migrate_ceo.py
# IMPORTANTE: lista congelada — NO importar constantes del app
CEO_PERMISSIONS = [
    'ask_knowledge_ops', 'ask_knowledge_products', 'ask_knowledge_pricing',
    'view_expedientes_own', 'view_expedientes_all', 'view_costos',
    'download_documents', 'manage_users',
]

def migrate_ceo(apps, schema_editor):
    OldUser = apps.get_model('auth', 'User')
    MWTUser = apps.get_model('users', 'MWTUser')
    UserPermission = apps.get_model('users', 'UserPermission')
    old = OldUser.objects.get(is_superuser=True)
    MWTUser.objects.create(
        id=old.id,              # preservar PK — crítico
        username=old.username, email=old.email, password=old.password,
        is_superuser=old.is_superuser, is_staff=old.is_staff,
        is_active=old.is_active, date_joined=old.date_joined,
        role='CEO', is_api_user=True,
    )
    for perm in CEO_PERMISSIONS:
        UserPermission.objects.create(
            user_id=old.id, permission=perm, granted_by_id=old.id,
        )

class Migration(migrations.Migration):
    dependencies = [('users', '0001_initial')]
    operations = [migrations.RunPython(migrate_ceo, migrations.RunPython.noop)]
```

7. `python manage.py migrate users` → aplica `0002_migrate_ceo`
8. Generar y aplicar migraciones de apps con FK a `auth.User` (las que encontraste en Verificación 1): `python manage.py makemigrations` → `python manage.py migrate`
9. `python manage.py check` sin errores → login CEO funciona → Django Admin accesible

**DONE cuando:**
- [ ] App `users` creada, `AUTH_USER_MODEL = 'users.MWTUser'` activo
- [ ] CEO migrado con `role=CEO`, `is_api_user=True`, todos sus `UserPermission`
- [ ] PK preservado: `MWTUser.objects.get(username=CEO_USERNAME).id == old_auth_user.id`
- [ ] Migraciones de FKs en apps existentes aplicadas
- [ ] `python manage.py check` sin errores, login CEO funciona
- [ ] Post-migración: admin login funciona con `MWTUser`. Histórico `django_admin_log` fuera de alcance

---

### Item 2: UserPermission

Ya definido en el Paso 2 de Item 1. Solo falta la validación:

```python
class UserPermission(models.Model):
    user       = models.ForeignKey(MWTUser, on_delete=models.CASCADE, related_name='permissions_set')
    permission = models.CharField(max_length=50, choices=Permission.choices)
    granted_by = models.ForeignKey(MWTUser, on_delete=models.SET_NULL, null=True, related_name='granted_permissions')
    granted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'permission')
```

**DONE cuando:**
- [ ] Modelo creado y migrado
- [ ] `save()` valida: permiso fuera del techo del rol → `ValidationError`
- [ ] CEO tiene todos sus permisos (creados por `users/0002`)

---

### Item 3: JWT extendido

El endpoint `POST /api/auth/token/` **ya existe** (Sprint 0). Solo modificar el serializer.

```python
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework.exceptions import AuthenticationFailed

class MWTTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['role'] = user.role
        token['legal_entity_id'] = str(user.legal_entity_id) if user.legal_entity_id else None
        token['permissions'] = list(user.permissions_set.values_list('permission', flat=True))
        return token

    def validate(self, attrs):
        data = super().validate(attrs)   # autentica + construye tokens
        if not self.user.is_api_user:    # guardia ANTES de devolver tokens
            raise AuthenticationFailed(
                {'error': 'api_access_not_enabled',
                 'detail': 'Este usuario no tiene acceso JWT habilitado.'}
            )
        return data
```

Apuntar la ruta existente a una view que use este serializer.

**Configuración en settings.py:**
```python
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=8),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=30),
    'ALGORITHM': 'HS256',
}
```

**DONE cuando:**
- [ ] La view de `POST /api/auth/token/` usa `MWTTokenObtainPairSerializer`
- [ ] JWT payload incluye `user_id` (Sprint 0), `role`, `legal_entity_id`, `permissions[]`
- [ ] `is_api_user=False` → 401 (`AuthenticationFailed`)
- [ ] Sesión web CEO no se toca

---

### Item 4: Decoradores @require_permission

Dos caminos — Session y JWT:

```python
# Camino A — Session (consola, /api/admin/)
def require_permission(perm: Permission):
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
def require_permission_jwt(perm: Permission):
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

**Importante:** Con `JWTStatelessUserAuthentication`, `request.auth` es el payload decodificado como dict. La interfaz correcta es `request.auth.get('campo', default)`. **Nunca** usar `getattr(request.auth, 'payload', {})`.

**DONE cuando:**
- [ ] Ambos decoradores + mixins class-based equivalentes implementados
- [ ] Endpoints `/api/knowledge/` usan exclusivamente `require_permission_jwt`

---

### Item 5: API admin usuarios

Auth: Session + `MANAGE_USERS`

**Endpoints:**

| Método | Path | Descripción |
|--------|------|-------------|
| POST | `/api/admin/users/` | Crear usuario (con cero permisos) |
| GET | `/api/admin/users/` | Listar todos |
| GET | `/api/admin/users/{id}/` | Detalle con permisos |
| GET | `/api/admin/users/{id}/permissions/` | Permisos actuales |
| PATCH | `/api/admin/users/{id}/permissions/` | Reemplazar permisos |

**Crear usuario** — payload:
```json
{ "username": "sondel_ops", "email": "ops@sondel.com", "password": "...",
  "role": "CLIENT_MARLUVAS", "legal_entity_id": "uuid",
  "whatsapp_number": "+50688888888", "is_api_user": true }
```
El usuario se crea con **cero** `UserPermission`. Los permisos se asignan por separado.

**PATCH permisos** — contrato:
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

**DONE cuando:**
- [ ] CRUD usuarios funcionando
- [ ] Password hasheado con `make_password()`
- [ ] `legal_entity_id` valida contra `LegalEntity` existente
- [ ] Self-patch CEO quitando `MANAGE_USERS` → 400
- [ ] Cada `UserPermission` insertado tiene `granted_by=request.user`

---

### Item 6: ConversationLog + retención

**Modelo:**
```python
class ConversationLog(models.Model):
    session_id     = models.CharField(max_length=64, db_index=True)
    user           = models.ForeignKey(MWTUser, null=True, on_delete=models.SET_NULL)
    user_role      = models.CharField(max_length=20)
    expediente_ref = models.ForeignKey('expedientes.Expediente', null=True, blank=True, on_delete=models.SET_NULL)
    question       = models.TextField()
    answer         = models.TextField()
    chunks_used    = models.JSONField(default=list)
    created_at     = models.DateTimeField(auto_now_add=True)
    retain_until   = models.DateField(null=True)

RETENTION_DAYS = {
    'CEO': 365, 'CLIENT_MARLUVAS': 365, 'CLIENT_TECMATER': 365,
    'INTERNAL': 90, 'ANONYMOUS': 30,
}
```

**Función `calculate_retention()` — en `apps/knowledge/utils.py`:**
```python
def calculate_retention(user_role, expediente_ref=None, as_of_date=None):
    if as_of_date is None:
        raise ValueError("calculate_retention: as_of_date es obligatorio")
    if expediente_ref is None:
        return as_of_date + timedelta(days=RETENTION_DAYS.get(user_role, 30))
    if expediente_ref.status != 'CERRADO':
        return None
    if expediente_ref.closed_at is None:
        raise ValueError(
            f"calculate_retention: Expediente {expediente_ref.pk} tiene status=CERRADO pero closed_at es None"
        )
    return expediente_ref.closed_at.date() + timedelta(days=365)
```

**Signal — para logs ya persistidos cuando el expediente se cierra:**
```python
@receiver(post_save, sender=Expediente)
def update_conversation_retention(sender, instance, **kwargs):
    if instance.status == 'CERRADO':
        if instance.closed_at is None:
            raise ValueError(
                f"calculate_retention: Expediente {instance.pk} tiene status=CERRADO pero closed_at es None"
            )
        def _update():
            ConversationLog.objects.filter(
                expediente_ref=instance,
                retain_until__isnull=True
            ).update(retain_until=instance.closed_at.date() + timedelta(days=365))
        transaction.on_commit(_update)  # OBLIGATORIO — nunca sin on_commit
```

**Celery Beat — agregar a `app.conf.beat_schedule` en `config/celery.py`:**
```python
app.conf.beat_schedule = {
    # Existentes Sprint 2 — no tocar
    'evaluate_credit_clocks': { ... },
    'process_pending_events': { ... },
    # Nuevo Sprint 8
    'purge_expired_logs': {
        'task': 'apps.knowledge.tasks.purge_expired_logs',
        'schedule': crontab(hour=3, minute=0),  # 3am diario
    },
}
```

**DONE cuando:**
- [ ] Modelo `ConversationLog` creado y migrado
- [ ] `calculate_retention()` en `apps/knowledge/utils.py`
- [ ] Signal con `transaction.on_commit()` — no sin él
- [ ] `purge_expired_logs` en `app.conf.beat_schedule`
- [ ] `--scheduler DatabaseScheduler` eliminado de celery-beat (Verificación 3)
- [ ] Check post-deploy: `docker compose logs celery-beat` muestra 3 tasks (`evaluate_credit_clocks`, `process_pending_events`, `purge_expired_logs`)
- [ ] Índice `(retain_until, created_at)` creado

---

## Bloque B — Knowledge Container

### Item 7: Schema PostgreSQL

```sql
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE knowledge_chunks (
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
  indexed_at      TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX knowledge_chunks_embedding_hnsw ON knowledge_chunks
  USING hnsw (embedding vector_cosine_ops) WITH (m=16, ef_construction=64);
CREATE INDEX knowledge_chunks_filters ON knowledge_chunks (visibility, stamp, domain, is_pricing);
CREATE INDEX knowledge_chunks_source  ON knowledge_chunks (source_file, source_hash);

CREATE TABLE indexation_log (
  id              SERIAL PRIMARY KEY,
  source_file     VARCHAR(255) NOT NULL,
  status          VARCHAR(20) NOT NULL,  -- SUCCESS | SKIPPED | REJECTED | FAILED
  reason          TEXT,
  chunks_created  INTEGER DEFAULT 0,
  embedding_model VARCHAR(50),
  indexed_at      TIMESTAMPTZ DEFAULT now()
);
```

Implementar vía migración Django. No tocar tablas de expedientes.

**DONE cuando:**
- [ ] Extensión vector activa en DB mwt
- [ ] Tablas y todos los índices creados
- [ ] Migración aplica sin tocar tablas de expedientes

---

### Item 8: Docker service mwt-knowledge

**Estructura:**
```
services/mwt-knowledge/
├── Dockerfile
├── entrypoint.sh
├── requirements.txt
├── main.py          (FastAPI — Item 11)
├── watcher.py       (Watcher — Item 9)
├── indexer.py       (Indexer — Item 10)
└── sessions.py      (Sesiones Redis — Item 12)
```

**Dockerfile:**
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

**entrypoint.sh:**
```bash
#!/bin/bash
set -e
echo "[mwt-knowledge] Iniciando watcher en background..."
python watcher.py &
echo "[mwt-knowledge] Iniciando FastAPI en :8001..."
exec uvicorn main:app --host 0.0.0.0 --port 8001 --workers 1
```

**docker-compose.yml** (agregar):
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
    - EMBEDDING_MODEL=text-embedding-3-small
    - KNOWLEDGE_INTERNAL_TOKEN=${KNOWLEDGE_INTERNAL_TOKEN}
    - MIN_SIMILARITY=0.5
    - LOG_LEVEL=INFO
  networks:
    - mwt-internal
  depends_on: [db, redis]
  # Sin ports — no expuesto al exterior
```

**requirements.txt:**
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
```

**Variables nuevas en `.env`:**
```
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxx
KNOWLEDGE_INTERNAL_TOKEN=<32 chars aleatorio>
KNOWLEDGE_SERVICE_URL=http://mwt-knowledge:8001
MIN_SIMILARITY=0.5
```

**DONE cuando:**
- [ ] Dockerfile y entrypoint.sh creados
- [ ] Servicio en docker-compose.yml
- [ ] `./knowledge-docs/` con `.gitkeep`
- [ ] `docker compose up mwt-knowledge` → logs: "Iniciando watcher..." + "Iniciando FastAPI en :8001"

---

### Item 9: Watcher

Archivo: `services/mwt-knowledge/watcher.py`

Usa `watchdog`. Monitorea `/docs/` recursivamente. Solo archivos `.md`.

Eventos: `FileCreatedEvent`, `FileModifiedEvent` → llama indexer. `FileDeletedEvent` → DELETE chunks del archivo + log REJECTED reason `archivo eliminado`.

Debounce 2s por archivo. Al iniciar: scan inicial de todos los `.md`.

---

### Item 10: Indexer

Archivo: `services/mwt-knowledge/indexer.py`

**Header canónico** (primeras 10 líneas del .md):
```
status: VIGENTE
visibility: INTERNAL
stamp: VIGENTE
domain: Plataforma
version: 1.0
```

**Reglas de validación — los 5 campos son obligatorios:**

| Campo | Válido | Si falla |
|-------|--------|----------|
| `status` | `VIGENTE` | REJECTED: `invalid_status:{valor}` |
| `stamp` | `VIGENTE` | REJECTED: `stamp_not_vigente` |
| `visibility` | `PUBLIC`, `INTERNAL`, `CEO-ONLY` | REJECTED: `invalid_visibility:{valor}` |
| `domain` | cualquier string no vacío | REJECTED: `domain_empty` |
| `version` | semver o string no vacío | REJECTED: `version_empty` |

Post-validación: `visibility=CEO-ONLY` → REJECTED `ceo_only_excluded` (esos archivos son para Claude Project directo, no para el agente).

**`is_pricing`** = `true` si el archivo es `ENT_COMERCIAL_PRICING`, `ENT_COMERCIAL_COSTOS`, `ENT_COMERCIAL_FINANZAS`, o si `domain` es `Pricing` o `Costos`.

**Chunking:** secciones `##` → máx 600 tokens por chunk (tiktoken) → batches de 100 para embeddings.

**Persistencia — transacción atómica:**
```sql
-- SUCCESS:
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

**Importante:** Un archivo que era buscable y deja de serlo (cambia a DRAFT, CEO-ONLY, etc.) **no puede dejar chunks previos** en pgvector.

**Estados de salida:**

| Estado | Chunks en DB | indexation_log |
|--------|-------------|----------------|
| SUCCESS | Nuevos chunks | status=SUCCESS |
| REJECTED | 0 (previos borrados) | status=REJECTED + reason |
| SKIPPED | Sin cambio (hash igual) | status=SKIPPED |
| FAILED | Sin cambio (rollback) | status=FAILED |

---

### Item 11: FastAPI interno

Archivo: `services/mwt-knowledge/main.py`

Auth: header `X-Internal-Token` = `KNOWLEDGE_INTERNAL_TOKEN` del env. Sin header o token incorrecto → 401. **Excepción:** `GET /status/` no requiere token.

**`POST /search/`** — request:
```json
{ "query": "...", "top_k": 5, "filters": { "domain": [...] },
  "exclude_pricing": false, "allowed_visibility": ["PUBLIC", "INTERNAL"] }
```

**SQL — todos los filtros en WHERE antes del LIMIT:**
```sql
SELECT id, source_file, section, chunk_index, content, domain, visibility, is_pricing,
       1 - (embedding <=> :query_embedding) AS similarity
FROM knowledge_chunks
WHERE stamp = 'VIGENTE'
  AND visibility = ANY(:allowed_visibility)
  AND (:domain_filter IS NULL OR domain = ANY(:domain_filter))
  AND (:exclude_pricing = false OR is_pricing = false)
  AND (embedding <=> :query_embedding) <= (1 - :min_similarity)
ORDER BY embedding <=> :query_embedding
LIMIT :top_k;
```

**`POST /search/` response:**
```json
{
  "results": [
    { "id": 123, "source_file": "ops/foo.md", "section": "Header",
      "content": "...", "similarity": 0.83, "domain": "Operación",
      "visibility": "INTERNAL", "is_pricing": false }
  ]
}
```

**`POST /ask/`** — request:
```json
{ "question": "...", "session_id": "uuid", "user_id": 123,
  "user_role": "...", "has_pricing_permission": false,
  "allowed_visibility": ["PUBLIC", "INTERNAL"],
  "top_k": 5, "language": "es", "filters": { "domain": [...] } }
```

`session_id` ausente → 400. `exclude_pricing` **no va en el request** — FastAPI lo deriva: `exclude_pricing = not has_pricing_permission`.

Pipeline: historial Redis → `/search/` interno → prompt Claude → append Redis → response.

**`POST /ask/` response:**
```json
{
  "answer": "...", "session_id": "uuid",
  "sources": [{"source_file": "...", "section": "...", "similarity": 0.83}],
  "chunks_used": [{"id": 123, "source_file": "...", "section": "...", "content": "..."}]
}
```

**`GET /status/`** — métricas indexación (sin auth).
**`POST /reindex/`** — re-indexa todo (requiere token).

---

### Item 12: Sesiones Redis

Archivo: `services/mwt-knowledge/sessions.py`

**Keys (prefijo `kw:` obligatorio):**
```
kw:session:{user_id}:{session_id}      → List JSON [{role, content, timestamp}]  TTL 2h
kw:session_meta:{user_id}:{session_id} → Hash {created_at}                       TTL 2h
```

**Regla de atomicidad:** toda operación que toque ambas keys usa `pipeline(transaction=True)`, salvo `redis.delete(session_key, meta_key)` (atómico por protocolo Redis).

**Implementación obligatoria:**

```python
# get_history(user_id, session_id):
session_exists, meta_exists = redis.exists(session_key), redis.exists(meta_key)
if session_exists != meta_exists:          # estado parcial → corrupta
    redis.delete(session_key, meta_key)
    return []
if not session_exists:
    return []
with redis.pipeline(transaction=True) as pipe:
    pipe.expire(session_key, 7200)
    pipe.expire(meta_key, 7200)
    pipe.execute()
return [json.loads(m) for m in redis.lrange(session_key, 0, -1)]

# append_message(user_id, session_id, message):
now_iso = datetime.now(timezone.utc).isoformat()
session_exists, meta_exists = redis.exists(session_key), redis.exists(meta_key)
if session_exists != meta_exists:
    redis.delete(session_key, meta_key)
    session_exists = meta_exists = False

if not session_exists and not meta_exists:  # sesión nueva
    with redis.pipeline(transaction=True) as pipe:
        pipe.rpush(session_key, json.dumps(message))
        pipe.hset(meta_key, mapping={"created_at": now_iso})
        pipe.expire(session_key, 7200)
        pipe.expire(meta_key, 7200)
        pipe.execute()
    return

with redis.pipeline(transaction=True) as pipe:  # sesión existente
    pipe.rpush(session_key, json.dumps(message))
    pipe.ltrim(session_key, -20, -1)       # sliding window 20 msgs
    pipe.expire(session_key, 7200)
    pipe.expire(meta_key, 7200)
    pipe.execute()

# clear_session(user_id, session_id):
redis.delete(session_key, meta_key)
```

**Seguridad:** la aislación depende del namespace `{user_id}` en la key. Sesión ajena = historial vacío (no 403).

**DONE cuando:**
- [ ] Las 3 funciones implementadas en `sessions.py`
- [ ] Pipelines usados correctamente (con la excepción del delete)
- [ ] `get_history()` solo-lectura extiende TTL
- [ ] 21 mensajes → `LLEN = 20`
- [ ] Tests de estado parcial (meta sin lista, lista sin meta) → limpian correctamente
- [ ] Sesión nueva → `created_at` es ISO-8601 válido

---

### Item 13: Django proxy /api/knowledge/

Auth: `JWTStatelessUserAuthentication` — sin DB lookup.

**Lógica de permisos (aplica a `/search/` y `/ask/`):**

```python
has_ops      = 'ask_knowledge_ops'      in request.auth.get('permissions', [])
has_products = 'ask_knowledge_products' in request.auth.get('permissions', [])
has_pricing  = 'ask_knowledge_pricing'  in request.auth.get('permissions', [])
role         = request.auth.get('role', '')

# Guardia 1 — ANONYMOUS
if role == 'ANONYMOUS':
    return JsonResponse({'error': 'permission_denied'}, status=403)

# Guardia 2 — sin permiso base
if not has_ops and not has_products:
    return JsonResponse({'error': 'permission_denied'}, status=403)

domain_filter      = None if has_ops else ['Marca', 'Producto', 'Mercado']
exclude_pricing    = not has_pricing
allowed_visibility = ['PUBLIC', 'INTERNAL'] if role in ['CEO', 'INTERNAL'] else ['PUBLIC']
```

**`POST /api/knowledge/search/`** → pasa filtros a FastAPI `/search/`. Response al cliente: reenvía `response["results"]` sin modificar.

**`POST /api/knowledge/ask/`** → construye payload para FastAPI `/ask/`:
```python
payload = {
    'question':               request.data['question'],
    'session_id':             request.data.get('session_id') or str(uuid.uuid4()),
    'user_id':                request.auth['user_id'],
    'user_role':              role,
    'has_pricing_permission': has_pricing,
    'allowed_visibility':     allowed_visibility,
    'language':               request.META.get('HTTP_ACCEPT_LANGUAGE', 'es')[:2],
    'top_k':                  5,
    'filters':                {'domain': domain_filter} if domain_filter else {},
}
```

Post-respuesta: `calculate_retention()` → INSERT `ConversationLog`. `chunks_used` se persiste desde el response de FastAPI — **no se reenvía al cliente.**

Timeout: 5s → 503.

**Response al cliente:**
```json
{
  "answer": "...",
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "sources": [...]
}
```

Si `session_id` no venía en el request, el autogenerado (UUID4) se devuelve aquí.

---

### Item 14: Tests

Ver LOTE_SM_SPRINT8 v3.15 para la lista completa de tests (es extensa). Resumen de categorías:

**Pilar A:** auth migration PK, permisos CEO, JWT claims, guardias ANONYMOUS/sin-permiso-base, retención con 4 casos + signal + cron.

**Pilar B:** indexer SUCCESS/REJECTED/SKIPPED/FAILED, anti-fantasma (válido→REJECTED), watcher, auth FastAPI, filtros pricing/visibility, sliding window Redis, namespace isolation, multi-turn session_id, SQL WHERE antes de LIMIT.

**Docker smoke tests (ejecutar post-deploy):**
```bash
# /status/ sin auth → 200
docker compose exec mwt-knowledge curl -s http://localhost:8001/status/

# /search/ con token válido, sin body → 422
docker compose exec mwt-knowledge sh -c 'curl -s -o /dev/null -w "%{http_code}" -X POST -H "X-Internal-Token: $KNOWLEDGE_INTERNAL_TOKEN" http://localhost:8001/search/'

# /search/ sin header → 401
docker compose exec mwt-knowledge curl -s -o /dev/null -w "%{http_code}" -X POST http://localhost:8001/search/

# /search/ con token incorrecto → 401
docker compose exec mwt-knowledge curl -s -o /dev/null -w "%{http_code}" -X POST -H "X-Internal-Token: wrong" http://localhost:8001/search/
```

**Regresión:** todos los endpoints Sprints 1–7 funcionales, login CEO ok, Beat tasks ejecutando.

---

## Nuevos endpoints Sprint 8

| Método | Path | Auth | Descripción |
|--------|------|------|-------------|
| POST | `/api/auth/token/` | credenciales | Extiende JWT Sprint 0 |
| POST | `/api/auth/token/refresh/` | refresh token | Sin cambios (Sprint 0) |
| POST | `/api/admin/users/` | Session + MANAGE_USERS | Crear usuario |
| GET | `/api/admin/users/` | Session + MANAGE_USERS | Listar usuarios |
| GET | `/api/admin/users/{id}/` | Session + MANAGE_USERS | Detalle |
| PATCH | `/api/admin/users/{id}/permissions/` | Session + MANAGE_USERS | Asignar permisos |
| GET | `/api/admin/users/{id}/permissions/` | Session + MANAGE_USERS | Ver permisos |
| POST | `/api/knowledge/search/` | JWT + ASK_KNOWLEDGE_* | Búsqueda semántica |
| POST | `/api/knowledge/ask/` | JWT + ASK_KNOWLEDGE_* | Pregunta con Claude |

FastAPI interno (`/search/`, `/ask/`, `/status/`, `/reindex/`) — solo red Docker, nunca expuesto.

---

## Cómo saber que Sprint 8 está terminado

1. `MWTUser` operativo, CEO migrado con todos sus permisos, login consola funcional
2. CEO puede crear usuarios y asignar permisos via API admin
3. JWT extendido funcional
4. `mwt-knowledge` arranca, monitorea `/docs/`, indexa `.md` con stamp=VIGENTE
5. ~120 `.md` indexados en pgvector
6. `POST /api/knowledge/search/` < 1.5s end-to-end
7. `POST /api/knowledge/ask/` < 5s
8. Multi-turn funcional: Redis con prefijo `kw:`, sliding 20 msgs, TTL 2h
9. `ConversationLog` con retención diferenciada
10. Tests passing, regresión Sprints 1–7 limpia

---

## Qué NO hacer

- No tocar el frontend de Sprint 7
- No crear UI de knowledge (es Sprint 9)
- No migrar histórico de `django_admin_log`
- No crear usuarios seed — el CEO los crea post-deploy
- No usar `getattr(request.auth, 'payload', {})` — siempre `request.auth.get()`
- No importar constantes del app dentro de migraciones — listas congeladas
- No poner `--scheduler DatabaseScheduler` en celery-beat
