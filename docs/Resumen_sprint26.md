# Resumen Sprint 26 — Notificaciones Email + Cobranza + Admin Templates

**Versión LOTE:** LOTE_SM_SPRINT26 v2.3
**Sprint:** 26
**Estado:** DRAFT — Auditado R13 (8.9/10). Pendiente aprobación CEO.
**Fecha:** 2026-04-08
**Depende de:** S21 (EventLog + activity feed), S24 (seguridad B2B), S25 (payment status machine, 59 tests)

---

## Objetivo

Sistema completo de notificaciones email transaccionales: emails automáticos por cambio de estado, cobranza de pagos vencidos con cron Celery Beat, templates Jinja2 editables por CEO, envío de proformas por email (Flujo C), y frontend admin para gestión de templates + historial de envíos.

---

## Fase 0 — Precondiciones y modelos

### S26-01 · Crear app `notifications/` con los 4 modelos

**Objetivo:** Definir todos los modelos del sistema de notificaciones con sus constraints, managers inmutables y audit trail.

| Archivo | Acción | Qué contiene |
|---------|--------|-------------|
| `apps/notifications/__init__.py` | **CREAR** | Registro de app Django |
| `apps/notifications/models.py` | **CREAR** | Modelos C1–C3 + `ImmutableManager` |
| `apps/notifications/migrations/0001_initial.py` | **CREAR** | Migración inicial de los 4 modelos |

**Modelos implementados en `models.py`:**

- **`NotificationTemplate`** — Templates Jinja2 editables por CEO. Campos: `id` (UUID), `name`, `template_key`, `subject_template`, `body_template`, `is_active`, `brand` (FK nullable), `language`, `created_at`, `updated_at`, `created_by`. Dos `UniqueConstraint` condicionales: una para `brand=null` (`uniq_default_template_per_key_lang`) y otra para `brand!=null` (`uniq_brand_template_per_key_lang`). Soft delete via `is_active=False`.

- **`NotificationAttempt`** — Registro append-only de cada intento de envío (1..N por evento). Campos: `id` (UUID), `correlation_id`, `event_log` (FK nullable), `expediente` (FK), `proforma` (FK nullable), `recipient_email`, `template_key`, `trigger_action_source`, `status` (`sent/failed/skipped/disabled`), `error`, `attempted_at`. Enforcement: `delete()` raises `PermissionError`, `save()` bloquea updates en registros existentes.

- **`NotificationLog`** — Registro final consolidado (0..1 por evento+recipient). Campos: `id` (UUID), `correlation_id`, `template` (FK), `event_log` (FK nullable), `expediente` (FK), `proforma` (FK nullable), `recipient_email`, `subject`, `body_preview` (max 500), `created_at`, `completed_at`, `status` (`sent/skipped/disabled/exhausted`), `error`, `trigger_action_source`, `template_key`, `attempt_count`. `UniqueConstraint` en `(event_log, recipient_email)` cuando `event_log!=null`. Enforcement: inmutable via `delete()`/`save()`.

- **`CollectionEmailLog`** — Audit trail cobranza automática. Campos: `id` (UUID), `expediente` (FK), `proforma` (FK nullable), `pago` (FK), `created_at`, `grace_days_used`, `amount_overdue`, `recipient_email`, `status` (`sent/failed`), `completed_at`, `error`. Enforcement: inmutable.

- **`ImmutableManager` + `ImmutableQuerySet`** — Bloquea `QuerySet.update()` y `QuerySet.delete()` en los 3 modelos de audit trail (`NotificationAttempt`, `NotificationLog`, `CollectionEmailLog`). Raises `PermissionError` en bulk operations.

---

### S26-02 · Verificar `contact_email` + `preferred_language` en `ClientSubsidiary`

**Objetivo:** Confirmar que los campos necesarios existen en el modelo. Si no existen, crearlos con migración aditiva.

| Archivo | Acción | Qué contiene |
|---------|--------|-------------|
| `apps/clientes/models.py` | **MODIFICAR** (si falta) | Agregar `contact_email = EmailField(null=True, blank=True)` |
| `apps/clientes/migrations/XXXX_add_contact_email.py` | **CREAR** (si falta) | Migración aditiva nullable para `contact_email` |

