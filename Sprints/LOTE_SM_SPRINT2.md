# LOTE_SM_SPRINT2 — Reloj de Crédito + Corrección de Artefactos
status: FROZEN — Aprobado CEO 2026-02-27
visibility: [INTERNAL]
domain: Plataforma (IDX_PLATAFORMA)
version: 3.5
tipo: Lote ruteado (ref → PLB_ORCHESTRATOR §E)
sprint: 2
priority: P0
depends_on: LOTE_SM_SPRINT1 (todos los items aprobados)
refs: ENT_OPS_STATE_MACHINE v1.2.2 (FROZEN), PLB_ORCHESTRATOR v1.2.2 (FROZEN)

---

## Scope Sprint 2

**Objetivo:** Activar el reloj de crédito automático (el sistema protege al CEO sin que tenga que revisar manualmente cada expediente) + habilitar corrección de errores en artefactos (operación real genera errores, hay que poder corregirlos sin romper la state machine).

**Precondición:** Sprint 1 DONE — 18 command endpoints POST funcionales, outbox llenándose, credit_clock_started_at persistido en C1/C7.

### Incluido en Sprint 2

| # | Feature | Fuente | Prioridad |
|---|---------|--------|-----------|
| 1 | Reloj de crédito automático (evaluar día 60/75/90) | §D2, §M2 | P0 — razón de ser del sprint |
| 2 | Celery + Redis en Docker (infra para tasks async) | Prerequisito de #1 | P0 — sin esto no hay reloj |
| 3 | C19 SupersedeArtifact (corregir artefactos) | §I3 | P1 — operación real lo necesita |
| 4 | C20 VoidArtifact (anular artefactos fiscales) | §I5 | P1 — complemento de C19 |
| 5 | Event dispatcher mínimo (outbox → procesado) | §K processed_at | P2 — marca eventos como procesados |
| 6 | Tests Sprint 2 | — | P0 — obligatorio |

### Excluido de Sprint 2

| Feature | Razón | Cuándo |
|---------|-------|--------|
| Frontend / UI | Backend-first. CEO opera via API + Admin | Sprint 3 |
| Notificaciones email/push | Necesita n8n o SMTP config. Manual por ahora | Sprint 3+ |
| Redis Streams event bus | Overhead. Celery directo es suficiente para MVP | Post-MVP |
| Conector fiscal (void ART-09 → nota crédito) | C20 registra el void; consecuencia fiscal es manual | Post-MVP |
| ART-10 Factura comisión | Solo mode=COMISION, post-MVP | Sprint 4+ |
| ART-12 Nota compensación | CEO-ONLY, post-MVP | Sprint 4+ |
| Multi-consumer event processing | 1 solo consumer (reloj) es suficiente | Post-MVP |

---

## Decisión de infraestructura: Redis + Celery (FIX-2 normalizado)

Sprint 2 Item 1 garantiza que al cerrar este item existen y funcionan: redis, celery-worker, celery-beat. Sin condicionales. El estado previo del repo es irrelevante — Item 1 deja los 3 servicios funcionales.

Stack después de Sprint 2:
- django, postgres, nginx, minio (Sprint 0)
- redis, celery-worker, celery-beat (garantizados por Sprint 2 Item 1)

---

## Items

