# PROMPT ANTIGRAVITY — Sprint 26: Notificaciones Email + Cobranza

Sos un desarrollador backend senior trabajando en MWT.ONE, una plataforma B2B Django 4.2 + DRF + Next.js 14 + PostgreSQL + Redis + Celery + MinIO.

## TU MISIÓN

Implementar el sistema de notificaciones email del Sprint 26 según LOTE_SM_SPRINT26 v2.3.

## CONTEXTO DEL CODEBASE

- State machine expedientes: FROZEN. No tocar `apps/expedientes/services/state_machine/`.
- ExpedientePago tiene payment_status (S25): pending → verified → credit_released / rejected.
- EventLog extendido (S21): user, proforma, action_source, previous/new status.
- post_command_hooks en dispatcher (S18): array de hooks post-command exitoso.
- Celery + Redis + Celery Beat operativos.
- UUID pk, soft delete, tiered visibility (CEO/AGENT/CLIENT serializers separados).
- action_source contract: C1..C22, verify_payment, reject_payment, release_credit, etc.

## ARQUITECTURA DEL SPRINT

### Modelos (4 + ImmutableManager)

1. **NotificationTemplate** — templates Jinja2 editables CEO. UniqueConstraint condicional (brand null/not null).
2. **NotificationAttempt** — append-only, 1..N por evento. Cada retry crea uno nuevo. Inmutable.
3. **NotificationLog** — resultado final consolidado, 0..1 por evento+recipient. Inmutable.
4. **CollectionEmailLog** — audit trail cobranza. Inmutable.

Los 3 modelos de audit trail usan `ImmutableManager` (bloquea QuerySet.update/delete) + override save()/delete().

### Email Backend

`SendResult` enum: SENT / RETRYABLE / PERMANENT. Los backends NUNCA devuelven bool.

### Task: SendNotificationTask

- Custom Task class con `on_failure()` callback.
- `autoretry_for=(RetryableEmailError,)` — Celery maneja retries automáticamente.
- Cuando retries se agotan → `on_failure()` persiste Log(exhausted).
- Advisory lock via `pg_advisory_xact_lock` con sha256 key determinístico.
- Send FUERA de transaction. Lock+check+log DENTRO.
- Semántica: AT-LEAST-ONCE entrega. Persistencia deduplicada.

### correlation_id

- Event-triggered: `correlation_id = event_log_id`
- Manual/test-send: `correlation_id = uuid4()` generado al inicio
- Pasar como kwarg real desde enqueue, no stashear en self.request.kwargs

### Flujo resumido

1. Kill switch off → Log(disabled) + Attempt(disabled)
2. No template / no recipient → Log(skipped) + Attempt(skipped)
3. Render error → Log(exhausted) + Attempt(failed)
4. Backend exception → Log(exhausted) + Attempt(failed)
5. RETRYABLE → Attempt(failed) + raise RetryableEmailError → Celery retries → on_failure persiste Log(exhausted)
6. PERMANENT → Attempt(failed) + Log(exhausted)
7. SENT → Attempt(sent) + Log(sent)
8. Unknown SendResult → Attempt(failed) + Log(exhausted)

**attempt_count** se calcula por `NotificationAttempt.objects.filter(correlation_id=...).count()` en TODA ruta terminal. Sin excepciones.

## REGLAS DURAS

1. **No tocar** state_machine/, pricing/, commercial/, docker-compose.yml
2. **SendResult enum** — nunca bool para resultado de envío
3. **ImmutableManager** en los 3 modelos de audit trail
4. **SandboxedEnvironment** para Jinja2 — siempre
5. **sha256** para advisory lock keys — nunca hash() de Python
6. **try/except** alrededor de render Y backend.send() — siempre crear audit trail antes de exit
7. **Advisory lock** para dedup de NotificationLog — send afuera, lock+log adentro
8. **63 tests** en test_sprint26.py

## ARCHIVOS A CREAR

```
apps/notifications/__init__.py
apps/notifications/models.py          # C1, C2a, C2b, C3 + ImmutableManager
apps/notifications/admin.py           # read-only para audit trail models
apps/notifications/backends.py        # D1: SendResult + SMTP + SES
apps/notifications/tasks.py           # E1: SendNotificationTask + E3: check_overdue_payments
apps/notifications/services.py        # E2, E2b, G2: resolvers + context builder + template resolver
apps/notifications/mappings.py        # F1: TRIGGER_TO_TEMPLATE
apps/notifications/serializers.py
apps/notifications/views.py           # H1-H3
apps/notifications/urls.py
apps/notifications/permissions.py     # IsCEO import
apps/notifications/migrations/0001_initial.py
apps/notifications/migrations/0002_seed_templates.py  # 10 seeds
backend/tests/test_sprint26.py        # 63 tests
frontend/src/app/[locale]/(mwt)/(dashboard)/notifications/templates/page.tsx
frontend/src/app/[locale]/(mwt)/(dashboard)/notifications/history/page.tsx
frontend/src/app/[locale]/(mwt)/(dashboard)/notifications/collections/page.tsx
frontend/src/components/notifications/  # 4 componentes
```

## ARCHIVOS A MODIFICAR

```
config/settings/base.py     # +INSTALLED_APPS, +6 settings
config/urls.py              # +include notifications
config/celery.py            # +beat_schedule
apps/expedientes/services/dispatcher.py  # +notify_on_command hook
apps/clientes/models.py     # +contact_email si no existe
apps/expedientes/models.py  # +proforma FK en ExpedientePago si no existe
frontend/src/components/layout/Sidebar.tsx  # +Notificaciones CEO
.env.example                # +6 variables
requirements/base.txt       # +Jinja2
requirements/test.txt       # +moto[ses]
```

## VERIFICACIÓN

```bash
python manage.py makemigrations notifications
python manage.py migrate
python manage.py check
pytest backend/tests/test_sprint26.py -v  # 63/63
pytest backend/ -v  # 0 regresiones
bandit -ll backend/  # 0 high/critical
```

## SI TENÉS DUDAS

- Sobre retry/on_failure: leer LOTE §E1 SendNotificationTask
- Sobre advisory lock: leer LOTE §E1 _advisory_lock_for_event
- Sobre cobranza: leer LOTE §E3 check_overdue_payments
- Sobre tiering: leer LOTE §H4
- Sobre algo no cubierto: preguntale al CEO, no adivines
