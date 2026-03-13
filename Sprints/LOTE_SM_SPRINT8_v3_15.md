# LOTE_SM_SPRINT8 — Auth + Knowledge Container
status: DRAFT — revisión final CEO
visibility: INTERNAL
stamp: DRAFT
domain: Plataforma
version: 3.0
sprint: 8
priority: P0
depends_on: LOTE_SM_SPRINT7
refs: ENT_PLAT_KNOWLEDGE, ENT_PLAT_LEGAL_ENTITY, ENT_PLAT_INFRA, ENT_PLAT_SEGURIDAD
revisado_por: Arquitecto (Claude) — 2026-03-12
nota: Nada ejecutado aún. v1.0 FROZEN prematuramente. v2.0 identificó conflictos. v3.0 los resuelve todos — Alejandro implementa sin preguntas.

---

## Objetivo

Dos pilares en secuencia estricta A → B:

**Pilar A — Identidad:** Extender `auth.User` a `MWTUser`, roles base, permisos granulares, JWT extendido, log de conversaciones con retención.

**Pilar B — Knowledge:** Contenedor `mwt-knowledge` que indexa `.md` del KB en pgvector y expone búsqueda semántica + respuesta Claude con historial multi-turn.

---

## Decisiones arquitectónicas — resueltas por el arquitecto

### D-01: Sin LegalEntityRef — FK directa a LegalEntity
`MWTUser.legal_entity` es FK a `LegalEntity` (app existente desde Sprint 5, modelo canónico per `ENT_PLAT_LEGAL_ENTITY`). No crear `LegalEntityRef` — viola POL_DETERMINISMO. El modelo ya existe.

### D-02: Inventario FKs auth.User — definido aquí
Los modelos de Sprints 1–7 que pueden tener FK a `auth.User` son:
- `EventLog.triggered_by` (Sprint 1)
- `ArtifactInstance.created_by` (Sprint 1–2)
- `Transfer.created_by` (Sprint 5)

**Apps contrib de Django que también referencian al usuario** (requieren atención al hacer swap de `AUTH_USER_MODEL`):
- `django.contrib.admin` → `LogEntry.user` FK al user model. **Decisión Sprint 8:** no se migra el histórico de `django_admin_log` — el sistema lleva Sprints 0–7 pero el uso del admin ha sido mínimo. El DONE de Item 1 se acota a "admin login funciona con `MWTUser`"; registros históricos de `LogEntry` anteriores al swap quedarán con FK huérfana (acceptable en este stage). Si en el futuro se necesita integridad histórica, la migración SQL es: `UPDATE django_admin_log SET user_id = <nuevo_id> WHERE user_id = <viejo_id>` ejecutada post-swap, preservando el mismo PK del CEO.
- `django.contrib.sessions` — no tiene FK directa al user model; no requiere acción.
- `django.contrib.auth` → tablas `auth_permission`, `auth_group` — heredadas por `MWTUser` via `AbstractUser`; se resuelven en `0001_initial`.

**Checklist Paso 1 de Item 1 (antes de tocar `AUTH_USER_MODEL`):**
1. `grep -rn "ForeignKey.*User\|auth.User" apps/` → confirmar lista de apps propias (mínimo EventLog, ArtifactInstance, Transfer)
2. `grep -rn "ForeignKey.*User\|auth.User" $(python -c "import django; print(django.__path__[0])")/contrib/` → identificar FKs contrib adicionales
3. Post-migración: verificar que admin login funciona con `MWTUser`. Histórico de `django_admin_log` queda fuera de alcance en Sprint 8 (consistente con D-02).

Alejandro en el **Paso 1 de Item 1** completa esta checklist antes de tocar `AUTH_USER_MODEL`. Si aparecen campos adicionales con FK a User en apps propias, los agrega a la lista de migraciones del Paso 7 (`makemigrations`/`migrate` de esas apps), **no** a `users/0002_migrate_ceo.py` — esa migración solo copia el CEO y crea permisos.

### D-03: JWT — extensión del Sprint 0, no implementación nueva
Sprint 0 (S0-07) ya implementó `SimpleJWT + login endpoint`. Item 3 de este sprint **extiende** ese JWT con `role` y `permissions[]` en el payload. El endpoint `POST /api/auth/token/` ya existe — se modifica el serializer, no se crea el endpoint.

### D-04: Celery Beat — usar app.conf.beat_schedule (única autoridad)
`app.conf.beat_schedule` en `config/celery.py` es la única fuente de verdad para schedules. **Paso ejecutable obligatorio en el mismo PR de Item 6:** verificar el comando del servicio `celery-beat` en `docker-compose.yml` y eliminar el flag `--scheduler django_celery_beat.schedulers:DatabaseScheduler` si existe. El servicio debe quedar sin `--scheduler` (Celery usa `app.conf` por defecto) o con `--scheduler celery.beat.PersistentScheduler`. Con `DatabaseScheduler` activo, `app.conf.beat_schedule` es ignorado silenciosamente.

Cambio exacto en `docker-compose.yml`:
```yaml
# ANTES (si existe):
celery-beat:
  command: celery -A config beat --scheduler django_celery_beat.schedulers:DatabaseScheduler

# DESPUÉS:
celery-beat:
  command: celery -A config beat -l info
```


### D-05: Redis — prefijo kw: obligatorio para knowledge
Django sessions usan el prefijo nativo de `django.contrib.sessions`. Knowledge usa prefijo `kw:` explícito en todas las keys:
- Messages: `kw:session:{user_id}:{session_id}`
- Metadata: `kw:session_meta:{user_id}:{session_id}`
Esto garantiza zero colisión independientemente de la configuración de Django sessions.

### D-06: PostgreSQL 16 + pgvector — confirmado seguro
`ENT_PLAT_INFRA` confirma PostgreSQL 16. pgvector aplica por DB. `CREATE EXTENSION IF NOT EXISTS vector` en DB `mwt` no afecta DB `paperless`. Alejandro ejecuta sin restricciones.

### D-07: Driver psycopg2-binary en mwt-knowledge
Django usa `psycopg2-binary` (estándar Django 5.x con PostgreSQL). `mwt-knowledge` usa el mismo driver para consistencia. `requirements.txt` de `mwt-knowledge` incluye `psycopg2-binary>=2.9`.

### D-08: CEO — is_api_user=True
CEO se migra con `is_api_user=True`. Habilita JWT sin afectar sesión web. La data migration `users/0002` lo establece explícitamente.

### D-09: ConversationLog en expediente BLOQUEADO — permitido
El bloqueo (C17) es estado operacional de flujo de dinero. No impide consultas de knowledge. El proxy Django no verifica estado del expediente antes de llamar `/ask/`. El log se crea normalmente.