**Regla:** Si `contact_email` es null → skip notificación + log warning. `preferred_language` → si no existe usar default `'es'`.

---

### S26-02b · Verificar FK `proforma` en `ExpedientePago`

**Objetivo:** Verificar si `ExpedientePago` ya tiene FK a `ArtifactInstance`. Si no, crear migración aditiva nullable.

| Archivo | Acción | Qué contiene |
|---------|--------|-------------|
| `apps/expedientes/models.py` | **MODIFICAR** (si falta) | Agregar `proforma = ForeignKey('expedientes.ArtifactInstance', null=True, blank=True, on_delete=SET_NULL, related_name='payments', limit_choices_to={'artifact_type': 'ART-02'})` |
| `apps/expedientes/migrations/XXXX_add_proforma_fk_expedientepago.py` | **CREAR** (si falta) | Migración aditiva nullable |

**Alternativa:** Si el FK no se puede agregar, `resolve_collection_recipient` usa Mode B por defecto para pagos sin proforma. Documentar decisión en PR.

---

### S26-03 · Data migration: 10 templates seed

**Objetivo:** Poblar la base de datos con 10 templates de notificación usando `get_or_create` idempotente.

| Archivo | Acción | Qué contiene |
|---------|--------|-------------|
| `apps/notifications/migrations/0002_seed_templates.py` | **CREAR** | Data migration con 10 seeds via `get_or_create` por `(template_key, brand=null, language='es')` |

**Templates seed (10 total):**

| template_key | Descripción |
|---|---|
| `expediente.registered` | C1 — Registro de expediente |
| `expediente.production` | Inicio de producción |
| `expediente.dispatched` | Despacho |
| `expediente.delivered` | Entrega |
| `payment.verified` | Pago verificado |
| `payment.rejected` | Pago rechazado |
| `payment.credit_released` | Crédito liberado |
| `payment.overdue` | Pago vencido (cobranza) |
| `proforma.sent` | Envío de proforma (Flujo C) |
| `expediente.cancelled` | Expediente cancelado |

---

## Fase 1 — Email backend + tasks (backend)

### S26-04 · Email backends + dependencias

**Objetivo:** Implementar la capa de abstracción de envío de emails con `SendResult` enum y dos backends concretos (SMTP + SES).

| Archivo | Acción | Qué contiene |
|---------|--------|-------------|
| `apps/notifications/backends.py` | **CREAR** | `SendResult` enum (SENT/RETRYABLE/PERMANENT), clase abstracta `EmailBackend`, `SMTPBackend`, `SESBackend`, función `get_email_backend()` |
| `requirements/base.txt` | **MODIFICAR** | Agregar `Jinja2` si no está |
| `requirements/test.txt` | **MODIFICAR** | Agregar `moto[ses]` si no está |

**Contrato `SendResult`:**
- `SENT` — proveedor aceptó el email
- `RETRYABLE` — fallo transitorio → Celery reintenta
- `PERMANENT` — dirección inválida/bloqueada → no reintentar

**`SMTPBackend.send()`:** Captura `SMTPRecipientsRefused` → PERMANENT; `SMTPException/ConnectionError/TimeoutError` → RETRYABLE.

**`SESBackend.send()`:** Captura `MessageRejected` → PERMANENT; `ClientError/ConnectionError` → RETRYABLE.

---

### S26-05 · `send_notification` task

**Objetivo:** Implementar la task Celery principal con flujo two-model (Attempt + Log), advisory lock, SendResult branching y on_failure callback.

| Archivo | Acción | Qué contiene |
|---------|--------|-------------|
| `apps/notifications/tasks.py` | **CREAR** | `SendNotificationTask` (custom Task class), `send_notification` shared_task, `check_overdue_payments` shared_task, helpers `_persist_terminal`, `_create_terminal`, `_stable_lock_key`, `_advisory_lock_for_event` |

**Flujo `send_notification`:**

