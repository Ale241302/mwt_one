# PLB_SPRINT1_EJECUCION — Paquete de Ejecución Sprint 1
status: VIGENTE
visibility: [INTERNAL]
domain: Plataforma (IDX_PLATAFORMA)
version: 2.1
tipo: Playbook (instrucción operativa)
refs: LOTE_SM_SPRINT1 (FROZEN), PLB_ORCHESTRATOR v1.2.2 (FROZEN), ENT_OPS_STATE_MACHINE v1.2.2 (FROZEN)
complemento: PLB_SPRINT1_PROMPTS (prompts tácticos para Antigravity)
prerrequisito: Sprint 0 DONE (todos los items aprobados)
changelog: |
  v2.1 — 8 fixes post-audit (Claude + ChatGPT) + conformidad taxonómica:
  FIX-1: Response payload y HTTP status codes congelados
  FIX-2: Contratos de can_transition_to vs can_execute_command explícitos
  FIX-3: Credit clock en Sprint 1 = solo persistir dato, no computar
  FIX-4: ART-10/ART-12 declarados explícitamente como fuera de Sprint 1
  FIX-5: Commands con auto-transición emiten 2 eventos
  FIX-6: Protocolo SPEC_GAP para Ale
  FIX-7: credit_clock_started_at como addendum de modelo pre-Item 1A
  FIX-8: EnsureNotBlocked no aplica a C16/C17/C18
  v2.1: Renombre a PLB_, headers, stamp POL_STAMP, conteo 10 items, registro IDX_PLATAFORMA

---

# 1. RESUMEN EJECUTIVO

Sprint 1 transforma los modelos de Sprint 0 en una API funcional de 18 commands que cubre el ciclo completo del expediente: REGISTRO→CERRADO + cancelación + bloqueo + costos + pagos. El resultado es un backend Django donde el CEO puede operar expedientes reales via API directa + Django Admin, sin frontend.

El sprint tiene 10 items (1A, 1B, 2-9) distribuidos en 2 agentes: AG-02 API Builder (Items 1A-7, endpoints y domain logic) y AG-06 QA (Items 8-9, tests). El CEO sigue como orquestador.

Complejidad mayor que Sprint 0: más items, dependencias más largas, un agente nuevo (AG-06 QA que puede trabajar en modo read-only anticipado), y la primera vez que lógica de dominio real entra al sistema. El riesgo principal no es técnico sino de disciplina: que AG-02 invente reglas de negocio o que mezcle capas.

Patrón arquitectural: command-heavy, no CRUD-first. Cada command = 1 endpoint POST dedicado. APIView por command. No ViewSet + @action.

---

# 2. DECISIONES CONGELADAS SPRINT 1 (v2.1)

Todas las decisiones de Sprint 0 siguen vigentes, más las siguientes:

## 2.0 Fixes v2 (decisiones congeladas nuevas)

### FIX-1: Response payload y HTTP status codes

Formato de response body unificado para todos los endpoints:

```json
{"expediente": {...}, "events": [...]}
```

- `expediente`: objeto serializado con ExpedienteSerializer (read)
- `events`: array de EventLogSerializer (read). 1 evento para commands normales, 2 eventos para commands con auto-transición (C5, C10).

HTTP status codes de éxito:
- C1 → 201 Created (nuevo recurso)
- C2-C5, C7-C10, C13, C15, C21 → 201 Created (crean artifact o line)
- C6, C11, C12, C14, C16 → 200 OK (solo transición, no crean recurso nuevo)
- C17, C18 → 200 OK (block/unblock)

Errores:
- CommandValidationError → 400 Bad Request
- PermissionDenied (DRF) → 403 Forbidden
- TransitionNotAllowedError → 409 Conflict
- ArtifactMissingError → 409 Conflict

### FIX-2: Contratos de funciones de services.py

Dos contratos distintos, no mezclar:

| Función | Retorno | Side effects | Uso |
|---------|---------|-------------|-----|
| `can_transition_to(expediente, target_state)` | `bool` (True/False) | Ninguno (puro) | Uso interno en auto-transiciones dentro de execute_command |
| `can_execute_command(expediente, command_name, user)` | No retorna False. O permite (implícito) o raise exception tipada | Ninguno | Guard en views. Si no lanza, se puede proceder |
| `execute_command(expediente, command_name, data, user)` | `(expediente, events_list)` | Mutaciones atómicas | Orquestador principal |
| `create_expediente(data, user)` | `(expediente, event)` | INSERT atómico | Solo para C1 |

Regla: `can_execute_command` nunca retorna `False`. Su contrato es: si hay problema, raise. Si no hay raise, el caller procede.

### FIX-3: Credit clock en Sprint 1

En Sprint 1, el credit clock se limita a persistir el dato, no a computar umbrales ni disparar alertas.

- C1: si `credit_clock_start_rule=on_creation` → `UPDATE expediente.credit_clock_started_at = now()` dentro del atomic de create_expediente.
- C7: si `credit_clock_start_rule=on_shipment` → `UPDATE expediente.credit_clock_started_at = now()` dentro del atomic de execute_command.
- No crear Celery tasks, no agendar Beat, no disparar consumers, no evaluar día 60/75/90.
- Sprint 2 usará `credit_clock_started_at` para computar los umbrales.