### D-10: Signals concurrentes en Expediente CERRADO — on_commit
Signal `retain_until` de ConversationLog y signal de Transfer (Sprint 5) ambas disparan en `post_save` de Expediente. Ambas deben usar `transaction.on_commit()` para evitar condición de carrera. Alejandro verifica que la signal de Sprint 5 ya usa `on_commit`. La nueva signal de Sprint 8 lo implementa obligatoriamente.

### D-11: Frontend Sprint 7 — no se toca
Knowledge es canal API-only en Sprint 8 (JWT). La consola mwt.one no expone UI de knowledge. El frontend de Sprint 7 queda intacto. UI de knowledge se decide en Sprint 9.

### D-12: Usuarios seed — CEO único por ahora
El sistema hoy tiene solo el superuser CEO. Los roles INTERNAL, CLIENT_MARLUVAS, CLIENT_TECMATER se crean via `POST /api/admin/users/` después del deploy. No hay seed data de otros usuarios en Sprint 8 — el CEO los crea desde la consola o via API.

### D-13: visibility=CEO-ONLY excluida del agente knowledge
Los archivos con `visibility: CEO-ONLY` en el KB (Claude Project) **no se indexan** en `knowledge_chunks`. Esta visibilidad existe para información sensible que el CEO consulta directamente vía Claude Project, no a través del agente mwt-knowledge. El indexer los rechaza con `reason: ceo_only_excluded`. Esto es una decisión de diseño intencional, no un error de validación.

---

## Modelo de roles y permisos

```python
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
```

---

## PILAR A — Identidad

### Item 1: MWTUser

- **Agente:** AG-02
- **Archivos:** `apps/users/models.py` (nueva app), `settings.py`, migraciones

**Paso obligatorio antes de código — inventario FKs:**
Ejecutar en repo: `grep -rn "ForeignKey.*User\|auth.User" apps/` y listar todos los resultados. Arquitecto definió lista base en D-02 (EventLog, ArtifactInstance, Transfer). Si aparecen campos adicionales con FK a User en apps propias, agregarlos a la lista de migraciones del Paso 7 (`makemigrations`/`migrate` de esas apps), **no** a `users/0002_migrate_ceo.py`.

**Modelo:**
```python
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

**Nota D-01:** `legal_entity` es FK a `LegalEntity` existente (Sprint 5, app `core` o `expedientes` — Alejandro usa el app_label correcto según donde vive el modelo). No crear modelo nuevo.

**Secuencia migración (orden estricto):**
1. `python manage.py startapp users`
2. Definir **ambos** modelos `MWTUser` + `UserPermission` en `users/models.py`
3. Activar `AUTH_USER_MODEL = 'users.MWTUser'` en `settings.py` **en el mismo commit/estado de código** que la definición del modelo — antes de correr cualquier migración. Django requiere que el swap esté activo al generar `0001_initial` para resolver correctamente los M2M heredados (`groups`, `user_permissions`) y evitar conflictos de reverse accessor con `auth.User`.
4. `python manage.py makemigrations users` → genera `0001_initial` con `MWTUser + UserPermission`
5. `python manage.py migrate users` → aplica `0001_initial`
6. Crear `users/0002_migrate_ceo.py` — data migration que copia el CEO actual a `MWTUser`:
   - `pk = old_user.id` **explícito**
   - Campos: `role='CEO'`, `is_api_user=True`, más todos los campos base copiados del objeto original
   - Permisos CEO: **lista local congelada de strings** — nunca importar `ROLE_PERMISSION_CEILING` ni ninguna constante del app dentro de una migración. Si el enum cambia en el futuro, la migración histórica debe seguir siendo determinista.
   - Patrón ejecutable:
   ```python
   # users/0002_migrate_ceo.py
   # IMPORTANTE: lista congelada — no importar constantes del app
   # Debe coincidir exactamente con ROLE_PERMISSION_CEILING[CEO] definido en el modelo
   CEO_PERMISSIONS = [
       'ask_knowledge_ops',
       'ask_knowledge_products',
       'ask_knowledge_pricing',
       'view_expedientes_own',    # incluido en techo CEO — faltaba
       'view_expedientes_all',
       'view_costos',
       'download_documents',
       'manage_users',
   ]

   def migrate_ceo(apps, schema_editor):
       OldUser = apps.get_model('auth', 'User')
       MWTUser = apps.get_model('users', 'MWTUser')
       UserPermission = apps.get_model('users', 'UserPermission')
       old = OldUser.objects.get(is_superuser=True)
       MWTUser.objects.create(
           id=old.id,              # preservar PK — crítico
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
           UserPermission.objects.create(
               user_id=old.id,
               permission=perm,
               granted_by_id=old.id,
           )

   class Migration(migrations.Migration):
       dependencies = [('users', '0001_initial')]
       operations = [migrations.RunPython(migrate_ceo, migrations.RunPython.noop)]
   ```
   - `python manage.py migrate users` → aplica `0002_migrate_ceo`

7. Generar y aplicar migraciones de apps con FK a `auth.User` (EventLog, ArtifactInstance, Transfer — lista de D-02): `python manage.py makemigrations` → `python manage.py migrate`
8. `python manage.py check` sin errores → login CEO funciona → Django Admin accesible para el CEO (**alcance:** acceso básico al admin UI con el nuevo `MWTUser`; customización de admin panels para módulos Sprints 1–7 es post-Sprint 8)

**Criterio de done:**
- [ ] App `users` creada
- [ ] `MWTUser` con todos los campos incluyendo FK a `LegalEntity` existente
- [ ] `AUTH_USER_MODEL = 'users.MWTUser'` activo
- [ ] CEO migrado con `role=CEO`, `is_api_user=True`, todos sus `UserPermission`
- [ ] **PK preservado:** `MWTUser.objects.get(username=CEO_USERNAME).id == old_auth_user.id` (verificar antes de alterar FKs de apps existentes)
- [ ] Migraciones de FKs en apps existentes aplicadas
- [ ] `python manage.py check` sin errores
- [ ] Login CEO en consola funciona post-migración

---

### Item 2: UserPermission

- **Agente:** AG-02
- **Dependencia:** Item 1 aprobado

```python
class UserPermission(models.Model):
    user       = models.ForeignKey(MWTUser, on_delete=models.CASCADE, related_name='permissions_set')
    permission = models.CharField(max_length=50, choices=Permission.choices)
    granted_by = models.ForeignKey(MWTUser, on_delete=models.SET_NULL, null=True, related_name='granted_permissions')
    granted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'permission')
