# Tareas MWT - Sprint 1: API Funcional (18 Command Handlers)

A continuación se detalla la lista de tareas a importar en Asana bajo el proyecto **Tareas MWT** (Sección: Sprint 1) derivadas de `PLB_SPRINT1_PROMPTS.md`, `PLB_SPRINT1_EJECUCION.md` y `PLB_SPRINT1_EJECUCION_ALE.md`.

**Prerequisito:** Sprint 0 DONE (5 items aprobados, 6 contenedores, modelos en PostgreSQL).

**Objetivo Sprint 1:** Construir toda la API — 18 command handlers (endpoints) que permiten al CEO operar expedientes de importación desde REGISTRO hasta CERRADO, incluyendo cancelación, bloqueo, costos y pagos. Todo vía API, sin UI.

---

## Tareas

### Tarea 0: Sprint 1 - Pre-Sprint: Addendum de Modelo (FIX-7)
- **Responsable (Agente):** AG-02 API Builder
- **Dependencia:** Sprint 0 DONE.
- **Descripción:** Verificar si el campo `credit_clock_started_at` (DateTimeField, nullable, blank=True, default=None) existe en el modelo Expediente. Si no existe, crear migración puntual. Correr `makemigrations` + `migrate`. Verificar campo visible en Django Admin. Este paso es previo a Item 1A — es addendum de compatibilidad Sprint 0→1.
- **Criterios de Éxito:**
  - Campo `credit_clock_started_at` existe en modelo Expediente.
  - `python manage.py migrate` sin errores.
  - Campo visible en Django Admin.
- **Branch:** N/A (addendum directo en main o branch de compatibilidad).

---

### Tarea 1: Sprint 1 - Item 1A: Read Serializers
- **Responsable (Agente):** AG-02 API Builder
- **Dependencia:** Pre-Sprint (Tarea 0) completado.
- **Descripción:** Crear 5 serializers de lectura para los modelos existentes de Sprint 0: ExpedienteSerializer (con status display, is_blocked, payment_status, timestamps, credit_clock_started_at), ArtifactInstanceSerializer, CostLineSerializer, PaymentLineSerializer, EventLogSerializer.
- **Archivos:** `apps/expedientes/serializers.py` (crear).
- **Criterios de Éxito:**
  - 5 serializer classes en serializers.py.
  - Cada serializer mapea correctamente a su modelo.
  - No hay campos inventados que no existan en el modelo.
  - ExpedienteSerializer muestra status como display string.
  - ExpedienteSerializer incluye credit_clock_started_at.
  - Archivo importable sin errores.
- **Riesgos:** Campos que no existen en los modelos de Sprint 0.
- **Branch:** `sprint1/item-1a-read-serializers`

---

### Tarea 2: Sprint 1 - Item 1B: Write Serializers por Command
- **Responsable (Agente):** AG-02 API Builder
- **Dependencia:** Item 1A aprobado.
- **Descripción:** Crear serializers de escritura para validar inputs de cada command: ExpedienteCreateSerializer (C1), RegisterCostSerializer (C15), RegisterPaymentSerializer (C21), y serializers para commands con artifact payload (C2-C10). Referencia: ENT_OPS_STATE_MACHINE §F1. NO crear serializers para ART-10, ART-12, C19, C20.
- **Archivos:** `apps/expedientes/serializers.py` (extender).
- **Criterios de Éxito:**
  - ExpedienteCreateSerializer con inputs de C1 (brand, client_id, mode, freight_mode, transport_mode, dispatch_mode, price_basis, credit_clock_start_rule).
  - RegisterCostSerializer con inputs de C15.
  - RegisterPaymentSerializer con inputs de C21.
  - Al menos un serializer por command con artifact payload (C2-C10).
  - No hay serializers para ART-10, ART-12, C19, C20.
  - Archivo importable sin errores.
- **Branch:** `sprint1/item-1b-write-serializers`