1. **Kill switch off** → `NotificationAttempt(disabled)` + `NotificationLog(disabled)` → return
2. **Dedup check** (event-triggered) → si ya existe Log terminal → return
3. **No template** → `Attempt(skipped)` + `Log(skipped)` → return
4. **No recipient** → `Attempt(skipped)` + `Log(skipped)` → return
5. **Render error** (try/except Jinja2) → `Attempt(failed)` + `Log(exhausted)` → return
6. **Backend exception** (try/except catch-all) → `Attempt(failed)` + `Log(exhausted)` → return
7. **RETRYABLE** → `Attempt(failed)` + raise `RetryableEmailError` → Celery retries → `on_failure()` persiste `Log(exhausted)`
8. **PERMANENT** → `Attempt(failed)` + `Log(exhausted)` → return
9. **SENT** → `Attempt(sent)` + `Log(sent)` → return
10. **Unknown SendResult** → `Attempt(failed)` + `Log(exhausted)` (no RuntimeError)

**Advisory lock:** `pg_advisory_xact_lock` con key `sha256(f"notif:{event_log_id}:{recipient_email}")`. Lock+check+log DENTRO de `transaction.atomic()`. Send FUERA.

**`on_failure()`:** Callback del Task custom. Persiste `Log(exhausted)` cuando retries se agotan. Calcula `attempt_count` por `correlation_id`.

**`correlation_id`:** `event_log_id` si event-triggered; `uuid4()` si manual/test-send.

---

### S26-06 · `resolve_notification_recipient` + `resolve_collection_recipient`

**Objetivo:** Dos funciones de resolución de destinatario según el modo de operación (B = cliente, C = CEO/MWT).

| Archivo | Acción | Qué contiene |
|---------|--------|-------------|
| `apps/notifications/services.py` | **CREAR** | `resolve_notification_recipient(expediente, proforma_id)`, `resolve_collection_recipient(pago)`, `build_notification_context(expediente, proforma_id, extra_context)`, `resolve_template(template_key, brand, language)` |

**`resolve_notification_recipient`:**
- Mode C (`operado_por=MWT`) → `settings.CEO_EMAIL`
- Mode B (cliente) → `expediente.client_subsidiary.contact_email`

**`resolve_collection_recipient`:**
- Resuelve por `pago.proforma` (FK del pago, no del expediente global)
- Si pago sin proforma FK → Mode B por defecto

**`resolve_template(template_key, brand, language)`:**
1. Busca `(key, brand, lang)` → activo
2. Fallback `(key, brand=null, lang)` → activo
3. Fallback `(key, brand=null, 'es')` → activo
4. None si no encuentra (log error, no crash)

---

### S26-07 · `check_overdue_payments` task

**Objetivo:** Cron diario que detecta pagos vencidos y envía emails de cobranza con dedup de 7 días.

| Archivo | Acción | Qué contiene |
|---------|--------|-------------|
| `apps/notifications/tasks.py` | **CREAR** (incluido en S26-05) | `check_overdue_payments` shared_task |

**Flujo:**
1. Kill switch → `logger.info` → return (NO crea `CollectionEmailLog`)
2. Query `ExpedientePago` con `status in ['pending','verified']` + `is_active=True`
3. `refresh_from_db(fields=['status','is_active'])` por pago antes de procesar
4. Calcular `due_date = pago.fecha + timedelta(days=grace_days)` (default 30 si null)
5. Si `today <= due_date` → skip
6. Dedup 7 días por `completed_at` → skip si ya se envió
7. `resolve_collection_recipient(pago)` → recipient + proforma
8. Render Jinja2 con try/except → `CollectionEmailLog(failed)` si error
9. `backend.send()` con try/except → SendResult branching:
   - SENT → `CollectionEmailLog(sent, completed_at=now())`
   - RETRYABLE/PERMANENT/Unknown → `CollectionEmailLog(failed)` (cron diario reintentará)
10. Advisory lock en `CollectionEmailLog` creation (key: `sha256(f"collection:{pago.pk}:{recipient}")`)

---

### S26-08 · Celery Beat config

**Objetivo:** Registrar el schedule diario de cobranza en Celery Beat.

