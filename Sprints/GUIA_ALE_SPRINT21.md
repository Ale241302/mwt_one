# GUIA_ALE_SPRINT21 — Sprint 21: Monitor de Actividad + Role-Based Sidebar

Ale, este sprint agrega visibilidad de lo que pasa en el sistema. Hasta ahora para saber qué pasó hay que buscar en el EventLog a mano o en el admin. Después de Sprint 21, hay un badge con notificaciones en el header, un panel dropdown con actividad reciente, y el sidebar filtra lo que ve cada rol.

---

## El cambio en una frase

**Antes:** EventLog es una tabla interna que nadie ve salvo en el admin
**Después:** EventLog alimenta un feed de actividad con badge, panel, y lectura/no-lectura por usuario

---

## Qué vas a construir (en orden)

### Fase 0 — Extender modelo (migración)

1. **5 campos nuevos en EventLog** — todos `null=True`:
   - `user` FK → quién ejecutó la acción (NULL = sistema)
   - `proforma` FK → proforma asociada si aplica (limit_choices_to ART-02)
   - `action_source` CharField(32) → qué acción generó el evento (ver contrato abajo)
   - `previous_status` CharField(20) → estado antes de la transición
   - `new_status` CharField(20) → estado después de la transición

2. **Modelo UserNotificationState** — 1 row por usuario:
   - `user` OneToOneField (es el PK)
   - `last_seen_event_id` BigIntegerField (default 0)
   - `updated_at` auto
   - Patrón "high-water mark": todo evento con id > last_seen es "no leído"

### Fase 1 — Endpoints

3. **GET `/api/activity-feed/`** — feed paginado con filtros:
   - Params: `expediente`, `proforma`, `event_type`, `unread_only`, `page`, `page_size`
   - Permisos vía `get_visible_events(user)` (función centralizada, ver abajo)
   - NO expone `payload` del EventLog (datos internos)
   - `user_display` NUNCA muestra email — fallback: nombre → rol → "Usuario" → "Sistema"

4. **GET `/api/activity-feed/count/`** — count para el badge:
   - Retorna `{ unread_count, has_more, last_seen_event_id }`
   - Cap real con `[:100]` slice (no COUNT) — si hay 100+ retorna 99 con has_more=true
   - Misma función de permisos que el feed

5. **POST `/api/activity-feed/mark-seen/`** — marcar como visto:
   - Sin parámetros, sin filtros
   - Avanza `last_seen_event_id` al max(id) del queryset BASE del usuario
   - Retorna `{ previous_last_seen, last_seen_event_id }`

### Fase 2 — Frontend

6. **Badge + panel** — AG-03 lo hace, pero los endpoints tienen que estar listos
7. **Sidebar por roles** — AG-03 activa código existente

### Fase 3 — Tests

8. **24 tests backend** — ver lista en el LOTE

---

## Contrato de action_source (CERRADO)

Valores únicos permitidos — cualquier otro string es un bug:

| Categoría | Valores |
|-----------|---------|
| Commands | `C1`, `C2`, `C3`, `C4`, `C5`, `C6`, `C7`, `C8`, `C9`, `C10`, `C11`, `C12`, `C13`, `C14`, `C15`, `C16`, `C17`, `C18`, `C19`, `C20`, `C21`, `C22` |
| Proforma (S20) | `create_proforma`, `reassign_line`, `change_mode` |
| PATCH | `patch_registro`, `patch_produccion`, `patch_preparacion`, `patch_despacho`, `patch_transito`, `patch_en_destino` |
| Sistema | `system_credit_clock`, `system_cron` |
| NULL | Entries pre-S21 (no backfill) |

---

## Función de permisos — `get_visible_events(user)`

Creá este archivo: `backend/apps/expedientes/services/activity_permissions.py`

Una sola función que determina qué EventLog ve cada usuario. Feed, count y mark-seen la usan — NUNCA duplicar la lógica.

| Rol | Qué ve |
|-----|--------|
| CEO (`role='CEO'` o `is_superuser`) | Todo |
| AGENT_* | Solo expedientes donde ha operado (existe EventLog con user=ese agente) |
| CLIENT_* | Solo expedientes de su client_subsidiary, excluyendo cost.registered, commission.invoiced, compensation.noted |

---

## Dónde actualizar EventLog.objects.create()

Cada lugar que crea EventLog hoy necesita agregar los campos nuevos:

