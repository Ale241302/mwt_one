# GUIA_ALE_SPRINT26 — Instrucciones de Ejecución AG-02

**Sprint:** 26 — Notificaciones Email + Cobranza + Admin Templates
**Lote:** LOTE_SM_SPRINT26 v2.3 (auditado R14, 9.1/10)
**Agente:** Alejandro (AG-02)

---

## Orden de ejecución

### Fase 0 — Modelos + precondiciones (Día 1)

1. **S26-02 + S26-02b: Verificar campos existentes**
   ```bash
   python manage.py shell -c "from apps.expedientes.models import ExpedientePago; print([f.name for f in ExpedientePago._meta.get_fields()])"
   python manage.py shell -c "from apps.clientes.models import ClientSubsidiary; print([f.name for f in ClientSubsidiary._meta.get_fields()])"
   ```
   Verificar si existen: `contact_email`, `preferred_language` en ClientSubsidiary. `proforma` FK en ExpedientePago. Si faltan → crear migraciones aditivas.

2. **S26-01: Crear app notifications/**
   ```bash
   python manage.py startapp notifications apps/notifications
   ```
   Modelos: NotificationTemplate, NotificationAttempt, NotificationLog, CollectionEmailLog. Ver LOTE §C1-C3 para definiciones exactas.

   **Clave:** Los 3 modelos de audit trail usan `ImmutableManager` + override `save()`/`delete()`. Ver §C2a enforcement.

3. **S26-03: Data migration 10 templates seed**
   ```bash
   python manage.py makemigrations notifications
   python manage.py migrate
   ```
   Seed con `get_or_create` por `template_key+brand+language`. 10 templates — ver LOTE §G1.

4. **Instalar dependencias**
   ```bash
   pip install Jinja2 --break-system-packages
   # En requirements/base.txt: +Jinja2
   # En requirements/test.txt: +moto[ses]
   ```

### Fase 1 — Backend tasks (Día 2-3)

5. **S26-04: Email backends** — `apps/notifications/backends.py`
   `SendResult` enum (SENT/RETRYABLE/PERMANENT). SMTPBackend + SESBackend. Ver §D1.

6. **S26-05: send_notification task** — `apps/notifications/tasks.py`
   **IMPORTANTE — Leer con cuidado:**
   - Task custom `SendNotificationTask(Task)` con `on_failure()` — ver §E1
   - `autoretry_for=(RetryableEmailError,)` — Celery maneja retries
   - `on_failure()` persiste Log(exhausted) cuando retries se agotan
   - `correlation_id` pasa como kwarg desde el primer enqueue (NO mutar `self.request.kwargs`)
   - Render Jinja2 envuelto en try/except
   - backend.send() envuelto en try/except (catch-all)
   - Advisory lock via `pg_advisory_xact_lock` con sha256 key

   **Nota R14 M1:** En la rama RETRYABLE, antes de lanzar RetryableEmailError, guardar `rendered_subject` y `rendered_body_preview` en el NotificationAttempt para que on_failure tenga contexto. Consultar último attempt por correlation_id en on_failure para rehidratar subject/body en el Log terminal.

   **Nota R14 M2:** Pasar `_correlation_id` y `_recipient` como kwargs reales desde `notify_on_command` (F2), no stashearlos en `self.request.kwargs`.

7. **S26-06: resolve_*_recipient** — `apps/notifications/services.py`
   Dos funciones: `resolve_notification_recipient` + `resolve_collection_recipient`. Ver §E2+E2b.

8. **S26-07: check_overdue_payments** — mismo `tasks.py`
   Cron diario. SendResult branching. Render try/except. Advisory lock. Ver §E3.

9. **S26-08: Celery Beat** — `config/celery.py`
   ```python
   'check-overdue-payments': {
       'task': 'apps.notifications.tasks.check_overdue_payments',
       'schedule': crontab(hour=14, minute=0),
   },
   ```

### Fase 2 — Hook + endpoints (Día 3-4)

10. **S26-09: Hook dispatcher** — modificar `apps/expedientes/services/dispatcher.py`
    Agregar `notify_on_command` a `post_command_hooks`. Pasar `event_log_id`, `command_name`, `proforma_id`. Ver §F2.

11. **S26-10: Templates CRUD** — `apps/notifications/views.py` + `urls.py`
    ViewSet CEO-only. Incluye `/restore/` y `/test-send/`. Ver §H1.

12. **S26-11: Historial endpoints** — mismo views.py
    GET /api/notifications/log/ + /collections/. Filtros + paginación. Ver §H2.

13. **S26-12: Send proforma** — mismo views.py
    POST /api/notifications/send-proforma/. template_key fijo 'proforma.sent'. Dedup 1h. Ver §H3.

### Fase 3 — Frontend (Día 4-5)

14. **S26-13: /notifications/templates** — página admin
15. **S26-14: /notifications/history + /collections** — historial
16. **S26-15: Sidebar** — agregar "Notificaciones" CEO-only, 3 subitems
17. **S26-16: Expediente detail** — sección colapsable "Emails enviados"

### Fase 4 — Integración (Día 5)

18. **S26-17: E2E** — activar MWT_NOTIFICATION_ENABLED=True en .env, verificar flujo completo
19. **S26-18: .env.example** — 6 variables nuevas
20. **S26-19: Regresiones** — `pytest backend/ -v`

---

## Archivos que NO podés tocar

- `apps/expedientes/services/state_machine/` (FROZEN)
- `apps/expedientes/services/pricing/` (S22)
- `apps/commercial/` (S23)
- `docker-compose.yml`

## Verificación final

```bash
pytest backend/tests/test_sprint26.py -v  # 63/63
pytest backend/ -v  # 0 regresiones
```

## Si tenés dudas

- Sobre SendResult/retry: leer §D1 + §E1 del LOTE
- Sobre advisory lock: leer §E1 helper _advisory_lock_for_event
- Sobre tiering/permisos: leer §H4
- Sobre algo no cubierto: preguntale al CEO, no adivines