| Archivo | Acción | Qué contiene |
|---------|--------|-------------|
| `config/celery.py` | **MODIFICAR** | Agregar entrada `'check-overdue-payments'` en `beat_schedule`: `crontab(hour=14, minute=0)` (8:00 AM Costa Rica / UTC-6) |

---

## Fase 2 — Hook dispatcher + endpoints (backend)

### S26-09 · Hook en dispatcher

**Objetivo:** Conectar el dispatcher de comandos con el sistema de notificaciones via `post_command_hooks`.

| Archivo | Acción | Qué contiene |
|---------|--------|-------------|
| `apps/notifications/mappings.py` | **CREAR** | Dict `TRIGGER_TO_TEMPLATE`: mapeo `action_source` → `template_key` para cada comando del dispatcher |
| `apps/expedientes/services/dispatcher.py` | **MODIFICAR** | Agregar función `notify_on_command` en el array `post_command_hooks`. Pasa `event_log_id` al enqueue de `send_notification.delay()`. Si hook falla → comando no falla (aislado en try/except) |

**`TRIGGER_TO_TEMPLATE` (mappings.py):**

| action_source | template_key |
|---|---|
| `C1` | `expediente.registered` |
| `verify_payment` | `payment.verified` |
| `reject_payment` | `payment.rejected` |
| `release_credit` | `payment.credit_released` |
| `C14` (despacho) | `expediente.dispatched` |
| `C15` (entrega) | `expediente.delivered` |
| Otros / no mapeados | No llama send_notification |

---

### S26-10 · Templates CRUD + restore

**Objetivo:** ViewSet CEO-only para CRUD de templates con soporte de test-send, soft delete y restore.

| Archivo | Acción | Qué contiene |
|---------|--------|-------------|
| `apps/notifications/views.py` | **CREAR** | `NotificationTemplateViewSet` (CRUD), `NotificationLogViewSet`, `CollectionEmailLogViewSet`, endpoint `/send-proforma/` |
| `apps/notifications/serializers.py` | **CREAR** | `NotificationTemplateSerializer`, `NotificationLogSerializer`, `CollectionEmailLogSerializer` |
| `apps/notifications/urls.py` | **CREAR** | Router con los 3 ViewSets + rutas `/templates/{id}/restore/` y `/templates/{id}/test-send/` |
| `apps/notifications/permissions.py` | **CREAR** | Import de `IsCEO` desde `apps.users.permissions` (o donde esté definido en el proyecto) |
| `config/urls.py` | **MODIFICAR** | Agregar `include('apps.notifications.urls')` en el router principal |

**Comportamiento ViewSet:**
- `DELETE` → soft delete: `is_active=False` (no elimina registro)
- `POST /restore/` → `is_active=True` (reactivar template)
- `POST /test-send/` → requiere `sample_expediente_id` en body → 400 si ausente → envía email real + crea `NotificationLog`
- Lista incluye templates inactivos (grayed en frontend)
- Solo CEO puede crear/editar/eliminar. Agent/Client → 403

---

### S26-11 · Historial endpoints

**Objetivo:** Endpoints de lectura para historial de notificaciones y cobranzas con filtros y paginación.

| Archivo | Acción | Qué contiene |
|---------|--------|-------------|
| `apps/notifications/views.py` | **CREAR** (incluido en S26-10) | `NotificationLogViewSet` (list, retrieve), `CollectionEmailLogViewSet` (list, retrieve) |
| `apps/notifications/serializers.py` | **CREAR** (incluido en S26-10) | Serializers de Log y CollectionLog |

**Filtros disponibles:** `?expediente=<id>`, `?status=<sent|skipped|disabled|exhausted|failed>`, `?template_key=`, `?recipient_email=`
**Paginación:** cursor-based o page-based según configuración global del proyecto.

---

### S26-12 · Send proforma endpoint

**Objetivo:** Endpoint manual para enviar proforma por email con deduplicación de 1 hora.

| Archivo | Acción | Qué contiene |
|---------|--------|-------------|
| `apps/notifications/views.py` | **CREAR** (incluido en S26-10) | `POST /send-proforma/` con validación `proforma_id` + dedup 1h via `NotificationLog` |

