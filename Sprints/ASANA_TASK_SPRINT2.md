# Tareas MWT - Sprint 2: Reloj de Crédito + Corrección de Artefactos

A continuación se detalla la lista de tareas a importar en Asana bajo el proyecto **Tareas MWT** (Sección: Sprint 2) derivadas de `LOTE_SM_SPRINT2.md`, `PLB_SPRINT2_PROMPTS.md` y `PLB_SPRINT2_EJECUCION.md`.

**Prerequisito:** Sprint 1 DONE (18 command endpoints POST funcionales, outbox llenándose, credit_clock_started_at persistido en C1/C7).

**Objetivo Sprint 2:** Activar el reloj de crédito automático (el sistema protege al CEO bloqueando expedientes que se acercan a 90 días sin intervención manual) + habilitar corrección de errores en artefactos (C19 SupersedeArtifact, C20 VoidArtifact) sin romper la state machine. Introduce infraestructura async (Redis + Celery) y event dispatcher mínimo.

**Stack nuevo Sprint 2:** Redis 7, Celery Worker, Celery Beat (además de django, postgres, nginx, minio de Sprint 0).

---

## Tareas

### Tarea 1: Sprint 2 - Item 1: Infra — [DONE]
- **Responsable (Agente):** AG-07 DevOps
- **Dependencia:** Sprint 1 DONE.
- **Descripción:** Garantizar que Redis 7, Celery Worker y Celery Beat están funcionales en el stack Docker. Crear `config/celery.py` con app Celery configurada. Configurar `CELERY_BROKER_URL=redis://redis:6379/0` y `CELERY_RESULT_BACKEND=redis://redis:6379/1`. Beat schedule definido ÚNICAMENTE en `app.conf.beat_schedule` dentro de `config/celery.py` (FIX-14 — NO django-celery-beat, NO settings.py). Schedules canónicos: `evaluate_credit_clocks` (crontab hour=6, minute=0) y `process_pending_events` (cada 300s).
- **Archivos permitidos:** docker-compose.yml, config/settings/base.py, requirements.txt, config/celery.py, config/__init__.py.
- **Archivos prohibidos:** apps/*, tests/*.
- **Criterios de Éxito:**
  - Redis 7 contenedor corriendo y healthy (redis-cli ping → PONG).
  - Celery worker corriendo, registrado (`celery -A config inspect ping` → OK).
  - Celery Beat corriendo y aceptando periodic tasks.
  - `config/celery.py` con app Celery configurada y beat_schedule definido.
  - `config/__init__.py` importa celery app.
  - Task de prueba ejecuta y completa correctamente.
  - Los 3 servicios levantan con `docker-compose up` sin errores.
- **Riesgos:** Redis no arranca (puerto 6379 ocupado), Celery worker no se registra (config/celery.py no importado), Beat no encuentra tasks.
- **Branch:** `sprint2/item-1-infra-celery`

---

### Tarea 2: Sprint 2 - Item 2: Reloj de Crédito — [DONE]
- **Responsable (Agente):** AG-02 API Builder
- **Dependencia:** Item 1 aprobado (Celery funcional).
- **Descripción:** Primer proceso automático del sistema. Task Celery `evaluate_credit_clocks()` que corre diariamente (6AM UTC via Beat) y evalúa todos los expedientes activos con credit_clock_started_at. Dos pasos independientes por expediente (FIX-13): Paso 1 — Enforcement de bloqueo (SIEMPRE, sin importar EventLog): si days≥75 AND is_blocked=false → C17 con actor SYSTEM. Paso 2 — Emisión de eventos (una sola vez por vida por umbral): 60d→warning, 75d→critical, 90d→expired. Cada expediente en `transaction.atomic()` con `select_for_update(skip_locked=True)` para protección anti-carreras. Estados ignorados via constante `CREDIT_CLOCK_IGNORED_STATUSES` derivada de enum `is_terminal=True` (FIX-15).
- **Archivos permitidos:** apps/expedientes/tasks.py (crear), apps/expedientes/services.py (extender).
- **Archivos prohibidos:** models.py, views.py, urls.py, serializers.py, tests/.
- **Criterios de Éxito:**
  - Task `evaluate_credit_clocks` registrado como shared_task en Celery Beat.
  - Consulta usa `CREDIT_CLOCK_IGNORED_STATUSES` (derivada de enum, no hardcode).
  - Dos pasos separados: enforcement (siempre) + emisión (una vez por vida).
  - `select_for_update(skip_locked=True)` por expediente.
  - Bloqueo automático día 75: execute_command C17 con user=None, actor_type="SYSTEM", bypass IsCEO.
  - Día 90: emite `credit_clock.expired`, bloquea si no estaba (actor_id="credit_clock_90d").
  - Idempotente emisión: N ejecuciones → sin duplicados.
  - Fallo en C17 → log error + continue (no tumba batch).
  - Locked → log "skipped_due_to_lock" + continue.
  - EventLog.emitted_by="SYSTEM:evaluate_credit_clocks", actor_type/actor_id dentro de payload JSON (sin columnas nuevas).
  - NO envía emails, NO crea dashboard, NO cobra automáticamente.
- **Riesgos:** Task no idempotente (duplica eventos/bloqueos). Celery Beat no lo agenda. Fallo en C17 tumba todo el batch.
- **Branch:** `sprint2/item-2-credit-clock`

---

### Tarea 3: Sprint 2 - Item 3: C19 SupersedeArtifact — [DONE]
- **Responsable (Agente):** AG-02 API Builder
- **Dependencia:** Item 2 aprobado + Item 6 aprobado (campos superseded_by, supersedes existen).
- **Descripción:** Endpoint nuevo para corregir artefactos con error sin romper la state machine. POST /api/expedientes/{pk}/supersede-artifact/ → C19. Input: original_artifact_id, new_payload, reason. CEO only. Precondiciones (§I3): original.status=completed, expediente.status≠CERRADO, mismo artifact_type, new_payload válido. Regla post-transición (§I3.1.3): si artefacto fue precondición de transición ya ejecutada → expediente debe estar bloqueado (is_blocked=true), si no → 409. Regla pre-transición (§I3.1.4): transición no ejecutada → supersede libre. Mutaciones atómicas: UPDATE original→superseded, INSERT nuevo ArtifactInstance (completed, supersedes=original.id), INSERT event_log. Flujo corrección: Block → Supersede → Unblock.
- **Archivos permitidos:** apps/expedientes/services.py, serializers.py, views.py, urls.py.
- **Archivos prohibidos:** models.py, tests/.
- **Criterios de Éxito:**
  - Endpoint funcional: POST /api/expedientes/{pk}/supersede-artifact/.
  - CEO only (IsCEO permission).
  - Falla si expediente CERRADO, si original.status≠completed, si artifact_type diferente.
  - Regla post-transición: 409 si transición ejecutada + no bloqueado.
  - Regla post-transición: OK si transición ejecutada + bloqueado.
  - Regla pre-transición: OK sin bloqueo requerido.
  - Mutaciones atómicas correctas (original→superseded, nuevo→completed, refs cruzadas).
  - Response: `{"expediente": ..., "events": [...]}` HTTP 200.
- **Riesgos:** Regla post-transición mal implementada (mapeo artifact_type → transición → estado actual incorrecta).
- **Branch:** `sprint2/item-3-supersede-artifact`

---

### Tarea 4: Sprint 2 - Item 4: C20 VoidArtifact — [DONE]
- **Responsable (Agente):** AG-02 API Builder
- **Dependencia:** Item 3 aprobado.
- **Descripción:** Endpoint para anular artefactos fiscales sin reemplazo. POST /api/expedientes/{pk}/void-artifact/ → C20. Input: artifact_id, reason. CEO only. Precondiciones (§I5): artifact.status=completed, artifact_type ∈ voidable_list (Sprint 2: solo ART-09). ART-01 a ART-08 NO son voidables (usar C19). Misma regla post-transición que C19. Mutaciones: UPDATE artifact.status→void, INSERT event_log. Efecto cascada: después de void ART-09, C14 (CloseExpediente) ya no puede ejecutarse (precondición ART-09.status=completed no cumplida). CEO debe emitir nueva factura (C13) antes de cerrar. NO implementar conector fiscal.
- **Archivos permitidos:** apps/expedientes/services.py, serializers.py, views.py, urls.py.
- **Archivos prohibidos:** models.py, tests/.
- **Criterios de Éxito:**
  - Endpoint funcional: POST /api/expedientes/{pk}/void-artifact/.
  - CEO only.
  - Falla si artifact_type no voidable (ej: ART-01 → rechazado).
  - Falla si artifact.status ≠ completed.
  - Regla post-transición respetada.
  - Mutaciones atómicas correctas.
  - Después de void ART-09: C14 falla (verificable manualmente).
  - Response: `{"expediente": ..., "events": [...]}` HTTP 200.
  - NO implementa conector fiscal.
- **Branch:** `sprint2/item-4-void-artifact`

---

### Tarea 5: Sprint 2 - Item 5: Event Dispatcher Mínimo — [DONE]
- **Responsable (Agente):** AG-02 API Builder
- **Dependencia:** Item 1 aprobado (Celery funcional).
- **Descripción:** Task Celery `process_pending_events()` que cada 5 minutos marca eventos pendientes como procesados. Consulta: EventLog WHERE processed_at IS NULL, ORDER BY occurred_at ASC, LIMIT 100. Para cada evento: UPDATE processed_at = now(). Sin side effects adicionales en Sprint 2. Propósito: validar pipeline outbox end-to-end y mantener processed_at limpio para Sprint 3+ (consumers reales). Intencionalmente mínimo.
- **Archivos permitidos:** apps/expedientes/tasks.py (extender).
- **Archivos prohibidos:** models.py, views.py, urls.py, serializers.py, services.py, tests/.
- **Criterios de Éxito:**
  - Task registrado en Celery y Beat schedule (cada 5 minutos).
  - Eventos con processed_at=null se marcan con processed_at=now().
  - Eventos ya procesados se ignoran.
  - Idempotente: 2 ejecuciones → mismos resultados.
  - Logging de batch procesado con conteo.
  - NO crea consumers reales, NO usa Redis Streams, NO implementa retry/DLQ.
- **Branch:** `sprint2/item-5-event-dispatcher`

---

### Tarea 6: Sprint 2 - Item 6: Migraciones de Modelo — [DONE]
- **Responsable (Agente):** AG-01 Architect
- **Dependencia:** Ninguna (puede correr al inicio del sprint, en paralelo con Item 1).
- **Descripción:** Verificar si ArtifactInstance tiene los campos necesarios para C19/C20. Si faltan → crear migración puntual. Si existen de Sprint 0 → marcar DONE sin cambios (no-op). Campos a verificar: `superseded_by` (UUIDField nullable FK self — el nuevo que me reemplaza), `supersedes` (UUIDField nullable FK self — el original que reemplazo). Status enum de ArtifactInstance debe incluir valores `superseded` y `void`. Mismo patrón FIX-7 de Sprint 1 (addendum de compatibilidad, no reabre Sprint 0).
- **Archivos permitidos:** apps/expedientes/models.py (solo agregar campos si faltan), apps/expedientes/enums.py (solo agregar valores si faltan).
- **Archivos prohibidos:** views.py, services.py, serializers.py, urls.py, tests/, tasks.py.
- **Criterios de Éxito:**
  - `superseded_by` existe en ArtifactInstance (verificado).
  - `supersedes` existe en ArtifactInstance (verificado).
  - Status enum incluye `void` y `superseded` (verificado).
  - `python manage.py migrate` sin errores.
  - `python manage.py check` sin errores.
  - Campos visibles en Django Admin.
- **Branch:** `sprint2/item-6-migrations`

---

### Tarea 7: Sprint 2 - Item 7: Tests Sprint 2 — [DONE]
- **Responsable (Agente):** AG-06 QA
- **Dependencia:** Items 2-6 aprobados (modelo completo + lógica completa).
- **Descripción:** Tests para todas las features nuevas de Sprint 2 en 3 archivos: test_credit_clock.py (~10 tests), test_corrections.py (~15 tests C19+C20), test_dispatcher.py (~3 tests). Incluye: idempotencia del reloj, concurrencia select_for_update, enforcement vs emisión, regla post-transición de C19/C20, cascada void ART-09→C14 falla, response format, y no-regresión Sprint 1 (happy path completo sigue funcional). Total esperado: ~31 tests.
- **Archivos permitidos:** tests/test_credit_clock.py (crear), tests/test_corrections.py (crear), tests/test_dispatcher.py (crear), tests/conftest.py (extender), tests/factories.py (extender).
- **Archivos prohibidos:** apps/* (no tocar código de producción).
- **Criterios de Éxito:**
  - **Reloj (~10 tests):** 59d→nada, 60d→warning, 75d+no_blocked→bloqueo SYSTEM, 75d+blocked→no duplica, 90d→expired, CERRADO ignorado, CANCELADO ignorado, idempotencia (2 ejecuciones), concurrencia (select_for_update), sin credit_clock→ignorado.
  - **C19 (~9 tests):** Happy path supersede, falla no CEO, falla CERRADO, falla artifact_type diferente, falla status≠completed, post-transición+no bloqueado→409, post-transición+bloqueado→OK, pre-transición→libre, atomicidad (monkeypatch fallo INSERT).
  - **C20 (~6 tests):** Happy path void ART-09, falla no CEO, falla no voidable (ART-01), falla status≠completed, void ART-09→C14 falla, post-transición+no bloqueado→409.
  - **Dispatcher (~3 tests):** processed_at=null→se marca, ya procesados→ignorados, idempotente.
  - **Response format (2 tests):** C19→HTTP 200 con formato, C20→HTTP 200 con formato.
  - **No-regresión (1 test):** Happy path Sprint 1 completo sigue funcional.
  - Todos los tests passing (~31 total).
  - Tests Sprint 1 siguen passing.
- **Branch:** `sprint2/item-7-tests`

---

## Dependencias Sprint 2

```
Sprint 1 DONE
    │
    ├── Item 6: Migraciones modelo (puede correr primero, paralelo a Item 1)
    │
    ├── Item 1: Infra Redis + Celery Worker (AG-07)
    │       │
    │       ├── Item 2: Reloj de Crédito (AG-02) ← ITEM MÁS CRÍTICO
    │       │
    │       └── Item 5: Event Dispatcher Mínimo (AG-02)
    │
    ├── Item 3: C19 SupersedeArtifact (AG-02, después de Item 2 + Item 6)
    │       │
    │       └── Item 4: C20 VoidArtifact (AG-02, después de Item 3)
    │
    └── Item 7: Tests Sprint 2 (AG-06, después de Items 2-6)
```

**Cadena crítica:** Item 1 → Item 2 → Item 3 → Item 4 → Item 7.

---

## Criterio de Cierre Sprint 2

Sprint 2 está **DONE** cuando:
1. Redis + Celery Worker + Beat funcionales.
2. `evaluate_credit_clocks` corre diariamente y aplica reglas 60/75/90.
3. Bloqueo automático día 75 funcional (SYSTEM bloquea, CEO desbloquea).
4. C19 SupersedeArtifact funcional con reglas §I3.1.
5. C20 VoidArtifact funcional para ART-09 (voidable list).
6. Flujo corrección post-transición: Block → Supersede → Unblock OK.
7. Event dispatcher marcando processed_at.
8. Todos los tests passing (~31 de Sprint 2 + tests Sprint 1).
9. 20 command endpoints POST totales (18 Sprint 1 + C19 + C20).
10. ArtifactInstance tiene campos superseded_by, supersedes, status incluye void/superseded.

## Lo que NO debe existir en Sprint 2
- Frontend/UI (Sprint 3)
- Notificaciones email/push (Sprint 3+)
- Consumers reales del event dispatcher (Sprint 3+)
- ART-10, ART-12 (post-MVP)
- Conector fiscal
- Redis Streams event bus
- Dashboard visual
- RBAC formal (MVP = is_superuser)