```

**Criterio de done:**
- [ ] Modelo creado y migrado
- [ ] Validación en `save()`: permiso fuera del techo del rol → `ValidationError`
- [ ] CEO tiene todos sus permisos pre-asignados (creados por `users/0002`)

---

### Item 3: JWT extendido

- **Agente:** AG-02
- **Dependencia:** Item 1 aprobado
- **Nota D-03:** El endpoint `POST /api/auth/token/` ya existe (Sprint 0). Solo modificar el serializer.
- **Nota user_id:** Sprint 0 ya incluye `user_id` en el payload JWT. Sprint 8 **preserva** ese claim y añade `role`, `legal_entity_id`, `permissions[]` — sin remover ningún claim existente. `request.auth['user_id']` sigue disponible en Item 12 (Redis namespace) e Item 13 (ConversationLog).

```python
class MWTTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        # Preserva: user_id (Sprint 0). Añade:
        token['role'] = user.role
        token['legal_entity_id'] = str(user.legal_entity_id) if user.legal_entity_id else None
        token['permissions'] = list(user.permissions_set.values_list('permission', flat=True))
        return token

    def validate(self, attrs):
        # Paso 1: autenticar credenciales (username/password) — sin emitir tokens aún
        # super().validate() autentica y asigna self.user; los tokens se construyen internamente
        # pero la guardia debe ejecutarse antes de que el response (con tokens) se devuelva.
        # Secuencia: autenticar → guardia is_api_user → construir y devolver tokens.
        data = super().validate(attrs)   # autentica y popula self.user; tokens ya en `data`
        # Paso 2: guardia is_api_user — rechazar antes de devolver el response con tokens
        if not self.user.is_api_user:
            raise AuthenticationFailed(
                {'error': 'api_access_not_enabled', 'detail': 'Este usuario no tiene acceso JWT habilitado.'}
            )
        # Paso 3: devolver tokens solo si la guardia pasó
        return data
```

**Nota:** La guardia usa `AuthenticationFailed` (HTTP 401) — decisión definitiva. No usar `PermissionDenied` (403) para este caso.

**Nota de secuencia:** `super().validate()` de `simplejwt` autentica credenciales y construye los tokens en `data`, pero no los envía — eso ocurre cuando `validate()` retorna. La guardia `is_api_user` interrumpe antes del `return data`, por lo que ningún token llega al cliente si la guardia falla. El comentario en código documenta esta secuencia para que no se reordene en refactorización.

**Configuración:**
```python
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=8),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=30),
    'ALGORITHM': 'HS256',
}
```

**Criterio de done:**
- [ ] La view de `POST /api/auth/token/` usa `MWTTokenObtainPairSerializer` como serializer activo
- [ ] JWT payload incluye `user_id` (Sprint 0, preservado), `role`, `legal_entity_id`, `permissions[]`
- [ ] `is_api_user=False` → `POST /api/auth/token/` → 401 (`AuthenticationFailed`)
- [ ] Test: access token emitido contiene `user_id`, `role`, `legal_entity_id`, `permissions`
- [ ] Sesión web CEO no se toca — sigue funcionando

---

### Item 4: Decoradores @require_permission

- **Agente:** AG-02
- **Dependencia:** Items 1–3 aprobados
- **Archivos:** `apps/users/decorators.py`, `apps/users/mixins.py`

**Camino A — Session (consola, endpoints /api/admin/):**
```python
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
```

**Camino B — JWT (endpoints /api/knowledge/ — sin DB lookup):**
```python
def require_permission_jwt(perm: Permission):
    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return JsonResponse({'error': 'auth_required'}, status=401)
            # JWTStatelessUserAuthentication expone claims directamente en request.auth
            # Usar request.auth.get() en todos los endpoints y decoradores — nunca getattr(request.auth, 'payload', {})
            token_permissions = request.auth.get('permissions', [])
            if perm not in token_permissions:
                return JsonResponse({'error': 'permission_denied', 'required': perm}, status=403)
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator
```

**Nota D-JWT:** Con `JWTStatelessUserAuthentication` (DRF SimpleJWT), `request.auth` es el payload decodificado como dict. La interfaz correcta es `request.auth['campo']` o `request.auth.get('campo', default)` **en todos los endpoints y decoradores del sprint**. `getattr(request.auth, 'payload', {})` es incorrecto y falla en runtime.

**Criterio de done:**
- [ ] Ambos decoradores implementados
- [ ] Mixins class-based equivalentes (`PermissionRequiredMixin`, `JWTPermissionRequiredMixin`)
- [ ] Endpoints `/api/knowledge/` usan exclusivamente `require_permission_jwt`

---

### Item 5: Endpoints admin — gestión de usuarios

- **Agente:** AG-02
- **Dependencia:** Items 1–4 aprobados
- **Auth:** Session + `MANAGE_USERS`

`POST /api/admin/users/` — crear usuario:
```json
{ "username": "sondel_ops", "email": "ops@sondel.com", "password": "...",
  "role": "CLIENT_MARLUVAS", "legal_entity_id": "uuid-de-LegalEntity",
  "whatsapp_number": "+50688888888", "is_api_user": true }
```
**El usuario se crea con cero `UserPermission`.** Los permisos se asignan en un paso separado via `PATCH /permissions/`. No hay set inicial automático — el CEO asigna explícitamente lo que necesita.

`PATCH /api/admin/users/{id}/permissions/` — reemplaza todos los permisos:
```json
{ "permissions": ["ask_knowledge_ops", "view_expedientes_own"] }
```
**Contrato exacto:**
1. Calcular `ceiling = ROLE_PERMISSION_CEILING[user.role]`
2. `accepted = requested ∩ ceiling`
3. `rejected = requested - ceiling`
4. **Guardia last admin:** verificar que después del reemplazo al menos un usuario activo tendrá `MANAGE_USERS`. Aplica tanto a self-patch como a patch de terceros. Si el reemplazo dejaría la plataforma sin ningún usuario activo con `MANAGE_USERS` → responder **400** antes de cualquier write:
```json
{ "error": "cannot_remove_last_manage_users",
  "detail": "No es posible quitar MANAGE_USERS: ningún otro usuario activo lo tendría." }