---

### Tarea 3: Sprint 1 - Item 2: Domain Logic + API Guards ⚠️ CRÍTICO
- **Responsable (Agente):** AG-02 API Builder
- **Dependencia:** Item 1B aprobado.
- **Descripción:** Crear la capa de dominio (services.py), errores tipados (exceptions.py) y permisos (permissions.py). Este es el item más crítico — todo el resto depende de él. services.py tiene 4 funciones principales: `create_expediente(data, user)→(exp, event)`, `can_transition_to(exp, target)→bool`, `can_execute_command(exp, cmd, user)→raise-or-pass`, `execute_command(exp, cmd, data, user)→(exp, events_list)`. Incluye auto-transiciones C5/C10 con 2 eventos (FIX-5), credit clock persist (FIX-3), y EnsureNotBlocked bypass para C16/C17/C18 (FIX-8).
- **Archivos:** `apps/expedientes/services.py`, `apps/expedientes/exceptions.py`, `apps/expedientes/permissions.py`.
- **Criterios de Éxito:**
  - services.py con 4 funciones con contratos FIX-2 respetados.
  - Toda lógica dentro de transaction.atomic().
  - Auto-transiciones (C5, C10) emitiendo 2 eventos dentro del mismo atomic (FIX-5).
  - can_transition_to evalúa estado + bloqueo + artifacts + policies.
  - exceptions.py con 3 excepciones tipadas (CommandValidationError→400, TransitionNotAllowedError→409, ArtifactMissingError→409).
  - permissions.py con IsCEO, EnsureNotBlocked, EnsureCommandAllowed.
  - EnsureNotBlocked NO aplica a C16/C17/C18 (FIX-8).
  - Credit clock: solo persist credit_clock_started_at en C1 (on_creation) y C7 (on_shipment). NO Celery (FIX-3).
  - event_log.emitted_by con formato "CX:CommandName".
- **Riesgos:** AG-02 inventa reglas de negocio. Mezcla de capas. Auto-transiciones mal implementadas.
- **⚠️ REVISIÓN CEO OBLIGATORIA antes de avanzar a Item 3.**
- **Branch:** `sprint1/item-2-domain-logic`

---

### Tarea 4: Sprint 1 - Item 3: Endpoints REGISTRO (C1-C5)
- **Responsable (Agente):** AG-02 API Builder
- **Dependencia:** Items 1A + 1B + 2 aprobados.
- **Descripción:** 5 endpoints POST para la fase REGISTRO. Patrón: APIView por command (NO ViewSet). C1 CreateExpediente (201), C2 RegisterOC (201), C3 CreateProforma (201), C4 DecideModeBC — CEO only (201), C5 RegisterSAPConfirmation — auto-transición→PRODUCCION con 2 eventos (201).
- **Archivos:** `apps/expedientes/views.py` (crear), `apps/expedientes/urls.py` (crear).
- **Criterios de Éxito:**
  - 5 APIView classes, cada view llama a services sin lógica propia.
  - Response body: `{"expediente": ..., "events": [...]}` en todos (FIX-1).
  - C5 retorna 2 eventos en events (FIX-5).
  - HTTP status: C1-C5 = 201.
  - URLs con {pk}.
- **Branch:** `sprint1/item-3-registro-endpoints`

---

### Tarea 5: Sprint 1 - Item 4: Endpoints PRODUCCION + PREPARACION (C6-C10)
- **Responsable (Agente):** AG-02 API Builder
- **Dependencia:** Item 3 aprobado.
- **Descripción:** 5 endpoints POST: C6 ConfirmProduction (200), C7 RegisterShipment (201) — persiste credit_clock_started_at si rule=on_shipment, C8 RegisterFreightQuote (201), C9 RegisterCustoms (201) — solo si dispatch_mode=mwt, C10 ApproveDispatch (201) — gate final con auto-transición→DESPACHO y 2 eventos.
- **Archivos:** `apps/expedientes/views.py` (extender), `apps/expedientes/urls.py` (extender).
- **Criterios de Éxito:**
  - 5 APIViews thin que llaman a services.
  - C6=200, C7-C9=201, C10=201.
  - C10 retorna 2 eventos (FIX-5).
  - C7 NO implementa credit clock en view — vive en services (FIX-3).
  - C9 solo ejecuta si dispatch_mode=mwt.
  - Regla de orden: C7→C8→C9→C10 (mwt) o C7→C8→C10 (client).
  - Response body: `{"expediente": ..., "events": [...]}`.