**Dedup 1h:** Si existe `NotificationLog` con `template_key='proforma.sent'` + mismo `proforma` + `completed_at >= now()-1h` → 409 Conflict.
**Recipient:** `resolve_notification_recipient(expediente, proforma_id)` → sin campo `override_used`.

---

## Fase 3 — Frontend (AG-03)

### S26-13 · Página `/notifications/templates`

**Objetivo:** UI para gestión de templates de notificación (CEO-only).

| Archivo | Acción | Qué contiene |
|---------|--------|-------------|
| `frontend/src/app/[locale]/(mwt)/(dashboard)/notifications/templates/page.tsx` | **CREAR** | Página principal de templates con `TemplatesTable` y modal `TemplateEditor` |
| `frontend/src/components/notifications/TemplatesTable.tsx` | **CREAR** | Tabla de templates con columnas: nombre, key, idioma, brand, estado (activo/inactivo). Acciones: editar, toggle, eliminar/restore, test-send |
| `frontend/src/components/notifications/TemplateEditor.tsx` | **CREAR** | Modal/drawer con campos: `name`, `template_key`, `language`, `brand`, `subject_template` (textarea), `body_template` (textarea), toggle `is_active`. Validación antes de guardar |

**Features:**
- Toggle activo/inactivo inline en tabla
- Test-send requiere selector de expediente (búsqueda/autocomplete)
- Templates inactivos visibles en gris

---

### S26-14 · Páginas historial y cobranzas

**Objetivo:** UI de solo lectura para historial de envíos y logs de cobranza.

| Archivo | Acción | Qué contiene |
|---------|--------|-------------|
| `frontend/src/app/[locale]/(mwt)/(dashboard)/notifications/history/page.tsx` | **CREAR** | Página de `NotificationLog` con filtros (expediente, status, template_key), paginación y status badges |
| `frontend/src/app/[locale]/(mwt)/(dashboard)/notifications/collections/page.tsx` | **CREAR** | Página de `CollectionEmailLog` con filtros (expediente, status), paginación y columnas: amount_overdue, grace_days_used, recipient, status, completed_at |
| `frontend/src/components/notifications/NotificationStatusBadge.tsx` | **CREAR** | Componente badge reutilizable para status: `sent` (verde), `skipped` (gris), `disabled` (amarillo), `exhausted` (rojo), `failed` (rojo) |

---

### S26-15 · Sidebar "Notificaciones"

**Objetivo:** Agregar sección Notificaciones al sidebar lateral, visible solo para CEO.

| Archivo | Acción | Qué contiene |
|---------|--------|-------------|
| `frontend/src/components/layout/Sidebar.tsx` | **MODIFICAR** | Agregar ítem "Notificaciones" con 3 subitems CEO-only: Templates (`/notifications/templates`), Historial (`/notifications/history`), Cobranzas (`/notifications/collections`) |

---

### S26-16 · Expediente detail — "Emails enviados"

**Objetivo:** Sección colapsable en el detalle de expediente mostrando los últimos 10 logs de notificación.

| Archivo | Acción | Qué contiene |
|---------|--------|-------------|
| `frontend/src/components/notifications/ExpedienteEmailsSection.tsx` | **CREAR** | Componente colapsable "Emails enviados": lista los últimos 10 `NotificationLog` del expediente. Read-only. Columnas: fecha, template_key, recipient, status, subject preview |

*(Integrar en la página de detalle de expediente existente)*

---

## Fase 4 — Integración + verificación

### S26-17 · Flujo E2E completo

**Objetivo:** Verificar el flujo completo de extremo a extremo: activar sistema → disparar comando → email enviado → log en historial → deduplicación verificada.

| Archivo | Acción | Qué contiene |
|---------|--------|-------------|
| `backend/tests/test_sprint26.py` | **CREAR** | 63 tests cubriendo todos los escenarios |

**Cobertura de tests (63 total):**