```
5. Eliminar **todos** los `UserPermission` del usuario → INSERT atómico de `accepted`, cada uno con `granted_by=request.user` → todo en una sola transacción
6. Respuesta **200** con set final persistido:
```json
{
  "permissions_applied": ["ask_knowledge_ops", "view_expedientes_own"],
  "permissions_rejected": ["view_costos"]
}
```
El campo `permissions_rejected` informa al caller qué no se aplicó (fuera del techo del rol). No es silencioso — siempre aparece en el response (vacío `[]` si no hay rechazos). Esto no es un error 4xx: el request fue válido, simplemente el rol no habilita esos permisos.

`GET /api/admin/users/` — lista todos.
`GET /api/admin/users/{id}/` — detalle con permisos.
`GET /api/admin/users/{id}/permissions/` — permisos actuales.

**Criterio de done:**
- [ ] API admin de usuarios funcionando: POST crear, GET listar, GET detalle, GET permisos, PATCH permisos
- [ ] Password hasheado con `make_password()`
- [ ] `legal_entity_id` valida contra `LegalEntity` existente
- [ ] Usuario nuevo creado con cero `UserPermission`
- [ ] `PATCH /permissions/`: cada `UserPermission` insertado tiene `granted_by=request.user`
- [ ] Self-patch CEO quitando `MANAGE_USERS` → 400 `cannot_remove_last_manage_users`
- [ ] Patch a tercero que dejaría plataforma sin `MANAGE_USERS` → 400 mismo error

---

### Item 6: ConversationLog + retención

- **Agente:** AG-02
- **Dependencia:** Item 1 aprobado
- **Archivos:** `apps/knowledge/models.py`
- **Nota D-09:** Conversaciones en expediente BLOQUEADO son permitidas — no agregar verificación de estado.
- **Nota D-10:** Signal usa `transaction.on_commit()` obligatoriamente.

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

**Autoridad única de cálculo — `calculate_retention()`:**
Esta función es la única fuente de verdad para `retain_until`. Se llama **antes del `save()`** al crear cada `ConversationLog` desde el proxy Django. La signal de expediente CERRADO la complementa (no la reemplaza) para logs ya persistidos.

```python
def calculate_retention(
    user_role: str,
    expediente_ref=None,
    as_of_date: date = None,  # obligatorio — el caller debe proveerlo siempre
) -> date | None:
    """
    Reglas (en orden de evaluación):
    - Sin expediente_ref → as_of_date + RETENTION_DAYS[user_role]
    - Con expediente abierto (status != 'CERRADO') → None  (signal lo completará al cerrar)
    - Con expediente ya cerrado → expediente.closed_at.date() + 365d

    as_of_date: obligatorio. El proxy pasa timezone.now().date() una sola vez.
    Los tests pasan una fecha fija y comparan contra esa misma fecha.
    La función no lee el reloj internamente — esa responsabilidad es del caller.
    """
    if as_of_date is None:
        raise ValueError("calculate_retention: as_of_date es obligatorio")
    if expediente_ref is None:
        return as_of_date + timedelta(days=RETENTION_DAYS.get(user_role, 30))
    if expediente_ref.status != 'CERRADO':
        return None
    # Invariante: status='CERRADO' requiere closed_at NOT NULL
    if expediente_ref.closed_at is None:
        raise ValueError(
            f"calculate_retention: Expediente {expediente_ref.pk} tiene status=CERRADO pero closed_at es None"
        )
    return expediente_ref.closed_at.date() + timedelta(days=365)
```

**Invariante del modelo Expediente:** `status='CERRADO'` implica `closed_at NOT NULL`. Esta precondición debe ser garantizada por el state machine (command de cierre siempre asigna `closed_at`). `calculate_retention()` y la signal la asumen y lanzan `ValueError` explícito si se viola — para detectar temprano un bug en el state machine, no silenciar el error.

```python
from django.utils import timezone
from apps.knowledge.utils import calculate_retention

as_of = timezone.now().date()   # una sola lectura del reloj — pasar siempre
ConversationLog.objects.create(
    ...
    retain_until=calculate_retention(role, expediente_obj, as_of_date=as_of),
)
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
**Nota D-04:** Eliminar `--scheduler django_celery_beat.schedulers:DatabaseScheduler` del servicio `celery-beat` en `docker-compose.yml` en este mismo PR. Ver D-04 para el cambio exacto.

**Signal — cubre logs ya persistidos cuando el expediente se cierra:**
```python
@receiver(post_save, sender=Expediente)
def update_conversation_retention(sender, instance, **kwargs):
    if instance.status == 'CERRADO':
        # Invariante: status='CERRADO' requiere closed_at NOT NULL
        # Mismo contrato que calculate_retention() — mismo mensaje canónico
        if instance.closed_at is None:
            raise ValueError(
                f"calculate_retention: Expediente {instance.pk} tiene status=CERRADO pero closed_at es None"
            )
        def _update():
            ConversationLog.objects.filter(
                expediente_ref=instance,
                retain_until__isnull=True
            ).update(retain_until=instance.closed_at.date() + timedelta(days=365))
        transaction.on_commit(_update)  # obligatorio — D-10
```
La guardia se evalúa antes del `on_commit` — si el state machine rompe la precondición, el error es inmediato y tiene el mismo mensaje que `calculate_retention()`, facilitando el diagnóstico.

**Criterio de done:**
- [ ] Modelo `ConversationLog` creado y migrado
- [ ] `calculate_retention()` implementado como función independiente en `apps/knowledge/utils.py`
- [ ] Proxy Django llama `calculate_retention()` antes de cada `save()` de `ConversationLog`
- [ ] Signal con `transaction.on_commit()` — no sin él
- [ ] `purge_expired_logs` en `app.conf.beat_schedule` junto a las tasks existentes de Sprint 2
- [ ] `--scheduler DatabaseScheduler` eliminado del servicio `celery-beat` en `docker-compose.yml`
- [ ] Check post-deploy: `docker compose logs celery-beat` muestra las 3 tasks cargadas (`evaluate_credit_clocks`, `process_pending_events`, `purge_expired_logs`) — si alguna no aparece, el scheduler sigue siendo incorrecto
- [ ] Índice `(retain_until, created_at)` creado

---

## PILAR B — Knowledge Container

### Item 7: Schema PostgreSQL

- **Agente:** AG-02
- **Dependencia:** Pilar A completo
- **Nota D-06:** PostgreSQL 16 confirmado — pgvector seguro.

```sql
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE knowledge_chunks (
  id              SERIAL PRIMARY KEY,
  source_file     VARCHAR(255) NOT NULL,  -- path relativo desde /docs/ — 255 para paths con subdirectorios
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

**Criterio de done:**
- [ ] Extensión vector activa en DB mwt
- [ ] Tablas y todos los índices creados via migración Django
- [ ] Migración aplica sin tocar tablas de expedientes

---

### Item 8: Docker service mwt-knowledge

- **Agente:** AG-07
- **Dependencia:** Item 7 aprobado
- **Nota D-07:** Usar `psycopg2-binary>=2.9` en requirements.txt

**Estructura de archivos del servicio:**
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

**`services/mwt-knowledge/Dockerfile`:**
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

**`services/mwt-knowledge/entrypoint.sh`:**
```bash
#!/bin/bash
set -e

echo "[mwt-knowledge] Iniciando watcher en background..."
python watcher.py &

echo "[mwt-knowledge] Iniciando FastAPI en :8001..."
exec uvicorn main:app --host 0.0.0.0 --port 8001 --workers 1
```
El watcher corre en background (`&`). `uvicorn` corre en foreground con `exec` — esto garantiza que Docker recibe las señales correctamente (SIGTERM en `docker stop`). Si el watcher muere, el contenedor sigue vivo pero indexación automática se detiene — acceptable, FastAPI sigue respondiendo.

**Agregar a docker-compose.yml:**
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

**`services/mwt-knowledge/requirements.txt`:**
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
OPENAI_API_KEY=sk-...
KNOWLEDGE_INTERNAL_TOKEN=<32 chars aleatorio>
KNOWLEDGE_SERVICE_URL=http://mwt-knowledge:8001
MIN_SIMILARITY=0.5
```

