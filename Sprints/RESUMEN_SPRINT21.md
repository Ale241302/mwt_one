# RESUMEN SPRINT 21 — Monitor de Actividad + Role-Based Sidebar

**Fecha de ejecución:** 01 de abril de 2026  
**Rama:** `main`  
**Estado final:** ✅ Migraciones aplicadas — servidor operativo en producción

---

## Objetivo del Sprint

Implementar observabilidad interna de la plataforma mediante:
1. Extensión del modelo `EventLog` con metadatos de auditoría
2. Mecanismo de estado de lectura por usuario (`UserNotificationState`)
3. Tres endpoints de activity feed con permisos por rol
4. Activación del sidebar filtrado por rol en el frontend
5. Suite de 24 tests automatizados

---

## FASE 0 — Modelos

### S21-01: Extender EventLog

**Archivo modificado:** `backend/apps/expedientes/models.py`

Se agregaron 5 campos nuevos al modelo `EventLog`, todos con `null=True, blank=True`:

| Campo | Tipo | Descripción |
|---|---|---|
| `user` | `ForeignKey(AUTH_USER_MODEL, SET_NULL)` | Usuario que originó el evento |
| `proforma` | `ForeignKey(ArtifactInstance)` | Proforma asociada (solo ART-02) |
| `action_source` | `CharField(max_length=32)` | Código de acción (C1..C22, create_proforma, patch_*, system_*) |
| `previous_status` | `CharField(max_length=20)` | Estado anterior del expediente |
| `new_status` | `CharField(max_length=20)` | Estado nuevo del expediente |

Se agregaron 2 índices en `Meta`:
- `idx_eventlog_exp_id_desc` — sobre `(expediente, -id)`
- `idx_eventlog_pf_id_desc` — sobre `(proforma, -id)`

**Archivos colaterales actualizados** para poblar los nuevos campos al crear `EventLog`:
- `backend/apps/expedientes/services/dispatcher.py` → `user`, `action_source`, `previous_status`, `new_status`
- Views de proformas (Sprint 20) → `action_source='create_proforma'`, `proforma=<instancia>`, `user`
- `reassign_line` view → `action_source='reassign_line'`, `user`
- `change_proforma_mode` view → `action_source='change_mode'`, `proforma`, `user`
- PATCH views (Sprint 18) → `action_source=f'patch_{status.lower()}'`, `user`
- Celery task `credit_clock` → `action_source='system_credit_clock'`, `user=None`

### S21-02: Crear modelo UserNotificationState

**Archivo modificado:** `backend/apps/expedientes/models.py`

Nuevo modelo agregado:

```python
class UserNotificationState(models.Model):
    user = OneToOneField(AUTH_USER_MODEL, primary_key=True, on_delete=CASCADE)
    last_seen_at = DateTimeField(null=True, blank=True)
    updated_at = DateTimeField(auto_now=True)
```

> **Nota:** La migración 0021 renombró el campo original `last_seen_event_id` (BigInteger) a `last_seen_at` (DateTimeField).

**Archivo modificado:** `backend/apps/expedientes/admin.py`
- Se registró `UserNotificationState` con `admin.site.register(UserNotificationState)`

#### Incidencia en migraciones — Bitácora de resolución

Durante la aplicación de migraciones se presentaron 3 errores en cadena que se resolvieron así:

**Error 1 — `DuplicateColumn: action_source`**
- **Causa:** Los campos de `EventLog` ya existían físicamente en la BD pero Django no los tenía registrados en `django_migrations`.
- **Solución:** `python manage.py migrate expedientes 0020 --fake`

**Error 2 — `UndefinedTable: expedientes_usernotificationstate`**
- **Causa:** La tabla `UserNotificationState` fue eliminada manualmente con `DROP TABLE` antes de correr el fake, y la migración 0021 intentó hacer `ALTER TABLE` sobre ella.
- **Solución:** Recrear la tabla manualmente en Postgres con la estructura original de la 0020 y luego correr la migración normalmente:
```sql
CREATE TABLE expedientes_usernotificationstate (
    user_id INTEGER NOT NULL PRIMARY KEY,
    last_seen_event_id BIGINT NOT NULL DEFAULT 0,
    updated_at TIMESTAMPTZ NOT NULL,
    CONSTRAINT fk_notif_user FOREIGN KEY (user_id)
        REFERENCES users_mwtuser(id) ON DELETE CASCADE
);
```
> El usuario real de la BD es `users_mwtuser`, no `users_customuser` — se descubrió consultando `pg_tables`.