- **Modelos (8 tests):** UniqueConstraint templates (default + brand), UniqueConstraint Log (event+recipient), `NotificationAttempt` append-only (delete raises, save raises, bulk update raises), `NotificationLog` inmutable, `CollectionEmailLog` inmutable
- **Backends (6 tests):** SMTP mock sent/permanent/retryable, SES mock con moto (sent/permanent/retryable), Sandbox bloquea `__import__`
- **send_notification (14 tests):** sent → Attempt(sent)+Log(sent), no recipient → Attempt(skipped)+Log(skipped), RETRYABLE → Attempt(failed)+retry+no Log aún, exhausted → Log(exhausted)+attempt_count, PERMANENT → Attempt(failed)+Log(exhausted), kill switch → Log(disabled), dedup (Log exists → skip), sha256 key determinístico, render error → Attempt(failed)+Log(exhausted), backend exception → audit trail, unknown SendResult → audit trail, correlation_id consistente, manual flow (event_log=None)
- **Resolvers (6 tests):** Mode C → CEO, Mode B → contact_email, null → None, cobranza con proforma, cobranza sin proforma → Mode B, preferred_language fallback
- **check_overdue_payments (10 tests):** overdue → sent+completed_at, within grace → skip, dedup 7d por completed_at, status changed → skip, kill switch → no log, lock key determinístico, render error → CollectionEmailLog(failed), RETRYABLE → CollectionEmailLog(failed), select_related proforma no falla, refresh_from_db
- **Beat schedule (1 test):** task en beat_schedule con crontab correcto
- **Dispatcher hook (4 tests):** C1 → delay llamado con event_log_id, hook falla → command safe, comando no mapeado → no call, args correctos
- **Templates CRUD (8 tests):** crear, leer, actualizar, DELETE→is_active=False, restore→is_active=True, CLIENT→403, test-send sin expediente→400, test-send→email+log
- **Historial (4 tests):** filtro expediente, filtro status, paginación, serializer campos
- **Send proforma (5 tests):** default recipient, override, 404 proforma, dedup 1h→409, crea Log correcto
- **Seeds (2 tests):** 10 templates post-migrate, idempotente (2x→10)

---

### S26-18 · Variables de entorno

**Objetivo:** Documentar las 6 nuevas variables de entorno del sprint.

| Archivo | Acción | Qué contiene |
|---------|--------|-------------|
| `.env.example` | **MODIFICAR** | Agregar 6 variables nuevas |
| `config/settings/base.py` | **MODIFICAR** | Agregar 6 settings + `notifications` en `INSTALLED_APPS` |

**Variables nuevas:**

```env
MWT_EMAIL_BACKEND=apps.notifications.backends.SMTPBackend
DEFAULT_FROM_EMAIL=notificaciones@mwt.one
MWT_NOTIFICATION_ENABLED=False
CEO_EMAIL=ceo@mwt.one
PORTAL_BASE_URL=https://portal.mwt.one
AWS_SES_REGION=us-east-1
```

**`config/settings/base.py`:** Agregar `'apps.notifications'` en `INSTALLED_APPS`. Definir los 6 settings con `env()` y defaults.

---

### S26-19 · 0 regresiones

**Objetivo:** Garantizar que los 59 tests del S25 y todos los tests previos siguen pasando.

```bash
# Comandos de verificación
python manage.py makemigrations notifications
python manage.py migrate
python manage.py check
pytest backend/tests/test_sprint26.py -v  # 63/63
pytest backend/ -v                         # 0 regresiones
bandit -ll backend/                        # 0 high/critical
```

---

## Resumen de archivos por fase

### Archivos CREADOS (22)