### FIX-4: Artefactos excluidos de Sprint 1

Los siguientes artefactos existen en la state machine (§E) pero NO se implementan en Sprint 1:

| Artefacto | Razón de exclusión | Cuándo |
|-----------|-------------------|--------|
| ART-10 Factura comisión | Solo aplica si mode=COMISION. Post-MVP | Sprint 3+ |
| ART-12 Nota compensación | [CEO-ONLY], opcional | Sprint 3+ |
| C19 SupersedeArtifact | Corrección artifacts — no happy path | Sprint 2 |
| C20 VoidArtifact | Anulación fiscal — no MVP | Sprint 2 |

Si Antigravity encuentra referencias a ART-10 o ART-12 en la state machine, debe ignorarlas. No implementar, no preguntar, no crear stubs.

### FIX-5: Commands con auto-transición emiten 2 eventos

La state machine §F1 define:
- C5: emite `sap.confirmed` + `expediente.state_changed`
- C10: emite `dispatch.approved` + `expediente.state_changed`

Dentro de `execute_command`, cuando un command tiene auto-transición:
1. INSERT event_log con evento del command (ej: `sap.confirmed`)
2. Evaluar `can_transition_to(target_state)`
3. Si True → UPDATE status + INSERT event_log con `expediente.state_changed`
4. Todo dentro del mismo `transaction.atomic()`

El response body retorna `"events": [event1, event2]` (array con 2 elementos).

Para commands sin auto-transición, el array tiene 1 elemento.

### FIX-6: Protocolo SPEC_GAP para Ale

Cuando Antigravity reporta `[SPEC_GAP]`:

1. Ale NO intenta resolver el gap
2. Ale NO le dice a Antigravity "asumí X"
3. Ale escala al CEO (Alvaro) con: item afectado + descripción del gap + texto exacto del reporte
4. CEO decide: (a) resolver el gap y re-despachar el item, o (b) declarar el gap como cosmético y autorizar continuación
5. Si el gap afecta lógica de dominio, el item queda BLOCKED hasta que CEO resuelva

### FIX-7: credit_clock_started_at — Addendum de modelo pre-Item 1A

El campo `credit_clock_started_at: DateTimeField, nullable, blank=True, default=None` debe existir en el modelo `Expediente` antes de que Sprint 1 arranque.

Si Sprint 0 no lo incluyó:
- Se agrega como migración puntual al inicio de Sprint 1, ANTES de Item 1A.
- No reabre Sprint 0. Es un addendum de compatibilidad Sprint 0→1.
- AG-02 puede crear la migración como paso previo, declarándolo en "Decisiones asumidas" de Item 1A.
- El campo es nullable porque expedientes creados antes de Sprint 1 no lo tendrán.

Si Sprint 0 ya lo incluyó: este fix es no-op.

Este fix cierra la dependencia de FIX-3 (C1 y C7 necesitan persistir el dato).

### FIX-8: EnsureNotBlocked no aplica a C16, C17, C18

La state machine §C3 establece que la cancelación ignora bloqueo. Por extensión lógica:

| Command | ¿Usa EnsureNotBlocked? | Razón |
|---------|----------------------|-------|
| C2-C15, C21 | SÍ | Commands operativos — bloqueado impide ejecución |
| C16 CancelExpediente | NO | Cancelación bypasses bloqueo por diseño (§C3) |
| C17 BlockExpediente | NO | El expediente ya está desbloqueado (precondición: is_blocked=false). Aplicar EnsureNotBlocked sería redundante pero no dañino. Sin embargo, NO se aplica para mantener consistencia con la regla: "C16/C17/C18 no usan EnsureNotBlocked" |
| C18 UnblockExpediente | NO | El expediente ESTÁ bloqueado — aplicar EnsureNotBlocked lo rechazaría, que es exactamente lo contrario de lo que se necesita |

Regla para views.py: los endpoints de C16, C17 y C18 NO incluyen `EnsureNotBlocked` en sus permission_classes. Solo usan `IsCEO` donde aplica (C16, C18) y autenticación base.

Regla para services.py: `can_execute_command` para C16 NO evalúa is_blocked. Para C17 evalúa is_blocked=false como precondición (no se puede bloquear lo que ya está bloqueado). Para C18 evalúa is_blocked=true como precondición (no se puede desbloquear lo que no está bloqueado).

## 2.1 Decisiones heredadas de Sprint 0 + Sprint 1