**Error 3 — `DuplicateColumn: expediente_id`**
- **Causa:** El campo `expediente_id` ya existía en `expedientes_eventlog` pero la 0022 intentaba crearlo de nuevo.
- **Solución:** `python manage.py migrate expedientes 0022 --fake`

**Error 4 — `UndefinedColumn: previous_status`**  
- **Causa:** Los campos `previous_status` y `new_status` nunca fueron creados físicamente (la 0020 fue fakeada cuando aún no existían).
- **Solución:** `ALTER TABLE` manual en Postgres:
```sql
ALTER TABLE expedientes_eventlog
    ADD COLUMN IF NOT EXISTS previous_status VARCHAR(20),
    ADD COLUMN IF NOT EXISTS new_status      VARCHAR(20),
    ADD COLUMN IF NOT EXISTS action_source   VARCHAR(32),
    ADD COLUMN IF NOT EXISTS user_id         INTEGER REFERENCES users_mwtuser(id) ON DELETE SET NULL;
```
Seguido de `docker-compose restart django` para limpiar el cache del ORM.

**Estado final de migraciones:**
```
[X] 0020_usernotificationstate_eventlog_action_source_and_more
[X] 0021_remove_usernotificationstate_last_seen_event_id_and_more
[X] 0022_eventlog_expediente_alter_eventlog_proforma
```

---

## FASE 1 — Endpoints

### S21-03: Feed + mark-seen

**Archivo CREADO (nuevo):** `backend/apps/expedientes/services/activity_permissions.py`

Contiene:
- `CEO_ONLY_EVENT_TYPES` — frozenset con `'cost.registered'`, `'commission.invoiced'`, `'compensation.noted'`
- `get_visible_events(user, base_qs=None)` — función centralizada de permisos del feed:
  - CEO: ve todos los eventos
  - AGENT_*: solo expedientes donde operó
  - CLIENT_*: solo su subsidiary, excluyendo CEO_ONLY_EVENT_TYPES

**Archivo modificado:** `backend/apps/expedientes/views.py`  
Se agregaron las clases:
- `ActivityFeedView(generics.ListAPIView)` — GET `/api/activity-feed/` con filtros `expediente`, `proforma`, `event_type`, `unread_only`. Paginación 25 por defecto, máx 100.
- `ActivityFeedMarkSeenView(views.APIView)` — POST `/api/activity-feed/mark-seen/`. Avanza `last_seen_at` al momento actual. Retorna `{ previous_last_seen, last_seen_at }`.

**Archivo modificado:** `backend/apps/expedientes/serializers.py`  
Se agregó `EventLogFeedSerializer` con campos:
`id`, `event_type`, `action_source`, `previous_status`, `new_status`, `expediente_id`, `expediente_number`, `proforma_id`, `proforma_number`, `user_id`, `user_display`, `created_at`

- `user_display` con fallback: `full_name → role → 'Usuario' → 'Sistema'`
- **Nunca incluye** `payload` ni `email`

**Archivo modificado:** `backend/apps/expedientes/urls.py`  
Rutas agregadas:
```python
path('activity-feed/', ActivityFeedView.as_view()),
path('activity-feed/count/', ActivityFeedCountView.as_view()),
path('activity-feed/mark-seen/', ActivityFeedMarkSeenView.as_view()),
```

### S21-04: Endpoint count/

**Archivo modificado:** `backend/apps/expedientes/views.py`  
Se agregó `ActivityFeedCountView(views.APIView)` — GET `/api/activity-feed/count/`

Lógica:
1. Obtiene `last_seen_at` del usuario desde `UserNotificationState`
2. Filtra `get_visible_events(user).filter(created_at__gt=last_seen_at)`
3. Usa `qs.order_by('-id').values_list('id', flat=True)[:100]` — slice real, **no** `.count()`
4. Retorna `{ unread_count: min(n, 99), has_more: n == 100, last_seen_at }`

---

## FASE 2 — Frontend

### S21-05: Badge + Panel dropdown

**Archivos CREADOS (nuevos):**

`frontend/src/components/ui/ActivityBadge.tsx`
- Badge numérico rojo en el header
- Muestra "99+" cuando `has_more=true`
- Polling cada 60 segundos, pausado si `document.hidden`
- Al hacer clic abre el `ActivityPanel`

`frontend/src/components/ui/ActivityPanel.tsx`
- Dropdown con últimas 20 actividades
- Formato de ítem: `{user_display} {acción} {expediente_number}`
- Timestamp relativo (ej. "hace 5 min")
- Click en ítem navega a `/dashboard/expedientes/{id}`
- Ítems con `id > lastSeenEventId` previo tienen highlight sutil