| Lugar | action_source | user | proforma |
|-------|--------------|------|----------|
| `post_command_hooks` (dispatcher) | `command_name` (C1, C5, etc.) | `request.user` | Si result es ART-02 o tiene parent_proforma |
| `create_proforma` (S20) | `'create_proforma'` | `request.user` | La proforma creada |
| `reassign_line` (S20) | `'reassign_line'` | `request.user` | NULL |
| `change_proforma_mode` (S20) | `'change_mode'` | `request.user` | La proforma modificada |
| PATCH views (S18) | `f'patch_{expediente.status.lower()}'` | `request.user` | NULL |
| Celery credit clock (S2) | `'system_credit_clock'` | NULL | NULL |

Para `previous_status`/`new_status`: solo populá si `status_changed=True` en el hook. Si no hay transición → NULL.

---

## Reglas que no podés romper

1. **State machine FROZEN** — no toques handlers de transición. Solo estás agregando campos al EventLog que ya se crea.
2. **Todos los campos null=True** — migración additive-only. Verificá con `sqlmigrate` que solo haya AddField.
3. **Permisos centralizados** — la función `get_visible_events()` es la ÚNICA fuente de verdad de permisos. Los 3 endpoints la llaman.
4. **payload no se serializa** — el feed NO expone el campo payload del EventLog. Datos internos.
5. **Email nunca en user_display** — fallback: full_name → role → "Usuario" → "Sistema".
6. **mark_seen sin filtros** — POST sin parámetros. Avanza al max del queryset base. No acepta expediente_id ni nada.
7. **CEO_ONLY_EVENT_TYPES** — constante frozenset en activity_permissions.py. No duplicar.

---

## Archivos que vas a tocar/crear

| Archivo | Qué hacer |
|---------|-----------|
| `apps/expedientes/models.py` | +5 campos en EventLog, +modelo UserNotificationState |
| `apps/expedientes/services/activity_permissions.py` | CREAR — get_visible_events(), CEO_ONLY_EVENT_TYPES |
| `apps/expedientes/views.py` (o views/activity.py) | +ActivityFeedView, +ActivityFeedCountView, +ActivityFeedMarkSeenView |
| `apps/expedientes/serializers.py` | +EventLogFeedSerializer |
| `apps/expedientes/urls.py` | +3 rutas (feed, count, mark-seen) |
| `apps/expedientes/admin.py` | +UserNotificationState en admin, +filtros en EventLog admin |
| `apps/expedientes/services/dispatcher.py` | Actualizar post_command_hooks con user, proforma, action_source, status |
| Todas las views que crean EventLog | Agregar los 5 campos nuevos |
| `apps/expedientes/tests/test_activity_feed.py` | CREAR — 24 tests |

## Archivos que NO podés tocar

- `apps/expedientes/services/state_machine/` handlers de transición (FROZEN)
- `docker-compose.yml`
- `apps/sizing/` (sprint pasado)
- `apps/expedientes/services/artifact_policy.py` (S20, no modificar)

---

## Verificación antes de hacer PR

```bash
# 1. Migración limpia
python manage.py makemigrations expedientes
python manage.py sqlmigrate expedientes XXXX  # solo AddField ×5 + CreateModel ×1
python manage.py migrate
python manage.py check

# 2. Tests
python manage.py test  # TODO verde, 0 failures

# 3. Grep de sanidad
grep -rn "CEO_ONLY_EVENT_TYPES" backend/  # debe aparecer SOLO en activity_permissions.py
grep -rn "get_visible_events" backend/  # debe aparecer en activity_permissions + 3 views
grep -rn "\.email" backend/apps/expedientes/serializers.py  # 0 en EventLogFeedSerializer

# 4. Verificar que EventLog viejo sigue funcionando
python manage.py shell -c "from apps.expedientes.models import EventLog; EventLog.objects.create(expediente_id=1, event_type='test', payload={})"
# Debe crear sin error (campos nuevos = NULL)
```

---

## Si tenés dudas

- Sobre el contrato de action_source: está cerrado en el LOTE. No inventar valores nuevos.
- Sobre permisos: `get_visible_events()` es la verdad. Si un endpoint hace su propio filtrado, es un bug.
- Sobre el frontend: AG-03 se encarga. Vos solo necesitás los 3 endpoints funcionando.
- Sobre algo no cubierto: preguntale al CEO, no adivines.