1. **Patrón command-heavy** (LOTE_SM_SPRINT1): 1 command = 1 POST endpoint. No ViewSet.
2. **Domain logic en services.py** (LOTE_SM_SPRINT1 Item 2): no en views, no en models, no en signals.
3. **Excepciones tipadas** (LOTE_SM_SPRINT1 Item 2): CommandValidationError→400, TransitionNotAllowedError→409, ArtifactMissingError→409.
4. **Outbox write-only** (scope Sprint 1): EventLog se llena, no se consume. Dispatcher viene en Sprint 2.
5. **MVP permissions** (LOTE_SM_SPRINT1 Item 2): IsCEO = is_superuser. No RBAC.
6. **Sobrepago permitido** (ENT_OPS_STATE_MACHINE §M): si SUM(payments) > invoice_total → paid. Diferencia es ajuste manual.
7. **1 moneda por expediente** (ENT_OPS_STATE_MACHINE §M): PaymentLine.currency debe coincidir con ART-09.currency.
8. **Lookup de URL: pk** — Todos los endpoints usan `{pk}` como lookup en la URL. lookup_field en views = `'pk'`. Si Sprint 0 usa UUID como PK, pk IS the UUID. No crear lookup_field separado.
9. **event_log.emitted_by** con formato `"CX:CommandName"` (ej: `"C5:RegisterSAPConfirmation"`).
10. **credit_clock_started_at en modelo Expediente** (FIX-7): DateTimeField, nullable. Si no existe de Sprint 0, se agrega como migración pre-Item 1A.
11. **EnsureNotBlocked excluye C16/C17/C18** (FIX-8): solo commands operativos (C2-C15, C21) usan el guard de bloqueo.

---

# 3. PLAN DE EJECUCIÓN (Sprint 1)

## 3.1 Secuencia real

```
PRE-SPRINT 1 — Addendum de modelo (si necesario)
│
├── Verificar si credit_clock_started_at existe en Expediente
│   └── Si NO existe → migración puntual (FIX-7) antes de Item 1A
│
FASE A — Serialización (AG-02 API)
│
├── Item 1A: Read Serializers (5 serializers de lectura)
│   └── Item 1B: Write Serializers por command (4+ serializers de escritura)
│
FASE B — Domain Logic (AG-02 API)
│
└── Item 2: services.py + exceptions.py + permissions.py
    │
    FASE C — Endpoints (AG-02 API) — puede ser parcialmente paralelo
    │
    ├── Item 3: REGISTRO (C1-C5) ← camino principal
    │   ├── Item 4: PRODUCCION + PREPARACION (C6-C10)
    │   │   └── Item 5: DESPACHO→CERRADO + Pagos (C11-C14, C21)
    │   └── Item 6: Costos + Cancel + Block (C15-C18) ← paralelo a Item 4
    │
    └── Item 7: URL Registry (consolidación final)

FASE D — Tests (AG-06 QA) — Item 8 después de Item 2 aprobado
│
├── Item 8: Tests de transición (después de Item 2 aprobado — necesita importar services)
└── Item 9: Tests de commands (después de Items 3-6 aprobados)
```

**Cambio vs v1:** Item 8 ya NO arranca en modo anticipado antes de que services.py exista. Los tests de transición necesitan importar `can_transition_to` y `execute_command` para funcionar. Si AG-06 arranca antes, inventará mocks que no reflejan la implementación real. Item 8 arranca cuando Item 2 está aprobado.

## 3.2 Desglose por item

### Item 1A: Read Serializers

Agente: AG-02 API Builder.
Objetivo: 5 serializers de lectura para los modelos de Sprint 0.

Archivos permitidos: apps/expedientes/serializers.py.
Archivos prohibidos: models.py, tests/, docker-compose.yml.

Precondiciones: LOTE_SM_SPRINT0 Items 2-4B aprobados (modelos estables).

Criterios de done:
- ExpedienteSerializer (read): status display, is_blocked, payment_status, timestamps, legal_entity, client, brand
- ArtifactInstanceSerializer (read): type, status, payload summary, timestamps
- CostLineSerializer (read): todos los campos
- PaymentLineSerializer (read): todos los campos
- EventLogSerializer (read-only): para timeline del expediente

Evidencia: serializers.py con 5 clases, cada una mapeando correctamente a los modelos de Sprint 0.

### Item 1B: Write Serializers por Command

Agente: AG-02 API Builder.
Objetivo: Serializers de escritura para validar inputs de cada command.

Archivos permitidos: apps/expedientes/serializers.py (extend).
Archivos prohibidos: models.py, tests/.

Precondiciones: Item 1A aprobado.

Criterios de done:
- ExpedienteCreateSerializer (C1): brand, client_id, mode, freight_mode, transport_mode, dispatch_mode, price_basis, credit_clock_start_rule (optional)
- RegisterCostSerializer (C15): cost_type, amount, currency, phase, description
- RegisterPaymentSerializer (C21): amount, currency, method, reference
- Serializers para commands con artifact payload (C2-C10): validación de inputs requeridos por cada command según ENT_OPS_STATE_MACHINE §F1

Referencia de campos: ENT_OPS_STATE_MACHINE §F1 (inputs de cada command). No inventar campos de validación que no estén en la spec.

### Item 2: Domain Logic + API Guards

Agente: AG-02 API Builder.
Objetivo: Capa de dominio y permisos. Este es el item más crítico — aquí vive la lógica de negocio.