### Item 1: Infra — Redis + Celery Worker
- **Agente:** AG-07 DevOps
- **Dependencia previa:** Sprint 1 DONE
- **Archivos a tocar:** docker-compose.yml, config/settings/base.py (CELERY_BROKER_URL, CELERY_RESULT_BACKEND), requirements.txt (celery, redis), config/celery.py (si no existe)
- **Archivos prohibidos:** apps/*, tests/*
- **Criterio de done:**
  - [ ] Redis 7 contenedor corriendo y accesible desde Django
  - [ ] Celery worker contenedor corriendo, registrado, processing tasks
  - [ ] Celery Beat contenedor corriendo y aceptando periodic tasks
  - [ ] `config/celery.py` con app Celery configurada
  - [ ] `config/__init__.py` importa celery app
  - [ ] Health check: `celery -A config inspect ping` responde OK
  - [ ] Task de prueba ejecuta y completa correctamente
  - [ ] `CELERY_BROKER_URL` y `CELERY_RESULT_BACKEND` apuntan a Redis
  - [ ] Los 3 servicios (redis, celery-worker, celery-beat) levantan con docker-compose up sin errores
  - [ ] **(FIX-14)** Beat schedule definido ÚNICAMENTE en `app.conf.beat_schedule` dentro de `config/celery.py`. NO usar django-celery-beat (DB), NO duplicar en settings.py. Schedules canónicos: `evaluate_credit_clocks` (crontab hour=6, minute=0) y `process_pending_events` (cada 300s). Un solo lugar, una sola verdad.

---

### Item 2: Reloj de Crédito — Task + Evaluación
- **Agente:** AG-02 API Builder
- **Dependencia previa:** Item 1 aprobado
- **Command ref:** ENT_OPS_STATE_MACHINE §D2 (umbrales), §M2 (día 90), §C2 (bloqueo automático)
- **Archivos a tocar:** apps/expedientes/tasks.py (crear), apps/expedientes/services.py (extender con lógica de evaluación)
- **Archivos prohibidos:** models.py, views.py, urls.py, serializers.py
- **Criterio de done:**
  - [ ] `evaluate_credit_clocks()` — Celery periodic task (Beat, diario)
  - [ ] Consulta: todos los expedientes donde `credit_clock_started_at IS NOT NULL` AND `status NOT IN (CERRADO, CANCELADO)`
  - [ ] Cálculo: `days_elapsed = (now - credit_clock_started_at).days`
  - [ ] Día 60+: emite evento `credit_clock.warning { expediente_id, days_elapsed, threshold: 60 }` + INSERT event_log
  - [ ] Día 75+: si `is_blocked=false` → ejecuta bloqueo automático con actor interno SYSTEM. Contrato: `execute_command(expediente, "C17", data={blocked_reason: "credit_clock_75d"}, user=None, actor_type="SYSTEM", actor_id="credit_clock_75d")`. Bypass de IsCEO permission — el sistema es actor válido para bloqueo automático. EventLog registra: emitted_by="SYSTEM:evaluate_credit_clocks", payload incluye {"actor_type": "SYSTEM", "actor_id": "credit_clock_75d"}. NO se agregan columnas nuevas a EventLog — actor_type/actor_id van dentro de payload JSON. Emite `credit_clock.critical`.
  - [ ] Día 90+: emite `credit_clock.expired`. Si no estaba bloqueado (edge case), bloquea con actor_id="credit_clock_90d". Ref §M2.
  - [ ] Task es idempotente: una sola vez por vida del expediente por umbral. Correr N veces no duplica eventos ni bloqueos. Verificación: EventLog.filter(expediente=exp, event_type=tipo).exists() → skip.
  - [ ] Task corre dentro de transaction.atomic() por expediente (no global — si uno falla, los demás continúan)
  - [ ] Beat schedule registrado: `evaluate_credit_clocks` cada 24h (configurable)
  - [ ] Expedientes ya en CERRADO/CANCELADO son ignorados (reloj detenido per §D2)

**Reglas del reloj (FIX-13 — separación eventos vs enforcement):**

El task evalúa cada expediente en DOS pasos independientes:

**Paso 1 — Enforcement de bloqueo (se ejecuta SIEMPRE):**
- Si days_elapsed >= 75 AND is_blocked=false → ejecutar C17 con actor SYSTEM (actor_id="credit_clock_75d")
- Si days_elapsed >= 90 AND is_blocked=false → ejecutar C17 con actor SYSTEM (actor_id="credit_clock_90d")
- Esto se evalúa en cada corrida del task, sin importar si el evento ya fue emitido. Si CEO desbloqueó manualmente y el expediente sigue vencido, el sistema re-bloquea. Esto es un control de seguridad, no un evento.

**Paso 2 — Emisión de eventos (una sola vez por vida por umbral):**
- Umbral 60: emitir credit_clock.warning UNA vez. Si ya existe EventLog con event_type=credit_clock.warning para este expediente → skip para siempre.
- Umbral 75: emitir credit_clock.critical UNA vez. Si ya existe → skip.
- Umbral 90: emitir credit_clock.expired UNA vez. Si ya existe → skip.
- Verificación: EventLog.filter(expediente=exp, event_type=tipo).exists() → skip emisión.

**Resumen:** idempotencia aplica a emisión de eventos; el bloqueo es enforcement de seguridad y se reimpone si el CEO desbloqueó y el expediente sigue vencido.

**FIX-15 — Estados ignorados como constante (alineada a enum central):**
- Usar constante `CREDIT_CLOCK_IGNORED_STATUSES` en services/tasks, derivada del enum central de estados terminales del state machine (no lista paralela hardcodeada).
- MVP: `{CERRADO, CANCELADO}`. Si el enum central agrega otro estado terminal, se refleja en un solo lugar.
- Contrato de derivación: el enum de estados debe declarar `is_terminal=True` en cada estado terminal. `CREDIT_CLOCK_IGNORED_STATUSES = {s for s in ExpedienteStatus if s.is_terminal}`.

**Manejo de fallo en enforcement (C17):**
- Si execute_command(C17) falla para un expediente → log error con expediente_id + exception → continue al siguiente expediente.
- No retry/backoff en Sprint 2. El expediente fallido queda sin bloquear y se reintenta en la próxima corrida diaria (idempotencia natural del task).
- El transaction.atomic() por expediente ya protege: fallo en uno no afecta a los demás.

**Protección anti-carreras:**
- Dentro de cada transaction.atomic() por expediente: usar `select_for_update(skip_locked=True)` para evitar doble ejecución si dos workers corren el task simultáneamente.
- Si el expediente está locked por otro worker → skip silencioso (log + continue). Se reintenta en la próxima corrida diaria.
- C17 es idempotente por expediente cuando is_blocked=true (no re-bloquea), pero select_for_update evita la carrera en el instante de transición.
- Esto evita deadlocks y que un lock bloquee el batch completo.

**NO hacer en este item:**
- Notificaciones email/push (manual por ahora)
- Dashboard visual (Sprint 3)
- Lógica de cobro o reclamo (§M2 dice "CEO resuelve manualmente")

---

### Item 3: C19 SupersedeArtifact
- **Agente:** AG-02 API Builder
- **Dependencia previa:** Item 2 aprobado (services.py estable con evaluación) + Item 6 aprobado (campos superseded_by, supersedes existen)
- **Command ref:** ENT_OPS_STATE_MACHINE §I3, §I3.1
- **Archivos a tocar:** apps/expedientes/services.py (extender execute_command para C19), apps/expedientes/serializers.py (SupersedeArtifactSerializer), apps/expedientes/views.py (SupersedeArtifactView), apps/expedientes/urls.py
- **Archivos prohibidos:** models.py, tests/
- **Criterio de done:**
  - [ ] `POST /api/expedientes/{pk}/supersede-artifact/` → C19
  - [ ] Input: original_artifact_id, new_payload, reason
  - [ ] Precondiciones (§I3):
    - original.status = completed
    - CEO only
    - expediente.status ≠ CERRADO
    - nuevo artifact_type = mismo que original (ART-05 → ART-05)
    - new_payload cumple validation_rules del artifact_type
  - [ ] Regla post-transición (§I3.1.3): si el artefacto fue precondición de una transición ya ejecutada → expediente debe estar bloqueado (is_blocked=true). Si no está bloqueado → 409 con mensaje descriptivo.
  - [ ] Regla pre-transición (§I3.1.4): si la transición habilitada aún no ocurrió → supersede libre (CEO only, sin bloqueo requerido)
  - [ ] Mutaciones atómicas:
    - UPDATE original.status → superseded
    - UPDATE original.superseded_by → nuevo.id
    - INSERT nuevo ArtifactInstance (status=completed, supersedes=original.id)
    - INSERT event_log (emitted_by="C19:SupersedeArtifact")
  - [ ] Response 200: {"expediente": ..., "events": [event]}
  - [ ] Flujo completo de corrección: BlockExpediente → SupersedeArtifact → UnblockExpediente funcional

**Verificar modelo:** ArtifactInstance necesita campos `superseded_by` y `supersedes` (UUID nullable, FK a self). Si no existen de Sprint 0 → migración puntual (mismo patrón FIX-7 de Sprint 1). Declarar en "Decisiones asumidas".

---

### Item 4: C20 VoidArtifact
- **Agente:** AG-02 API Builder
- **Dependencia previa:** Item 3 aprobado
- **Command ref:** ENT_OPS_STATE_MACHINE §I5, §I5.1
- **Archivos a tocar:** apps/expedientes/services.py (extender), apps/expedientes/serializers.py, apps/expedientes/views.py, apps/expedientes/urls.py
- **Archivos prohibidos:** models.py, tests/
- **Criterio de done:**
  - [ ] `POST /api/expedientes/{pk}/void-artifact/` → C20
  - [ ] Input: artifact_id, reason
  - [ ] Precondiciones (§I5):
    - artifact.status = completed
    - CEO only
    - artifact_type ∈ voidable_list (ART-09, ART-10, ART-12). En Sprint 2: solo ART-09 es relevante (ART-10/12 no implementados)
  - [ ] Regla: ART-01 a ART-08 NO son voidables (son operativos, usar C19 para corregir)
  - [ ] Regla post-transición (§I5.1): si artefacto fue precondición de transición ejecutada → expediente debe estar bloqueado
  - [ ] Mutaciones atómicas:
    - UPDATE artifact.status → void
    - INSERT event_log (emitted_by="C20:VoidArtifact")
  - [ ] Response 200: {"expediente": ..., "events": [event]}
  - [ ] Efecto cascada en C14: si ART-09 es voided → payment_status no cambia, pero C14 (CloseExpediente) ya no puede ejecutarse porque ART-09.status ≠ completed. CEO debe emitir nueva factura (C13) antes de cerrar.

**Verificar modelo:** ArtifactInstance.status enum necesita valor `void` y `superseded`. Si no existen de Sprint 0 → migración puntual. Declarar en "Decisiones asumidas".

**NO hacer en este item:**
- Conector fiscal (void ART-09 → nota crédito externa). El sistema registra el void; la consecuencia fiscal es manual.

---

### Item 5: Event Dispatcher Mínimo
- **Agente:** AG-02 API Builder
- **Dependencia previa:** Item 1 aprobado (Celery funcional)
- **Command ref:** ENT_OPS_STATE_MACHINE §K (processed_at)
- **Archivos a tocar:** apps/expedientes/tasks.py (extender), apps/expedientes/services.py (mínimo)
- **Archivos prohibidos:** models.py, views.py, urls.py
- **Criterio de done:**
  - [ ] `process_pending_events()` — Celery periodic task (Beat, cada 5 minutos)
  - [ ] Consulta: EventLog WHERE processed_at IS NULL, ORDER BY occurred_at ASC, LIMIT 100
  - [ ] Para cada evento: UPDATE processed_at = now(). Sin side effects adicionales en Sprint 2.
  - [ ] Task idempotente: si un evento ya tiene processed_at, se ignora
  - [ ] Logging: cada batch procesado se loguea con conteo
  - [ ] Propósito Sprint 2: marca eventos como "procesados" para que Sprint 3+ pueda agregar consumers reales (notificaciones, webhooks) sin reprocesar historia

**NO hacer en este item:**
- Consumers reales (email, webhook, etc.)
- Redis Streams
- Retry logic sofisticada
- Dead letter queue

Este item es intencionalmente mínimo. Su valor es: (1) validar que el outbox pipeline funciona end-to-end, (2) mantener processed_at limpio para Sprint 3.

---

### Item 6: Migraciones de modelo (si necesarias)
- **Agente:** AG-01 Architect
- **Dependencia previa:** Ninguna (puede correr al inicio del sprint)
- **Archivos a tocar:** apps/expedientes/models.py (mínimo), apps/expedientes/enums.py (si aplica)
- **Archivos prohibidos:** views.py, services.py, tests/
- **Criterio de done:**
  - [ ] Verificar si ArtifactInstance tiene campos: `superseded_by` (UUID nullable FK self), `supersedes` (UUID nullable FK self)
  - [ ] Verificar si ArtifactInstance.status enum tiene valores: `void`, `superseded`
  - [ ] Si faltan → crear migración puntual
  - [ ] Si existen de Sprint 0 → este item es no-op (marcar DONE sin cambios)
  - [ ] `python manage.py migrate` sin errores
  - [ ] `python manage.py check` sin errores
  - [ ] Campos visibles en Django Admin

**Regla:** Este item NO reabre Sprint 0. Es addendum de compatibilidad Sprint 1→2, mismo patrón que FIX-7 (credit_clock_started_at).

---

### Item 7: Tests Sprint 2
- **Agente:** AG-06 QA
- **Dependencia previa:** Items 2-6 aprobados (incluye migraciones de Item 6 — QA necesita modelo completo)
- **Archivos a tocar:** tests/test_credit_clock.py (crear), tests/test_corrections.py (crear), tests/test_dispatcher.py (crear)
- **Archivos prohibidos:** apps/* (no tocar código producción)
- **Criterio de done:**

**Tests reloj de crédito:**
  - [ ] Test expediente con 59 días → no genera evento ni bloqueo
  - [ ] Test expediente con 60 días → genera credit_clock.warning, no bloquea
  - [ ] Test expediente con 75 días + is_blocked=false → bloquea automáticamente (blocked_by_type=SYSTEM)
  - [ ] Test expediente con 75 días + is_blocked=true → no re-bloquea, no duplica evento
  - [ ] Test expediente con 90 días → genera credit_clock.expired, verifica bloqueo
  - [ ] Test expediente CERRADO con clock > 60 días → ignorado (reloj detenido)
  - [ ] Test expediente CANCELADO con clock > 60 días → ignorado
  - [ ] Test idempotencia: correr task 2 veces → no duplica eventos
  - [ ] Test concurrencia (select_for_update): simular dos ejecuciones casi simultáneas del task sobre mismo expediente en day 75 + is_blocked=false → una sola transición efectiva, estado final bloqueado, sin duplicados
  - [ ] Test expediente sin credit_clock_started_at → ignorado

**Tests C19 SupersedeArtifact:**
  - [ ] Happy path: supersede ART-05 con nuevo payload → original.status=superseded, nuevo.status=completed
  - [ ] Falla si no CEO
  - [ ] Falla si expediente CERRADO
  - [ ] Falla si artifact_type diferente (ej: intentar supersede ART-05 con ART-06)
  - [ ] Falla si original.status ≠ completed
  - [ ] Post-transición: artefacto precondición de transición ejecutada + expediente NO bloqueado → 409
  - [ ] Post-transición: artefacto precondición de transición ejecutada + expediente bloqueado → OK
  - [ ] Pre-transición: artefacto cuya transición aún no ocurrió → supersede libre sin bloqueo
  - [ ] Atomicidad: monkeypatch fallo en INSERT nuevo → original no cambia status

**Tests C20 VoidArtifact:**
  - [ ] Happy path: void ART-09 → artifact.status=void
  - [ ] Falla si no CEO
  - [ ] Falla si artifact_type no es voidable (ej: ART-01)
  - [ ] Falla si artifact.status ≠ completed
  - [ ] Después de void ART-09: C14 CloseExpediente falla (ART-09 no completed)
  - [ ] Post-transición + no bloqueado → 409

**Tests event dispatcher:**
  - [ ] Eventos con processed_at=null → se marcan processed_at=now()
  - [ ] Eventos ya procesados → se ignoran
  - [ ] Task idempotente: 2 ejecuciones → mismos resultados

**Tests response format:**
  - [ ] C19 retorna {"expediente": ..., "events": [...]} con HTTP 200
  - [ ] C20 retorna {"expediente": ..., "events": [...]} con HTTP 200

---

## Dependencias entre items

```
LOTE_SM_SPRINT1 (aprobado)
    │
    ├── Item 6: Migraciones modelo (puede correr primero)
    │
    ├── Item 1: Infra Redis + Celery Worker (AG-07)
    │       │
    │       ├── Item 2: Reloj de Crédito (AG-02)
    │       │
    │       └── Item 5: Event Dispatcher Mínimo (AG-02)
    │
    ├── Item 3: C19 SupersedeArtifact (AG-02, después de Item 2)
    │       │
    │       └── Item 4: C20 VoidArtifact (AG-02, después de Item 3)
    │
    └── Item 7: Tests Sprint 2 (AG-06, después de Items 2-5)
```

**Paralelismo posible:**
- Item 6 (migraciones) puede correr en paralelo con Item 1 (infra)
- Item 5 (dispatcher) puede correr en paralelo con Items 2-4 (ambos dependen solo de Item 1)
- Items 3-4 son secuenciales (C20 usa los mismos patrones que C19)

---

## Criterio de cierre de Sprint 2

Sprint 2 está DONE cuando:

1. Redis + Celery worker corriendo y funcionales
2. Celery Beat ejecutando 2 periodic tasks: evaluate_credit_clocks (diario) + process_pending_events (cada 5 min)
3. Reloj de crédito evalúa automáticamente día 60/75/90 para todos los expedientes activos
4. Bloqueo automático día 75 funcional (SYSTEM bloquea, CEO desbloquea)
5. Día 90 genera evento credit_clock.expired
6. C19 SupersedeArtifact funcional con todas las reglas §I3.1
7. C20 VoidArtifact funcional para ART-09 (voidable list)
8. Flujo completo corrección post-transición: Block → Supersede → Unblock funcional
9. Event dispatcher marcando eventos como procesados
10. Todos los tests de Item 7 passing
11. Los 18 command endpoints de Sprint 1 siguen funcionales (no regresión)
12. ArtifactInstance tiene campos superseded_by, supersedes, status incluye void/superseded

**Lo que significa "Sprint 2 DONE":**
- El sistema protege al CEO: si un expediente se acerca a 90 días, el sistema bloquea automáticamente
- El CEO puede corregir errores en artefactos sin romper la state machine
- El outbox se procesa (aunque sin consumers reales aún)
- Total: 18 command endpoints POST (Sprint 1) + 2 nuevos (C19, C20) = 20 command endpoints POST

**Lo que NO debe existir al cerrar Sprint 2:**
- Frontend/UI (Sprint 3)
- Notificaciones email/push (Sprint 3+)
- Consumers reales del event dispatcher (Sprint 3+)
- ART-10, ART-12 (post-MVP)
- Conector fiscal
- Redis Streams event bus

---

## Qué queda para Sprint 3+

| Feature | Sprint |
|---------|--------|
| Frontend básico (lista + detalle + timeline + semáforos) | 3 |
| Notificaciones (email CEO en alertas crédito, eventos importantes) | 3 |
| Event consumers reales (dispatcher → acciones) | 3 |
| Costos doble vista | 4 |
| Factura MWT generación | 4 |
| Dashboard financiero | 4+ |

---

Stamp: FROZEN v3.5 — Aprobado CEO 2026-02-27
Auditoría: 4 rondas ChatGPT, calificación final 10/10
Origen: ENT_OPS_STATE_MACHINE v1.2.2 (FROZEN) + PLB_ORCHESTRATOR v1.2.2 (FROZEN) + priorización CEO 2026-02-27
Changelog: v1.0→v2.0→v3.0→v3.1→v3.2→v3.3→v3.4→v3.5 (15+ fixes acumulados)