`frontend/src/hooks/useActivityFeed.ts`
- Estado: `unreadCount`, `hasMore`, `lastSeenEventId`, `activities`, `isLoading`
- Funciones: `markAsSeen()`, `refresh()`
- Flujo al abrir panel: captura `lastSeenEventId` actual → fetch `/activity-feed/?page_size=20` → POST `/activity-feed/mark-seen/`

**Archivo modificado:** `frontend/src/components/layout/Header.tsx`
- Se agregó `<ActivityBadge />` en la barra del header
- Sin valores hex hardcodeados — usa CSS variables del sistema de diseño existente

### S21-06: Activar sidebar por rol

**Archivo modificado:** `frontend/src/components/layout/Sidebar.tsx`

Se activó (o implementó si no existía) el filtrado de ítems de navegación según el rol del usuario autenticado:

| Rol | Ítems visibles |
|---|---|
| `CEO` | Dashboard, Expedientes, Brands, Clients, Suppliers, Products, Portal, Settings |
| `AGENT_*` | Dashboard, Expedientes, Products |
| `CLIENT_*` | Portal Home, Mis Pedidos, Documentos |

---

## FASE 3 — Tests

**Archivo CREADO (nuevo):** `backend/apps/expedientes/tests/test_activity_feed.py`

24 tests organizados en 6 grupos:

| Grupo | Tests | Cobertura |
|---|---|---|
| EventLog extendido | 6 | Commands populan `user`/`action_source`, proforma FK, Celery con `user=None`, entradas pre-S21 no generan error |
| UserNotificationState | 3 | `get_or_create` primer acceso, `mark-seen` avanza timestamp, segundo `mark-seen` idempotente |
| Feed endpoint | 4 | Sin filtros paginado, filtro por expediente, filtro por proforma, `unread_only` |
| mark-seen | 2 | Response contiene `previous_last_seen` + `last_seen_at` (no campo `marked`), avanza al máximo global no al filtrado |
| Permisos | 5 | CLIENT_* solo sus expedientes, CLIENT_* no ve CEO_ONLY, AGENT_* solo operados, CEO ve todo, 401 sin autenticación |
| Count | 3 | Count correcto, 150 eventos → `unread_count=99` + `has_more=true`, 0 eventos → `unread_count=0` |

---

## Archivos que NO se tocaron

- `apps/expedientes/services/state_machine/` — handlers FROZEN (contrato de Sprint 18)
- `docker-compose.yml`
- `apps/sizing/` — módulo de Sprint 20
- `apps/expedientes/services/artifact_policy.py` — Sprint 20

---

## Resumen de archivos por tipo de cambio

### Creados
| Archivo | Descripción |
|---|---|
| `backend/apps/expedientes/services/activity_permissions.py` | Permisos centralizados del feed |
| `backend/apps/expedientes/tests/test_activity_feed.py` | 24 tests del sprint |
| `frontend/src/components/ui/ActivityBadge.tsx` | Badge de notificaciones en header |
| `frontend/src/components/ui/ActivityPanel.tsx` | Panel dropdown de actividades |
| `frontend/src/hooks/useActivityFeed.ts` | Hook de estado del feed |

### Modificados
| Archivo | Qué cambió |
|---|---|
| `backend/apps/expedientes/models.py` | +5 campos en `EventLog`, nuevo modelo `UserNotificationState` |
| `backend/apps/expedientes/migrations/0020_*.py` | Migración de campos (aplicada con `--fake` por inconsistencia previa) |
| `backend/apps/expedientes/migrations/0021_*.py` | Renombrado `last_seen_event_id` → `last_seen_at` |
| `backend/apps/expedientes/migrations/0022_*.py` | FK `expediente` y `proforma` en `EventLog` (aplicada con `--fake`) |
| `backend/apps/expedientes/serializers.py` | Nuevo `EventLogFeedSerializer` |
| `backend/apps/expedientes/views.py` | 3 nuevas views de activity feed |
| `backend/apps/expedientes/urls.py` | 3 nuevas rutas |
| `backend/apps/expedientes/admin.py` | Registro de `UserNotificationState` |
| `backend/apps/expedientes/services/dispatcher.py` | Poblado de nuevos campos en `EventLog.objects.create()` |
| `frontend/src/components/layout/Header.tsx` | Integración de `<ActivityBadge />` |
| `frontend/src/components/layout/Sidebar.tsx` | Filtrado de navegación por rol |