Archivos permitidos: apps/expedientes/services.py, apps/expedientes/exceptions.py, apps/expedientes/permissions.py.
Archivos prohibidos: models.py, tests/.

Precondiciones: Item 1B aprobado.

Criterios de done:

**services.py** — capa de dominio:
- `create_expediente(data, user)`: handler específico para C1. Resuelve credit_clock_start_rule según §D1. Si rule=on_creation, persiste credit_clock_started_at=now() (FIX-3). Corre dentro de transaction.atomic(). Retorna `(expediente, event)`.
- `can_transition_to(expediente, target_state)`: método puro. Retorna `bool`. Evalúa: (1) estado actual válido según §B, (2) is_blocked==false, (3) artefactos requeridos según §E existen y están completed, (4) policy checks (dispatch_mode, payment_status).
- `can_execute_command(expediente, command_name, user)`: guard. No retorna False — o permite o raise exception tipada (FIX-2). Combina precondiciones del command + permisos.
- `execute_command(expediente, command_name, data, user)`: orquesta todo dentro de transaction.atomic(). Para C7 con rule=on_shipment, persiste credit_clock_started_at=now() (FIX-3). Para C5/C10, emite 2 eventos (FIX-5). Retorna `(expediente, events_list)`.

**exceptions.py** — errores tipados:
- CommandValidationError → 400 (input inválido o precondición no cumplida)
- TransitionNotAllowedError → 409 (transición prohibida)
- ArtifactMissingError → 409 (artefacto requerido no existe)

**permissions.py** — wrappers HTTP (thin layer, delegan a services):
- IsCEO (MVP: is_superuser)
- EnsureNotBlocked (delega a services) — NO aplica a C16, C17, C18 (FIX-8)
- EnsureCommandAllowed (delega a services)
- Guards devuelven errores descriptivos (qué falta, no solo "prohibido")

Referencia canónica: ENT_OPS_STATE_MACHINE §B (transiciones), §F (commands), §J (auto-transiciones), §C (bloqueo).

### Item 3: Endpoints REGISTRO (C1-C5)

Agente: AG-02 API Builder.
Objetivo: 5 endpoints POST para la fase de registro.

Archivos permitidos: apps/expedientes/views.py, apps/expedientes/urls.py.
Archivos prohibidos: models.py, tests/.

Precondiciones: Items 1A + 1B + 2 aprobados.

Patrón: 1 command = 1 APIView con método POST. No ViewSet. Lookup: `pk`.

Endpoints:
- POST /api/expedientes/ → C1 CreateExpediente. Usa create_expediente() de services.py. Response: 201, `{"expediente": ..., "events": [event]}`.
- POST /api/expedientes/{pk}/register-oc/ → C2. Crea ART-01. Pre: status=REGISTRO, is_blocked=false. Response: 201.
- POST /api/expedientes/{pk}/create-proforma/ → C3. Crea ART-02. Pre: status=REGISTRO, ART-01 exists. Response: 201.
- POST /api/expedientes/{pk}/decide-mode/ → C4. Crea ART-03. Pre: status=REGISTRO, ART-02 exists, CEO only. Response: 201.
- POST /api/expedientes/{pk}/confirm-sap/ → C5. Crea ART-04 + auto-transición→PRODUCCION. Pre: ART-01+02+03 exist. Response: 201, events=[sap.confirmed, expediente.state_changed] (FIX-5).

C5 implementa transición automática según §J: dentro del handler, después de crear ART-04, evalúa can_transition_to(PRODUCCION) y si true, transiciona dentro de la misma transaction.atomic().

### Item 4: Endpoints PRODUCCION + PREPARACION (C6-C10)

Agente: AG-02 API Builder.
Precondiciones: Item 3 aprobado.

Endpoints:
- POST .../confirm-production/ → C6. Transición→PREPARACION. Response: 200.
- POST .../register-shipment/ → C7. Crea ART-05. Side effect Sprint 1: solo persiste credit_clock_started_at si rule=on_shipment (FIX-3). No Celery, no Beat. Response: 201.
- POST .../register-freight-quote/ → C8. Crea ART-06. Pre: ART-05 exists. Response: 201.
- POST .../register-customs/ → C9. Crea ART-08. Pre: dispatch_mode=mwt, ART-05+06 exist. Response: 201.
- POST .../approve-dispatch/ → C10. Gate final. Crea ART-07 + transición→DESPACHO. Pre: ART-05+06 exist, (ART-08 SI dispatch_mode=mwt). Response: 201, events=[dispatch.approved, expediente.state_changed] (FIX-5).

Regla de orden PREPARACION: C7→C8→C9→C10 (mwt) o C7→C8→C10 (client). C10 es siempre gate.

### Item 5: Endpoints DESPACHO→CERRADO + Pagos (C11-C14, C21)

Agente: AG-02 API Builder.
Precondiciones: Item 4 aprobado.