**Criterio de done:**
- [ ] `services/mwt-knowledge/Dockerfile` y `entrypoint.sh` creados y con permisos correctos
- [ ] Servicio en docker-compose.yml
- [ ] `./knowledge-docs/` con `.gitkeep`
- [ ] `docker compose up mwt-knowledge` sin errores
- [ ] Logs: "Iniciando watcher en background..." + "Iniciando FastAPI en :8001" en `docker compose logs mwt-knowledge`

---

### Item 9: Watcher

- **Agente:** AG-02
- **Archivo:** `services/mwt-knowledge/watcher.py`

Comportamiento:
- Monitorea `/docs/` recursivamente con `watchdog`
- Eventos: `FileCreatedEvent`, `FileModifiedEvent`, `FileDeletedEvent` — solo `.md`
- `FileDeletedEvent`: DELETE chunks del archivo + INSERT log `REJECTED` reason `archivo eliminado`
- Debounce 2s por archivo
- Hilo separado — no bloquea FastAPI
- Al iniciar: scan inicial de todos los `.md` (indexer los salta si hash no cambió)

---

### Item 10: Indexer

- **Agente:** AG-02
- **Archivo:** `services/mwt-knowledge/indexer.py`

**Header canónico que el indexer valida** (primeras 10 líneas del `.md`):
```
status: VIGENTE
visibility: INTERNAL
stamp: VIGENTE
domain: Plataforma
version: 1.0
```

**Reglas de validación de header (los 5 campos son obligatorios — faltante o inválido → REJECTED):**

| Campo | Valores válidos | Acción si falla |
|-------|----------------|-----------------|
| `status` | `VIGENTE` | REJECTED — reason: `invalid_status:{valor}` |
| `stamp` | `VIGENTE` | REJECTED — reason: `stamp_not_vigente` |
| `visibility` | `PUBLIC` \| `INTERNAL` \| `CEO-ONLY` | REJECTED — reason: `invalid_visibility:{valor}` |
| `domain` | cualquier string no vacío | REJECTED — reason: `domain_empty` |
| `version` | semver o string no vacío | REJECTED — reason: `version_empty` |

Reglas adicionales post-validación:
- `visibility = CEO-ONLY` → `REJECTED` — reason: `ceo_only_excluded` (D-13: CEO-ONLY es para Claude Project, no para el agente knowledge)
- Hash sin cambio → `SKIPPED` (no es error — el chunk está actualizado)
- `doc_type` extraído del prefijo del nombre: `PLB_` → `PLB`, `ENT_` → `ENT`, etc.

**`is_pricing` — derivación automática en el indexer:**
Un chunk se marca `is_pricing = true` si el nombre del archivo fuente pertenece a alguno de estos prefijos/archivos: `ENT_COMERCIAL_PRICING`, `ENT_COMERCIAL_COSTOS`, `ENT_COMERCIAL_FINANZAS`, o si el `domain` del header es `Pricing` o `Costos`. En cualquier otro caso `is_pricing = false`. Este campo es persistido en `knowledge_chunks` y usado por `/search/` para filtrar cuando el claim `has_pricing_permission = false`.

**Chunking:** secciones `##` → máx 600 tokens por chunk (tiktoken) → batches de 100 para embeddings.

**Persistencia — transacción atómica (SUCCESS):**
```sql
BEGIN;
DELETE FROM knowledge_chunks WHERE source_file = :source_file;
INSERT INTO knowledge_chunks (...) VALUES (...);
INSERT INTO indexation_log (..., status='SUCCESS');
COMMIT;
```
Fallo → rollback completo + INSERT `FAILED`.

**Persistencia — cuando reindex termina en REJECTED:**
Si un archivo ya indexado es modificado y el nuevo header resulta inválido (`stamp=DRAFT`, `visibility=CEO-ONLY`, campo faltante, etc.), el estado final debe ser **cero chunks activos** para ese `source_file`. La regla:
```sql
BEGIN;
DELETE FROM knowledge_chunks WHERE source_file = :source_file;  -- limpiar chunks previos
INSERT INTO indexation_log (..., status='REJECTED', reason=:reason);
COMMIT;
```
Esto aplica a **cualquier** resultado REJECTED en reindex — no solo al primer indexado. Un archivo que era buscable y deja de serlo no puede dejar fantasmas en pgvector.

**Resumen de estados de salida del indexer:**

| Estado | Chunks en DB | indexation_log |
|--------|-------------|----------------|
| SUCCESS | Nuevos chunks del archivo | status=SUCCESS |
| REJECTED | 0 (previos borrados si existían) | status=REJECTED + reason |
| SKIPPED | Sin cambio (hash igual) | status=SKIPPED |
| FAILED | Sin cambio (rollback) | status=FAILED |

---

### Item 11: FastAPI interno

- **Agente:** AG-02
- **Archivo:** `services/mwt-knowledge/main.py`
- **Auth interna:** header `X-Internal-Token` con `KNOWLEDGE_INTERNAL_TOKEN` — sin él → 401

**`POST /search/`** — búsqueda semántica:
```json
{ "query": "...", "top_k": 5, "filters": { "domain": [...] },
  "exclude_pricing": false, "allowed_visibility": ["PUBLIC", "INTERNAL"] }
```
**Pipeline — implementación única:**
Todos los filtros van en el `WHERE` antes del `ORDER BY ... LIMIT top_k` — tanto los filtros de negocio como el umbral semántico. Esto garantiza que `top_k` resultados son los más relevantes dentro del espacio válido y superan el umbral mínimo de similitud.

```sql
SELECT id, source_file, section, chunk_index, content, domain, visibility, is_pricing,
       1 - (embedding <=> :query_embedding) AS similarity
FROM knowledge_chunks
WHERE stamp = 'VIGENTE'
  AND visibility = ANY(:allowed_visibility)                         -- filtro permisos
  AND (:domain_filter IS NULL OR domain = ANY(:domain_filter))     -- filtro domain (NULL = sin restricción)
  AND (:exclude_pricing = false OR is_pricing = false)             -- filtro pricing
  AND (embedding <=> :query_embedding) <= (1 - :min_similarity)   -- umbral semántico en WHERE
ORDER BY embedding <=> :query_embedding
LIMIT :top_k;
```
`:min_similarity` viene de `MIN_SIMILARITY=0.5` (env). Sin post-filtrado — todo corte ocurre antes del `LIMIT`.