- **Branch:** `sprint1/item-4-produccion-endpoints`

---

### Tarea 6: Sprint 1 - Item 5: Endpoints DESPACHO→CERRADO + Pagos (C11-C14, C21)
- **Responsable (Agente):** AG-02 API Builder
- **Dependencia:** Item 4 aprobado.
- **Descripción:** 5 endpoints POST: C11 ConfirmDeparture (200), C12 ConfirmArrival (200), C13 IssueInvoice (201), C21 RegisterPayment (201) — acumulación SUM≥total→paid y sobrepago OK, C14 CloseExpediente (200) — pre: ART-09 + payment_status=paid + is_blocked=false.
- **Archivos:** `apps/expedientes/views.py` (extender), `apps/expedientes/urls.py` (extender).
- **Criterios de Éxito:**
  - 5 APIViews thin.
  - C11=200, C12=200, C13=201, C21=201, C14=200.
  - C21 acumulación: pending→partial→paid funcional (en services).
  - C14 falla si payment_status ≠ paid.
  - Response body: `{"expediente": ..., "events": [...]}`.
- **Branch:** `sprint1/item-5-despacho-endpoints`

---

### Tarea 7: Sprint 1 - Item 6: Endpoints Costos + Cancel + Block (C15-C18)
- **Responsable (Agente):** AG-02 API Builder
- **Dependencia:** Item 2 aprobado (puede correr en paralelo con Items 3-5).
- **Descripción:** 4 endpoints POST: C15 RegisterCost (201) — append-only, pre: status ≠ CERRADO/CANCELADO; C16 CancelExpediente (200) — CEO only, desde 3 estados, ignora bloqueo §C3; C17 BlockExpediente (200) — pre: is_blocked=false; C18 UnblockExpediente (200) — CEO only. Ninguno usa EnsureNotBlocked (FIX-8).
- **Archivos:** `apps/expedientes/views.py` (extender), `apps/expedientes/urls.py` (extender).
- **Criterios de Éxito:**
  - 4 APIViews thin.
  - C15=201, C16=200, C17=200, C18=200.
  - C16 solo acepta desde REGISTRO, PRODUCCION, PREPARACION.
  - C16 y C18 son CEO only (IsCEO permission).
  - C16, C17, C18 NO usan EnsureNotBlocked (FIX-8).
  - C17/C18 escriben event_log para historia.
- **Branch:** `sprint1/item-6-exception-endpoints`

---

### Tarea 8: Sprint 1 - Item 7: URL Registry
- **Responsable (Agente):** AG-02 API Builder
- **Dependencia:** Items 3-6 implementados.
- **Descripción:** Consolidar todas las URLs y registrar en config/urls.py. Verificar que todos los endpoints usan {pk}, están bajo /api/expedientes/, y que no existen rutas para C19, C20, ART-10, ART-12.
- **Archivos:** `apps/expedientes/urls.py` (consolidar), `config/urls.py` (registrar include).
- **Criterios de Éxito:**
  - Todos los endpoints bajo /api/expedientes/.
  - URL patterns limpios y consistentes con {pk}.
  - config/urls.py incluye expedientes.urls.
  - `python manage.py show_urls` muestra las 18 rutas.
  - No hay rutas para ART-10, ART-12, C19, C20.
- **Branch:** `sprint1/item-7-url-registry`