Endpoints:
- POST .../confirm-departure/ → C11. Transición→TRANSITO. Response: 200.
- POST .../confirm-arrival/ → C12. Transición→EN_DESTINO. Response: 200.
- POST .../issue-invoice/ → C13. Crea ART-09. Response: 201.
- POST .../register-payment/ → C21. Crea PaymentLine + actualiza payment_status. Regla acumulación §L3: SUM(payments) >= invoice_total → paid. Sobrepago permitido §M. Response: 201.
- POST .../close/ → C14. Transición→CERRADO. Pre: ART-09 exists + payment_status=paid + is_blocked=false. Response: 200.

C21 calcula amount_paid_total después de insertar PaymentLine y actualiza payment_status automáticamente (pending→partial→paid).

### Item 6: Endpoints Costos + Cancel + Block (C15-C18)

Agente: AG-02 API Builder.
Precondiciones: Item 3 aprobado (C15 puede ejecutarse desde REGISTRO).

Endpoints:
- POST .../register-cost/ → C15. CostLine append-only. Pre: status ≠ CERRADO, ≠ CANCELADO. Response: 201.
- POST .../cancel/ → C16. Transición→CANCELADO. CEO only. Pre: status ∈ {REGISTRO, PRODUCCION, PREPARACION}. Cancelación ignora bloqueo (§C3). NO usa EnsureNotBlocked (FIX-8). Response: 200.
- POST .../block/ → C17. Sets is_blocked=true + 4 campos. Pre: is_blocked=false. NO usa EnsureNotBlocked (FIX-8). Response: 200.
- POST .../unblock/ → C18. Clears bloqueo. CEO only. Historia en event_log. NO usa EnsureNotBlocked (FIX-8). Response: 200.

### Item 7: URL Registry

Agente: AG-02 API Builder.
Precondiciones: Items 3-6 implementados.

Consolidar todas las URLs bajo /api/expedientes/. Registrar en config/urls.py. Verificar que todos los endpoints usan `{pk}` como lookup.

### Item 8: Tests de transición (spec-based)

Agente: AG-06 QA.
Precondición: Item 2 aprobado (necesita importar services.py).