**`POST /ask/`** — pregunta con Claude:
```json
{
  "question": "...", "session_id": "uuid",
  "user_id": 123, "user_role": "...",
  "has_pricing_permission": false,
  "allowed_visibility": ["PUBLIC", "INTERNAL"],
  "top_k": 5, "language": "es",
  "filters": { "domain": [...] }
}
```
- `session_id` ausente → 400 (Django siempre lo inyecta)
- `exclude_pricing` **no va en este payload** — FastAPI lo deriva internamente: `exclude_pricing = not has_pricing_permission` antes de llamar su `/search/` interno. Un solo campo de control, una sola derivación.
- Pipeline: historial Redis → `/search/` interno (con `exclude_pricing` derivado) → prompt Claude condicional por `has_pricing_permission` → append Redis → response

**Response schemas — contratos obligatorios de FastAPI:**

`POST /search/` response:
```json
{
  "results": [
    {
      "id": 123,
      "source_file": "ops/foo.md",
      "section": "Header",
      "content": "...",
      "similarity": 0.83,
      "domain": "Operación",
      "visibility": "INTERNAL",
      "is_pricing": false
    }
  ]
}
```

`POST /ask/` response:
```json
{
  "answer": "...",
  "session_id": "uuid",
  "sources": [{"source_file": "...", "section": "...", "similarity": 0.83}],
  "chunks_used": [{"id": 123, "source_file": "...", "section": "...", "content": "..."}]
}
```

**Regla de trazabilidad (aplica Item 11 + Item 13):**
- `chunks_used`: FastAPI lo incluye en response; Django proxy lo persiste en `ConversationLog.chunks_used` y **no** lo reenvía al cliente.
- `sources`: FastAPI lo incluye en response; Django proxy lo reenvía al cliente tal cual.
- `session_id`: Django proxy lo reenvía al cliente siempre.

**`GET /status/`** — métricas indexación. **Excepción de auth:** este endpoint no requiere `X-Internal-Token` — es de solo lectura, no expone chunks ni embeddings, y debe ser accesible para health checks y CI sin credenciales. Documentado aquí como excepción deliberada; todos los demás endpoints requieren `X-Internal-Token`.
**`POST /reindex/`** — re-indexa todo en background. Requiere `X-Internal-Token`.

---

### Item 12: Sesiones Redis

- **Agente:** AG-02
- **Archivo:** `services/mwt-knowledge/sessions.py`
- **Nota D-05:** Prefijo `kw:` obligatorio en todas las keys.

```
kw:session:{user_id}:{session_id}      → List JSON [{role, content, timestamp}]  TTL 2h sliding
kw:session_meta:{user_id}:{session_id} → Hash {created_at}                       TTL 2h sliding
```

**Contrato de TTL sliding — ejecutable:**
**Regla de atomicidad:** toda operación que toque ambas keys usa `pipeline(transaction=True)`. La única excepción es `redis.delete(session_key, meta_key)` — el comando `DEL` multi-key de Redis es atómico por definición del protocolo. Fuera de esa excepción explícita, no hay comandos Redis sueltos cuando se modifica el par.

**Contrato completo de `sessions.py` — implementación obligatoria:**

`get_history(user_id, session_id)`:
```python
session_exists, meta_exists = redis.exists(session_key), redis.exists(meta_key)
if session_exists != meta_exists:          # estado parcial → corrupta
    redis.delete(session_key, meta_key)    # DEL multi-key: excepción atómica permitida
    return []
if not session_exists:                     # sesión inexistente → historial vacío
    return []
# sesión válida: refrescar TTL en pipeline
with redis.pipeline(transaction=True) as pipe:
    pipe.expire(session_key, 7200)
    pipe.expire(meta_key, 7200)
    pipe.execute()
return [json.loads(m) for m in redis.lrange(session_key, 0, -1)]
```

`append_message(user_id, session_id, message)`:
```python
now_iso = datetime.now(timezone.utc).isoformat()
session_exists, meta_exists = redis.exists(session_key), redis.exists(meta_key)
if session_exists != meta_exists:          # estado parcial → limpiar y recrear
    redis.delete(session_key, meta_key)    # DEL multi-key: excepción atómica permitida
    session_exists = meta_exists = False   # forzar bootstrap en el branch siguiente

if not session_exists and not meta_exists: # sesión nueva O recién limpiada
    with redis.pipeline(transaction=True) as pipe:
        pipe.rpush(session_key, json.dumps(message))
        pipe.hset(meta_key, mapping={"created_at": now_iso})
        pipe.expire(session_key, 7200)
        pipe.expire(meta_key, 7200)
        pipe.execute()
    return  # sesión creada con primer mensaje

# sesión existente: append normal
with redis.pipeline(transaction=True) as pipe:
    pipe.rpush(session_key, json.dumps(message))
    pipe.ltrim(session_key, -20, -1)       # sliding window 20 mensajes
    pipe.expire(session_key, 7200)
    pipe.expire(meta_key, 7200)
    pipe.execute()
```

`clear_session(user_id, session_id)`:
```python
redis.delete(session_key, meta_key)  # DEL multi-key: atómico, idempotente
```

**Seguridad de sesión:** la aislación entre usuarios depende del namespace `{user_id}` en la key Redis. Un usuario solo puede construir keys con su propio `user_id` (extraído del JWT); si el `session_id` no existe bajo ese namespace, el resultado es historial vacío — no 403. No existe campo `owner_user_id`; el namespace es el control primario.

**Max 20 mensajes** (sliding window via `LTRIM` en `append_message`)

**Criterio de done:**
- [ ] `get_history()`, `append_message()`, `clear_session()` implementados en `sessions.py`
- [ ] Toda operación que toca ambas keys usa `pipeline(transaction=True)`, salvo `redis.delete(session_key, meta_key)` como excepción atómica explícita
- [ ] Test: llamar solo `get_history()` (sin writes) y verificar que TTL de ambas keys se extiende
- [ ] Test: 21 mensajes → `LLEN = 20`, el mensaje más viejo eliminado
- [ ] Test estado parcial "meta sin lista": insertar solo `kw:session_meta:*` → `get_history()` → devuelve `[]`, ambas keys eliminadas
- [ ] Test estado parcial "lista sin meta": insertar solo `kw:session:*` → `get_history()` → devuelve `[]`, ambas keys eliminadas
- [ ] Test sesión nueva: `append_message()` en sesión inexistente → `kw:session_meta:*` contiene `created_at` como string ISO-8601 válido

---

### Item 13: Django proxy /api/knowledge/

- **Agente:** AG-02
- **Dependencia:** Items 11, 12 aprobados
- **Auth:** `JWTStatelessUserAuthentication` — sin DB lookup por request
- **Nota D-11:** Frontend Sprint 7 no se toca. Este proxy es API-only.

**`POST /api/knowledge/search/`:**
Django evalúa permisos desde claims del token y construye filtros antes de llamar FastAPI.