---

### Tarea 9: Sprint 1 - Item 8: Tests de Transición (spec-based)
- **Responsable (Agente):** AG-06 QA
- **Dependencia:** Item 2 aprobado (necesita importar services.py).
- **Descripción:** Tests que verifican la state machine: transiciones válidas, prohibidas, cancelación, bloqueo. Crear ExpedienteFactory con status configurable. Test happy path 7 transiciones REGISTRO→CERRADO. Test cada transición prohibida §B3. Test cancelación (3 permitidas + 4 prohibidas). Test bloqueo/desbloqueo.
- **Archivos:** `tests/test_transitions.py`, `tests/factories.py`, `tests/conftest.py`.
- **Criterios de Éxito:**
  - ExpedienteFactory funcional.
  - Happy path test: 7 transiciones exitosas en secuencia.
  - Al menos 1 test por cada transición prohibida de §B3.
  - 3 tests cancelación permitida + 4 tests cancelación prohibida.
  - Test bloqueo + desbloqueo.
  - Tests usan contratos reales de services.py (FIX-2).
  - Todos los tests passing.
- **Branch:** `sprint1/item-8-tests-transitions`

---

### Tarea 10: Sprint 1 - Item 9: Tests de Commands (API-based)
- **Responsable (Agente):** AG-06 QA
- **Dependencia:** Items 3-6 aprobados (endpoints funcionales).
- **Descripción:** Tests end-to-end vía API para cada command. ~30 tests esperados. Incluye: happy path + failure por cada command, auto-transición C5/C10 con 2 eventos, permisos CEO-only (C4, C16, C18), bloqueo, atomicidad (3 casos con monkeypatch), response format (FIX-1), credit clock (FIX-3), EnsureNotBlocked bypass (FIX-8).
- **Archivos:** `tests/test_commands.py`, `tests/test_permissions.py`, `tests/conftest.py`.
- **Criterios de Éxito:**
  - Al menos 1 test happy path + 1 test failure por cada command.
  - Test auto-transición C5 y C10 con 2 eventos (FIX-5).
  - Test gate C10 con dispatch_mode=mwt vs client.
  - Test C14 falla sin payment.
  - Test C21 acumulación completa (pending→partial→paid + sobrepago).
  - Tests permissions (3 CEO-only commands).
  - Test is_blocked impide commands operativos.
  - 3 tests atomicidad passing (monkeypatch).
  - Tests response format body y HTTP status (FIX-1).
  - Tests credit clock persist en C1 y C7 (FIX-3).
  - Tests EnsureNotBlocked bypass: C16 OK bloqueado, C18 OK bloqueado (FIX-8).
  - Todos los tests passing.
- **Branch:** `sprint1/item-9-tests-commands`

---

## Criterio de Cierre Sprint 1

Sprint 1 está **DONE** cuando:
1. 18 endpoints POST funcionales bajo /api/expedientes/.
2. Happy path completo: C1→C2→C3→C4→C5→C6→C7→C8→C9→C10→C11→C12→C13→C21→C14 funcional vía API.
3. Cancelación funcional: C16 desde REGISTRO, PRODUCCION, PREPARACION.
4. Bloqueo/desbloqueo funcional: C17/C18.
5. Costos: C15 registra, C21 acumula pagos.
6. Todos los tests passing (Sprint 0 + Sprint 1).
7. 0 endpoints para C19, C20.
8. `manage.py check` sin errores.

## Lo que NO debe existir en Sprint 1
- Frontend/UI (Sprint 3)
- Event consumers/dispatcher (Sprint 2)
- Reloj de crédito automático (Sprint 2) — solo credit_clock_started_at
- C19/C20 SupersedeArtifact/VoidArtifact (Sprint 2)
- ART-10 Factura comisión / ART-12 Nota compensación (post-MVP)
- Conectores externos
- RBAC formal (MVP = is_superuser)