Archivos permitidos: tests/test_transitions.py, tests/factories.py.
Archivos prohibidos: apps/*, docker-compose.yml.

Criterios de done:
- ExpedienteFactory con status configurable + artifacts opcionales
- Test happy path: REGISTRO→...→CERRADO (7 transiciones)
- Test cada transición prohibida de §B3
- Test cancelación desde 3 estados permitidos + 4 prohibidos
- Test bloqueo impide transición
- Test desbloqueo restaura

### Item 9: Tests de commands (API-based)

Agente: AG-06 QA.
Precondiciones: Items 3-6 aprobados.

Archivos permitidos: tests/test_commands.py, tests/test_permissions.py, tests/conftest.py.
Archivos prohibidos: apps/*, docker-compose.yml.

Criterios de done:
- Test cada command (C1-C18, C21): happy path + precondiciones que fallan
- Test C5 y C10: auto-transición + 2 eventos en response (FIX-5)
- Test C14: falla si payment_status ≠ paid
- Test C10 como gate: falla sin ART-05+06, o sin ART-08 si dispatch_mode=mwt
- Test permissions: C4, C16, C18 CEO only
- Test is_blocked: commands operativos fallan si bloqueado
- Test atomicidad (3 casos): command sin transición, command con transición, ledger — monkeypatch para verificar rollback
- Test C21: acumulación payments, sobrepago, transitions pending→partial→paid
- Test response format: verificar `{"expediente": {...}, "events": [...]}` en al menos 1 command normal y 1 con auto-transición (FIX-1)
- Test EnsureNotBlocked bypass: C16 OK bloqueado, C18 OK bloqueado, operativos fallan bloqueado (FIX-8)
- Test credit clock: C1 on_creation persiste, C7 on_shipment persiste, C1 on_shipment no persiste (FIX-3)

## 3.3 Dependencias y handoffs

### Handoff interno AG-02: Serializers → Domain → Endpoints

La cadena 1A → 1B → 2 → 3 → 4/5/6 → 7 es estrictamente secuencial dentro del mismo agente. Cada item se aprueba individualmente antes de avanzar.

Item 2 (domain logic) es el más crítico. Si services.py está mal, todos los endpoints (Items 3-6) heredan el error. CEO debe revisar services.py contra la state machine campo por campo antes de aprobar.

### Handoff AG-02 → AG-06: Endpoints → Tests

AG-06 arranca Item 8 cuando Item 2 está aprobado (necesita services.py real, no mocks inventados).

Item 9 (tests de commands) requiere que todos los endpoints (Items 3-6) estén aprobados y funcionales.

### Regla de aprobación

CEO aprueba items individuales. Sprint 1 solo se marca DONE cuando los 10 items estén aprobados. Si un item falla, solo los que dependen directamente se bloquean.

## 3.4 Riesgos de ejecución

### Riesgo 1: AG-02 inventa reglas de negocio en services.py

Causa: services.py es donde vive la lógica de dominio. El agente puede "mejorar" la spec.
Impacto: lógica de negocio diverge de la state machine FROZEN, tests pasan contra implementación incorrecta.
Mitigación: CEO verifica services.py contra §B (transiciones), §F (commands), §J (auto-transiciones), §C (bloqueo). Cada precondición debe ser trazable a la spec. Si hay algo extra, rechazar.

### Riesgo 2: Mezcla de capas (domain logic en views, validación en models)

Causa: es tentador poner lógica en views.py o en models.py en vez de services.py.
Impacto: Sprint 2+ tiene que refactorizar para mover lógica al lugar correcto.
Mitigación: views.py debe ser thin — solo deserializa, llama a services, serializa respuesta. models.py no tiene métodos de negocio (eso quedó en Sprint 0). permissions.py delega a services.

### Riesgo 3: Transiciones automáticas (C5, C10) mal implementadas

Causa: la auto-transición debe ocurrir DENTRO del handler, no en signal/job/event.
Impacto: estado inconsistente — artifact creado pero transición no ocurrió, o viceversa.
Mitigación: verificar que can_transition_to() + transition + segundo event_log se ejecutan dentro del mismo transaction.atomic() que el insert del artifact. C5 y C10 deben producir 2 eventos (FIX-5).

### Riesgo 4: Tests pasan pero no cubren lo importante

Causa: AG-06 puede crear tests que pasan pero no verifican las precondiciones críticas.
Impacto: falsa sensación de cobertura.
Mitigación: Item 9 tiene criterios explícitos: test atomicidad con monkeypatch, test gate C10, test payment acumulación, test permissions CEO only, test response format (FIX-1). CEO verifica que cada criterio tiene al menos un test.

### Riesgo 5: C21 (RegisterPayment) con lógica de acumulación incorrecta

Causa: la regla SUM(payments) >= invoice_total → paid tiene edge cases (sobrepago, moneda distinta).
Impacto: expedientes que no se pueden cerrar, o que se cierran con payment incorrecto.
Mitigación: regla MVP §M es clara: 1 moneda por expediente, sobrepago permitido y marcado como paid. Si payment.currency ≠ ART-09.currency, el CEO ya convirtió antes de registrar. Tests deben cubrir: 0→pending, partial, exact→paid, over→paid.

### Riesgo 6: Credit clock side effects fuera de scope

Causa: C7 dice "inicia credit clock" en la state machine, pero Sprint 1 no tiene reloj automático.
Impacto: AG-02 puede crear Celery tasks o evaluar umbrales día 60/75/90.
Mitigación: FIX-3 congela que Sprint 1 solo persiste `credit_clock_started_at`. No computar, no alertar, no agendar.

## 3.5 Criterio de cierre de Sprint 1

Sprint 1 está DONE cuando:

1. 18 endpoints POST funcionales bajo /api/expedientes/
2. services.py con create_expediente, can_transition_to, can_execute_command, execute_command — contratos FIX-2 respetados
3. exceptions.py con 3 errores tipados
4. permissions.py con IsCEO, EnsureNotBlocked, EnsureCommandAllowed
5. Happy path completo verificable via API: crear expediente → registrar OC → proforma → decidir → SAP → producción → ... → cerrar
6. Cancelación funcional desde REGISTRO, PRODUCCION, PREPARACION
7. Bloqueo/desbloqueo funcional con historia en event_log
8. C21 payment acumulación funcional (pending→partial→paid)
9. Todos los tests de Items 8-9 passing
10. Tests de atomicidad passing (3 casos)
11. Response format `{"expediente": ..., "events": [...]}` en todos los endpoints (FIX-1)
12. C5 y C10 emiten 2 eventos (FIX-5)
13. C16/C17/C18 no usan EnsureNotBlocked (FIX-8)
14. credit_clock_started_at se persiste en C1 (on_creation) y C7 (on_shipment) (FIX-3+7)
15. Los 10 items aprobados con reportes §I, sin blockers abiertos

Lo que significa "Sprint 1 DONE":
- CEO puede operar expedientes reales via API + admin
- El ciclo completo REGISTRO→CERRADO funciona con artifacts, pagos y costos
- El outbox (EventLog) se llena correctamente (aunque no se consume aún)
- El sistema rechaza correctamente transiciones prohibidas, commands sin precondiciones, y operaciones en estados terminales

Lo que NO debe existir al cerrar Sprint 1:
- Frontend/UI (Sprint 3)
- Event consumers/dispatcher (Sprint 2)
- Reloj de crédito automático — solo el dato credit_clock_started_at (Sprint 2)
- C19/C20 (SupersedeArtifact, VoidArtifact — Sprint 2)
- ART-10 (Factura comisión) — post-MVP (FIX-4)
- ART-12 (Nota compensación) — post-MVP (FIX-4)
- Conectores externos
- RBAC formal (MVP = is_superuser)

---

# 4. PLAN OPERATIVO PARA ALE (Sprint 1)

## 4.1 Antes de arrancar

Confirmar que Sprint 0 está cerrado:
- Los 6 items de Sprint 0 DONE y aprobados
- `python manage.py migrate` y `python manage.py check` sin errores
- 6 modelos visibles en Django admin
- AppendOnlyModel verificado (CostLine y PaymentLine bloquean update/delete)

Verificar addendum FIX-7:
- ¿Existe `credit_clock_started_at` en modelo Expediente?
- Si NO → crear migración: `credit_clock_started_at = DateTimeField(null=True, blank=True, default=None)`
- Correr `python manage.py makemigrations` + `python manage.py migrate`
- Verificar campo visible en Django admin
- Este paso es PREVIO a Item 1A. No requiere aprobación de item — es addendum de compatibilidad.

Confirmar documentos FROZEN vigentes (mismos que Sprint 0 + LOTE_SM_SPRINT1):
- ENT_OPS_STATE_MACHINE v1.2.2 — FROZEN
- PLB_ORCHESTRATOR v1.2.2 — FROZEN
- LOTE_SM_SPRINT1 — FROZEN

Branch de trabajo: cada item en su branch (sprint1/item-1a-read-serializers, etc.). CEO mergea a main después de aprobar.

## 4.2 Interacción con Antigravity

Misma mecánica que Sprint 0: system prompt + prompt táctico del item. Un item a la vez.

Diferencia clave: Sprint 1 tiene un item crítico (Item 2 — domain logic) que requiere revisión más profunda. Para Item 2, Ale debe comparar services.py línea por línea contra la state machine. No basta con que "funcione" — debe funcionar por las razones correctas.

Para Items 3-6 (endpoints), la revisión es más mecánica: verificar que cada endpoint llama a services correctamente, que las URLs usan `{pk}`, que las respuestas son `{"expediente": ..., "events": [...]}` con el HTTP status correcto (FIX-1).

Para Items 8-9 (tests), verificar que cada criterio de done del LOTE tiene al menos un test que lo cubre.

## 4.3 Revisión de outputs

Orden de revisión por item:

Para Items 1A/1B (serializers): verificar que cada serializer mapea a los campos del modelo, que no hay campos inventados, que los write serializers cubren los inputs de §F1.

Para Item 2 (domain logic): REVISIÓN PROFUNDA.
- services.py: verificar can_transition_to retorna bool (FIX-2), can_execute_command raise-or-pass (FIX-2), execute_command retorna (expediente, events_list), auto-transiciones emiten 2 eventos (FIX-5), credit clock solo persiste dato (FIX-3)
- exceptions.py: 3 errores exactos, mapping a HTTP codes correcto
- permissions.py: thin layer, delega a services, EnsureNotBlocked excluye C16/C17/C18 (FIX-8)

Para Items 3-6 (endpoints): verificar patrón APIView (no ViewSet), URLs con `{pk}`, llamadas a services, transaction.atomic() en services, respuestas `{"expediente": ..., "events": [...]}`, HTTP status codes correctos (FIX-1).

Para Item 7 (URLs): verificar consolidación limpia, config/urls.py actualizado, todos usan `{pk}`.

Para Items 8-9 (tests): verificar cobertura de cada criterio del LOTE, especialmente atomicidad con monkeypatch, response format, 2 eventos en C5/C10, y bypass de EnsureNotBlocked.

## 4.4 Protocolo SPEC_GAP (FIX-6)

Si Antigravity reporta `[SPEC_GAP]` en cualquier item:

1. **No resolver.** Ale no tiene autoridad para decidir gaps de spec.
2. **No decir "asumí X".** Eso es exactamente lo que queremos evitar.
3. **Escalar al CEO** con: nombre del item + descripción textual del gap + texto exacto del reporte de Antigravity.
4. **CEO decide:** (a) resolver y re-despachar, o (b) declarar cosmético y autorizar continuar.
5. **Si afecta dominio → BLOCKED.** No continuar parcialmente con lógica inventada.

## 4.5 Branches y merges

```
main (Sprint 0 completo)
├── sprint1/item-1a-read-serializers
├── sprint1/item-1b-write-serializers
├── sprint1/item-2-domain-logic       ← REVISIÓN PROFUNDA
├── sprint1/item-3-registro-endpoints
├── sprint1/item-4-produccion-endpoints
├── sprint1/item-5-despacho-endpoints
├── sprint1/item-6-exception-endpoints
├── sprint1/item-7-url-registry
├── sprint1/item-8-tests-transitions   ← después de Item 2 aprobado
└── sprint1/item-9-tests-commands
```

## 4.6 Cuándo escalar

Escalar al CEO (Alvaro) cuando:
- Antigravity reporta [SPEC_GAP] (FIX-6)
- services.py tiene lógica no trazable a la spec
- Un command necesita un campo que no existe en el modelo (posible gap de Sprint 0)
- La regla de acumulación de pagos (C21) tiene un edge case no cubierto por §L3
- Los tests de atomicidad revelan que transaction.atomic() no cubre todo el handler
- Un endpoint necesita tocar models.py (fuera de scope AG-02)
- Antigravity intenta implementar ART-10, ART-12, C19, C20, o credit clock automático

## 4.7 Preparación Sprint 2

Antes de cerrar Sprint 1, verificar:
- Happy path completo via curl/httpie: C1→C2→C3→C4→C5→C6→C7→C8→C10→C11→C12→C13→C21→C14
- Cancelación: C1→C16 (desde REGISTRO)
- Bloqueo: C1→C17→(command falla)→C18→(command funciona)
- Todos los tests passing
- Outbox (EventLog) se llena correctamente con cada command
- Response format correcto en todos los endpoints
- C5 y C10 con 2 eventos
- credit_clock_started_at se persiste correctamente en C1 (on_creation) y C7 (on_shipment)
- No hay [SPEC_GAP] abiertos

Señales de que se puede abrir Sprint 2: el CEO puede operar expedientes reales via API sin encontrar errores, los tests de atomicidad pasan, el outbox tiene eventos correctos.

---

# 5. DOCUMENTO DE ARQUITECTURA DE APOYO (Sprint 1)

## 5.1 Patrón arquitectural

Sprint 1 introduce 3 capas nuevas sobre los modelos de Sprint 0:

```
┌──────────────────────────────────────────┐
│            views.py (thin)               │
│  APIView por command. Deserializa,       │
│  llama services, serializa respuesta.    │
│  Traduce exceptions → HTTP status codes. │
│  Response: {"expediente":..,"events":[]} │
└──────────────┬───────────────────────────┘
               │ llama
┌──────────────▼───────────────────────────┐
│           services.py (domain)           │
│  create_expediente → (exp, event)        │
│  can_transition_to → bool                │
│  can_execute_command → raise or pass     │
│  execute_command → (exp, events_list)    │
│  Todo dentro de transaction.atomic().    │
│  Fuente de verdad: state machine FROZEN. │
└──────────────┬───────────────────────────┘
               │ opera sobre
┌──────────────▼───────────────────────────┐
│          models.py (Sprint 0)            │
│  Expediente, LegalEntity, Artifact,      │
│  EventLog, CostLine, PaymentLine.        │
│  NO tiene lógica de negocio.             │
└──────────────────────────────────────────┘
```

Regla de capas:
- views.py NO tiene lógica de negocio
- services.py tiene TODA la lógica de dominio
- models.py NO tiene métodos de negocio (solo estructura de datos)
- permissions.py es thin wrapper que delega a services
- serializers.py solo valida estructura de input/output

## 5.2 Patrón de command endpoint

Cada command sigue este flujo:

```
Request POST /api/expedientes/{pk}/[command]/
  → View deserializa input con WriteSerializer
  → View llama services.can_execute_command(expediente, command, user)
  → Si falla → exception → HTTP 400/403/409
  → View llama services.execute_command(expediente, command, data, user)
    → Dentro de transaction.atomic():
      → Validar precondiciones
      → Mutar (insert artifact, update status, insert event_log)
      → Si auto-transición aplica: can_transition_to() + transition + 2do event_log
      → Si C7 + rule=on_shipment: persist credit_clock_started_at
  → View serializa respuesta con ReadSerializer
  → Response: {"expediente": ExpedienteSerializer, "events": [EventLogSerializer...]}
  → HTTP 200 o 201 según FIX-1
```

Excepción: C1 (CreateExpediente) usa create_expediente() directamente, no execute_command(), porque no hay expediente previo.

## 5.3 Fronteras de Sprint 1

SÍ entra:
- serializers.py (read + write)
- services.py (domain logic completa para 18 commands)
- exceptions.py (3 errores tipados)
- permissions.py (thin wrappers)
- views.py (18 APIViews)
- urls.py (18 rutas bajo /api/expedientes/)
- tests/ (transitions + commands + permissions + atomicidad + response format)

NO entra:
- Frontend / UI
- Event consumers / dispatcher (outbox write-only)
- Reloj de crédito automático (solo credit_clock_started_at)
- C19/C20 (SupersedeArtifact, VoidArtifact)
- ART-10 (Factura comisión) — post-MVP (FIX-4)
- ART-12 (Nota compensación) — post-MVP (FIX-4)
- Conectores externos
- RBAC formal

## 5.4 Riesgos técnicos

### config/settings/base.py en Sprint 1

AG-02 no debería necesitar tocar settings. Si DRF no está instalado, es un gap de Sprint 0 (debería estar en INSTALLED_APPS). Si AG-02 necesita agregar DRF a settings, debe declararlo en "Decisiones asumidas".

### Transición automática y atomicidad

Las auto-transiciones (C5→PRODUCCION, C10→DESPACHO) deben ocurrir dentro del mismo transaction.atomic() que el insert del artifact. Si se implementan fuera (signal, celery task), el sistema pierde consistencia. Ambos commands emiten 2 eventos. Verificar esto explícitamente en code review.

### event_log.emitted_by

Cada EventLog debe incluir emitted_by con el formato "CX:CommandName" (ej: "C5:RegisterSAPConfirmation"). Esto es trazabilidad, no decoración. Si falta, el outbox pierde utilidad para Sprint 2.

---

Stamp vigente: APROBADO por CEO el 2026-02-26 23:59
Vencimiento: 2026-05-27 (stamp + 90 días)
Estado: VIGENTE
Aprobador final: CEO (actualmente: Alvaro)