**Regla de acceso base (evaluar primero — antes de cualquier filtro):**
- Si el usuario **no tiene** `ASK_KNOWLEDGE_OPS` **ni** `ASK_KNOWLEDGE_PRODUCTS` → **403** inmediato, sin llamar FastAPI.
- `ASK_KNOWLEDGE_PRICING` por sí solo **no habilita acceso**. Es un elevador de scope sobre un permiso base.

**Tabla de combinaciones válidas:**

| Permisos del usuario | domain filter | exclude_pricing | allowed_visibility |
|---------------------|---------------|----------------|--------------------|
| Sin OPS ni PRODUCTS | — | — | **403** |
| Solo PRICING (sin base) | — | — | **403** |
| PRODUCTS (sin OPS, sin PRICING) | `[Marca, Producto, Mercado]` | `true` | por rol |
| PRODUCTS + PRICING | `[Marca, Producto, Mercado]` | `false` | por rol |
| OPS (sin PRICING) | sin restricción | `true` | por rol |
| OPS + PRICING | sin restricción | `false` | por rol |
| OPS + PRODUCTS + PRICING | sin restricción | `false` | por rol |

**`allowed_visibility` por rol (aplica a todas las combinaciones anteriores):**
- `CEO` o `INTERNAL` → `["PUBLIC", "INTERNAL"]`
- `CLIENT_*` → `["PUBLIC"]`
- `ANONYMOUS` → **403** antes de evaluar permisos knowledge

**Pseudocódigo Django (aplica a `/search/` y `/ask/`):**
```python
has_ops      = 'ask_knowledge_ops'      in request.auth.get('permissions', [])
has_products = 'ask_knowledge_products' in request.auth.get('permissions', [])
has_pricing  = 'ask_knowledge_pricing'  in request.auth.get('permissions', [])
role         = request.auth.get('role', '')

# Guardia 1 — rol ANONYMOUS
if role == 'ANONYMOUS':
    return JsonResponse({'error': 'permission_denied'}, status=403)

# Guardia 2 — sin permiso knowledge base (OPS o PRODUCTS)
if not has_ops and not has_products:
    return JsonResponse({'error': 'permission_denied'}, status=403)

domain_filter      = None if has_ops else ['Marca', 'Producto', 'Mercado']
exclude_pricing    = not has_pricing
allowed_visibility = ['PUBLIC', 'INTERNAL'] if role in ['CEO', 'INTERNAL'] else ['PUBLIC']
```

**Response de `/api/knowledge/search/` al cliente:**
Django reenvía `response["results"]` de FastAPI sin modificar estructura, salvo manejo de errores/timeouts:
```json
{
  "results": [
    {
      "id": 123,
      "source_file": "ops/foo.md",
      "section": "Header",
      "content": "...",
      "similarity": 0.83,
      "domain": "Operación",
      "visibility": "INTERNAL",
      "is_pricing": false
    }
  ]
}
```

**`POST /api/knowledge/ask/`:**
Django inyecta todos los campos de control desde claims JWT (sin DB lookup). Usar las variables derivadas del pseudocódigo anterior (`has_ops`, `has_products`, `has_pricing`, `role`, `domain_filter`, `allowed_visibility`) — no recalcular. `exclude_pricing` **no va en este payload** — FastAPI lo deriva de `has_pricing_permission`:

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
Post-respuesta FastAPI → `calculate_retention()` → INSERT `ConversationLog` usando `user_id` del claim (sin ORM lookup adicional). `ConversationLog.chunks_used` se persiste desde `response["chunks_used"]` del payload FastAPI — este campo **no** se reenvía al cliente.
Timeout: 5s → 503 descriptivo.

**Response de `/api/knowledge/ask/` al cliente — `session_id` siempre presente:**
Django filtra el response de FastAPI y reenvía solo los campos públicos:
```json
{
  "answer": "...",
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "sources": [...]
}
```
`chunks_used` queda en `ConversationLog` para trazabilidad interna — nunca llega al cliente.
Si el caller omitió `session_id` en el request, el autogenerado (UUID4) se devuelve aquí — permitiendo que el siguiente turn lo reutilice para multi-turn coherente.


### Item 14: Tests

- **Agente:** AG-06
- **Dependencia:** Items 1–13 aprobados

**Pilar A — Auth:**
- [ ] CEO migrado: `has_permission(manage_users)` → True
- [ ] CLIENT_MARLUVAS sin permiso: `has_permission(ask_knowledge_ops)` → False
- [ ] `view_expedientes_all` asignado a CLIENT_MARLUVAS → en `permissions_rejected`
- [ ] `is_api_user=False` → `POST /api/auth/token/` → 401 (`AuthenticationFailed`)
- [ ] JWT payload contiene `user_id` (coincide con `MWTUser.id` autenticado), `role`, `legal_entity_id`, `permissions[]` — test falla si el serializer rompe cualquiera de estos claims en refactorización futura
- [ ] INTERNAL → `allowed_visibility=["PUBLIC","INTERNAL"]` inyectado
- [ ] CLIENT_* → `allowed_visibility=["PUBLIC"]` inyectado
- [ ] ANONYMOUS (role='ANONYMOUS') → 403 en Guardia 1, antes de evaluar permisos knowledge
- [ ] Usuario sin OPS ni PRODUCTS → 403 en Guardia 2
- [ ] Usuario con solo PRICING (sin OPS ni PRODUCTS) → 403 en Guardia 2

**Pilar A — Migración PK (FIX-4):**
- [ ] Test de migración integral: crear `auth.User` legacy con `id=1` + registros en `EventLog`, `ArtifactInstance` y `Transfer` apuntando a `user_id=1` → ejecutar `users/0002_migrate_ceo.py` + migraciones de FK → verificar `MWTUser.objects.get(id=1)` existe y todos los registros históricos siguen resolviendo al mismo `id=1`. El test falla si el PK cambia.
- [ ] Test permisos CEO migrados: `set(UserPermission.objects.filter(user_id=1).values_list('permission', flat=True))` == `set(ROLE_PERMISSION_CEILING[UserRole.CEO])` — el test falla si `CEO_PERMISSIONS` en la migración no cubre el techo completo del rol.

**Pilar A — Retención (FIX-5):**
- [ ] Caso 1 — sin expediente: `as_of = date(2026, 1, 1)` → `calculate_retention('CEO', None, as_of)` == `date(2027, 1, 1)`. Comparar contra `as_of + 365d`, no contra `date.today()`.
- [ ] Caso 2 — expediente abierto: `calculate_retention('CEO', exp_abierto, as_of)` == `None`
- [ ] Caso 3 — expediente ya CERRADO al crear el log (sin signal): `exp.status='CERRADO'`, `exp.closed_at=date(2025, 6, 1)` → `calculate_retention('CEO', exp, as_of)` == `date(2026, 6, 1)`. Este caso no depende de la signal — el valor debe estar correcto en el `save()` inicial.
- [ ] Invariante `closed_at`: `exp.status='CERRADO'`, `exp.closed_at=None` → `calculate_retention()` lanza `ValueError` con mensaje descriptivo. Protege contra bugs en el state machine.
- [ ] Signal expediente CERRADO → actualiza `retain_until` de logs previos con `retain_until=None`
- [ ] Cron: log con `retain_until < today` → eliminado