| Archivo | Fase | Item |
|---------|------|------|
| `apps/notifications/__init__.py` | 0 | S26-01 |
| `apps/notifications/models.py` | 0 | S26-01 |
| `apps/notifications/admin.py` | 0 | S26-01 |
| `apps/notifications/migrations/0001_initial.py` | 0 | S26-01 |
| `apps/notifications/migrations/0002_seed_templates.py` | 0 | S26-03 |
| `apps/notifications/backends.py` | 1 | S26-04 |
| `apps/notifications/tasks.py` | 1 | S26-05 / S26-07 |
| `apps/notifications/services.py` | 1 | S26-06 |
| `apps/notifications/mappings.py` | 2 | S26-09 |
| `apps/notifications/serializers.py` | 2 | S26-10 |
| `apps/notifications/views.py` | 2 | S26-10 / S26-11 / S26-12 |
| `apps/notifications/urls.py` | 2 | S26-10 |
| `apps/notifications/permissions.py` | 2 | S26-10 |
| `backend/tests/test_sprint26.py` | 4 | S26-17 |
| `frontend/src/app/[locale]/(mwt)/(dashboard)/notifications/templates/page.tsx` | 3 | S26-13 |
| `frontend/src/app/[locale]/(mwt)/(dashboard)/notifications/history/page.tsx` | 3 | S26-14 |
| `frontend/src/app/[locale]/(mwt)/(dashboard)/notifications/collections/page.tsx` | 3 | S26-14 |
| `frontend/src/components/notifications/TemplatesTable.tsx` | 3 | S26-13 |
| `frontend/src/components/notifications/TemplateEditor.tsx` | 3 | S26-13 |
| `frontend/src/components/notifications/NotificationStatusBadge.tsx` | 3 | S26-14 |
| `frontend/src/components/notifications/ExpedienteEmailsSection.tsx` | 3 | S26-16 |

### Archivos MODIFICADOS (10)

| Archivo | Fase | Item | Qué se agrega |
|---------|------|------|---------------|
| `apps/clientes/models.py` | 0 | S26-02 | `contact_email` (si no existe) |
| `apps/expedientes/models.py` | 0 | S26-02b | FK `proforma` en `ExpedientePago` (si no existe) |
| `apps/notifications/admin.py` | 0 | S26-01 | Registrar modelos como read-only |
| `config/settings/base.py` | 1/4 | S26-04/S26-18 | `'apps.notifications'` en INSTALLED_APPS + 6 settings |
| `config/urls.py` | 2 | S26-10 | `include('apps.notifications.urls')` |
| `config/celery.py` | 1 | S26-08 | Beat schedule `check-overdue-payments` a las 14:00 UTC |
| `apps/expedientes/services/dispatcher.py` | 2 | S26-09 | Hook `notify_on_command` en `post_command_hooks` |
| `frontend/src/components/layout/Sidebar.tsx` | 3 | S26-15 | Sección "Notificaciones" con 3 subitems CEO-only |
| `.env.example` | 4 | S26-18 | 6 variables nuevas |
| `requirements/base.txt` | 1 | S26-04 | `Jinja2` |
| `requirements/test.txt` | 1 | S26-04 | `moto[ses]` |

---

## Decisiones CEO pendientes (bloqueantes)

| ID | Decisión requerida | Default asumido |
|----|--------------------|-----------------|
| DEC-S26-01 | Email provider: SMTP / SendGrid / Amazon SES | **Bloqueante — no ejecutar sin decisión** |
| DEC-S26-02 | `contact_email` obligatorio o nullable en `ClientSubsidiary` | Nullable — skip si null |
| DEC-S26-03 | Qué transiciones disparan email al cliente | C1, producción, despacho, entrega, pago verified/rejected/released, overdue |
| DEC-S26-04 | Gracia cobranza: `payment_grace_days` por cliente o global | `payment_grace_days` de `ClientSubsidiary`; default 30 si null |
| DEC-S26-05 | Cobranza Mode C: email a CEO o al cliente | CEO si Mode C; cliente si Mode B |

---

## Reglas duras (no negociables)

1. **No tocar** `state_machine/`, `pricing/`, `commercial/`, `docker-compose.yml`
2. `SendResult` enum — nunca `bool` para resultado de envío
3. `ImmutableManager` en los 3 modelos de audit trail
4. `SandboxedEnvironment` para Jinja2 — siempre
5. `sha256` para advisory lock keys — nunca `hash()` de Python
6. `try/except` alrededor de render Y `backend.send()` — siempre crear audit trail antes de exit
7. Advisory lock para dedup de `NotificationLog` — send afuera, lock+log adentro
8. **63 tests** en `test_sprint26.py` — todos deben pasar

---

*Resumen generado desde LOTE_SM_SPRINT26 v2.3 — 2026-04-09*