**Pilar B — Knowledge:**
- [ ] `.md` stamp=VIGENTE → SUCCESS, chunks en DB
- [ ] `.md` stamp=DRAFT → REJECTED
- [ ] **Transición válido → REJECTED (test anti-fantasma):** indexar un `.md` válido (SUCCESS, chunks en DB) → modificarlo cambiando `stamp: DRAFT` o `visibility: CEO-ONLY` → disparar reindex → verificar: (1) `knowledge_chunks WHERE source_file = :archivo` devuelve 0 filas, (2) `indexation_log` registra `status=REJECTED` con `reason` correcta. El test falla si quedan chunks previos en pgvector.
- [ ] visibility=CEO-ONLY → REJECTED
- [ ] Hash sin cambio → SKIPPED
- [ ] Archivo eliminado → chunks borrados
- [ ] Fallo OpenAI → FAILED, sin chunks parciales
- [ ] Crear `.md` en /docs/ → indexer dispara < 3s
- [ ] Sin `X-Internal-Token` → 401
- [ ] `has_pricing_permission=false` → chunks pricing excluidos
- [ ] `allowed_visibility=["PUBLIC"]` → chunks INTERNAL no aparecen
- [ ] 20+ mensajes → sliding window elimina el más viejo
- [ ] `user_id=1` intenta leer sesión creada por `user_id=2` → historial vacío (namespace aísla automáticamente, no 403)
- [ ] **Multi-turn `session_id`:** llamar `POST /api/knowledge/ask/` sin `session_id` en request → response incluye `session_id` UUID válido → usar ese UUID en segunda llamada → segunda respuesta tiene historial de la primera (context preserved)

**Pilar B — SQL WHERE antes de LIMIT (FIX-6):**
- [ ] Sembrar corpus mixto: 10 chunks públicos sin pricing + 5 chunks INTERNAL + 5 chunks con `is_pricing=true`. Llamar `/search/` con `top_k=5`, `allowed_visibility=["PUBLIC"]`, `exclude_pricing=false`. Verificar que los 5 resultados son todos `visibility=PUBLIC`. Si los filtros se aplicaran post-LIMIT, podrían aparecer chunks INTERNAL. El test detecta esa regresión.
- [ ] Test umbral semántico en WHERE: sembrar chunks con similitud conocida — algunos por encima de `MIN_SIMILARITY=0.5` y algunos por debajo. Verificar que los resultados devueltos son todos `similarity >= 0.5` y que el recuento no supera `top_k`. El test falla si `MIN_SIMILARITY` se mueve al post-LIMIT.

**Docker smoke test (FIX-7):**
- [ ] `docker compose build mwt-knowledge` → sin errores
- [ ] `docker compose up -d mwt-knowledge` → logs contienen "Iniciando watcher en background" + "Iniciando FastAPI en :8001"
- [ ] `docker compose exec mwt-knowledge curl -s http://localhost:8001/status/` → 200 sin header (excepción explícita — ver Item 11)
- [ ] `docker compose exec mwt-knowledge sh -c 'curl -s -o /dev/null -w "%{http_code}" -X POST -H "X-Internal-Token: $KNOWLEDGE_INTERNAL_TOKEN" http://localhost:8001/search/'` → 422 (token válido, body faltante)
- [ ] `docker compose exec mwt-knowledge curl -s -o /dev/null -w "%{http_code}" -X POST http://localhost:8001/search/` → 401 (sin header)
- [ ] `docker compose exec mwt-knowledge curl -s -o /dev/null -w "%{http_code}" -X POST -H "X-Internal-Token: wrong" http://localhost:8001/search/` → 401 (token incorrecto)
- [ ] Este smoke test se agrega como paso de CI/verificación post-deploy — no como unit test Django

**Regresión:**
- [ ] Todos los endpoints Sprints 1–7 funcionales post-migración AUTH_USER_MODEL
- [ ] Login CEO en consola no afectado
- [ ] `evaluate_credit_clocks` y `process_pending_events` siguen ejecutando en Beat

---


## Nuevos endpoints Sprint 8

| Método | Path | Auth | Descripción |
|--------|------|------|-------------|
| POST | /api/auth/token/ | credenciales | Extiende JWT Sprint 0 con rol + permisos |
| POST | /api/auth/token/refresh/ | refresh token | Existente Sprint 0 — sin cambios |
| POST | /api/admin/users/ | Session + MANAGE_USERS | Crear usuario |
| GET | /api/admin/users/ | Session + MANAGE_USERS | Listar usuarios |
| GET | /api/admin/users/{id}/ | Session + MANAGE_USERS | Detalle usuario |
| PATCH | /api/admin/users/{id}/permissions/ | Session + MANAGE_USERS | Asignar permisos |
| GET | /api/admin/users/{id}/permissions/ | Session + MANAGE_USERS | Ver permisos |
| POST | /api/knowledge/search/ | JWT + ASK_KNOWLEDGE_* | Búsqueda semántica |
| POST | /api/knowledge/ask/ | JWT + ASK_KNOWLEDGE_* | Pregunta con Claude |

FastAPI interno (`/search/`, `/ask/`, `/status/`, `/reindex/`) — solo red Docker interna, nunca expuesto.

---

## Criterio SPRINT 8 DONE

1. `MWTUser` operativo, CEO migrado con todos sus permisos, login consola funcional
2. CEO puede crear usuarios y asignar permisos via API admin
3. JWT extendido funcional (extensión Sprint 0)
4. `mwt-knowledge` arranca, monitorea `/docs/`, indexa `.md` con stamp=VIGENTE
5. ~120 `.md` indexados en pgvector
6. `POST /api/knowledge/search/` < 1.5s end-to-end
7. `POST /api/knowledge/ask/` < 5s (embedding + pgvector + Claude)
8. Multi-turn funcional: Redis con prefijo `kw:`, sliding 20 msgs, TTL 2h
9. `ConversationLog` con retención diferenciada
10. Tests passing, regresión Sprints 1–7 limpia

---

## Lo que desbloquea este sprint

- Canal WhatsApp (Sprint 9): webhook llama `/api/knowledge/ask/` con JWT
- n8n workflows: pueden llamar `/api/knowledge/search/`
- Sprint 9: indexación PDFs MinIO + `document_index` operativos
- Portal B2B: base de usuarios lista

---

Stamp: DRAFT v3.15 — Ronda 15 (curl en Dockerfile mwt-knowledge) — Listo para FROZEN
Origen: v1.0 (spec original) + v2.0 (análisis conflictos) + v3.0 (resoluciones arquitectónicas) — 2026-03-12
