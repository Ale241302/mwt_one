# LOTE_SM_SPRINT1 — Command Handlers + Tests
sprint: 1
priority: P0
depends_on: LOTE_SM_SPRINT0 (todos los items aprobados)
refs: ENT_OPS_STATE_MACHINE (FROZEN), PLB_ORCHESTRATOR v1.2.2 (FROZEN)
status: DONE — CERRADO · 9/9 items · 0 pendientes

---

## Scope Sprint 1

**Incluido:** Commands C1–C14 (happy path completo REGISTRO→CERRADO) + C15 (CostLine) + C16–C18 (cancelación y bloqueo) + C21 (pagos). Total: 18 commands.

**Excluido de Sprint 1:**
- C19 SupersedeArtifact — corrección de artifacts, post-MVP
- C20 VoidArtifact — anulación fiscal, post-MVP
- Frontend (sin UI; CEO opera via Django Admin + API directa)
- Conectores externos (fiscal, notificaciones push)
- Reloj de crédito automático (alertas día 60/75/90 — Sprint 2)
- Event consumers (outbox write-only en Sprint 1; sin dispatcher ni consumers)

**Patrón de endpoints:** `APIView` / `GenericAPIView` por command. Este sistema es command-heavy, no CRUD-first. Cada command = 1 endpoint POST dedicado. No usar ViewSet + @action.

---

## Items

### Item 1A: Read Serializers
- **Agente:** AG-02 API Builder
- **Dependencia previa:** LOTE_SM_SPRINT0 Items 2-4B aprobados (modelos estables)
- **Archivos a tocar:** `apps/expedientes/serializers.py`
- **Archivos prohibidos:** models.py, tests/, docker-compose.yml
- **Criterio de done:**
  - [ ] ExpedienteSerializer (read — status display, is_blocked, payment_status, timestamps)
  - [ ] ArtifactInstanceSerializer (read — type, status, payload summary)
  - [ ] CostLineSerializer (read)
  - [ ] PaymentLineSerializer (read)
  - [ ] EventLogSerializer (read-only, para timeline del expediente)

---

### Item 1B: Write Serializers por Command
- **Agente:** AG-02 API Builder
- **Dependencia previa:** Item 1A
- **Archivos a tocar:** `apps/expedientes/serializers.py` (extend)
- **Archivos prohibidos:** models.py, tests/
- **Criterio de done:**
  - [ ] ExpedienteCreateSerializer (C1 — brand, client_id, mode, freight_mode, transport_mode, dispatch_mode, price_basis, credit_clock_start_rule optional)
  - [ ] RegisterCostSerializer (C15 — cost_type, amount, currency, phase, description)
  - [ ] RegisterPaymentSerializer (C21 — amount, currency, method, reference)
  - [ ] Serializers de commands con artifact payload (C2-C10): inline o dedicados según complejidad. Mínimo: validación de inputs requeridos por cada command.

---

### Item 2: Domain Logic + API Guards
- **Agente:** AG-02 API Builder
- **Dependencia previa:** Item 1B
- **Archivos a tocar:** `apps/expedientes/services.py` (domain logic), `apps/expedientes/permissions.py` (HTTP guards)
- **Archivos prohibidos:** models.py, tests/
- **Criterio de done:**
  - [ ] `apps/expedientes/services.py` — capa de dominio:
    - `create_expediente(data, user)` — handler específico para C1 (no existe expediente previo). Retorna expediente creado. Corre dentro de `transaction.atomic()`.
    - `can_transition_to(expediente, target_state)` — evalúa: (1) estado actual válido, (2) is_blocked==false, (3) artefactos requeridos completados, (4) policy checks (dispatch_mode, payment_status). Ref: state machine §B + §F
    - `can_execute_command(expediente, command_name, user)` — combina precondiciones del command + permisos. Para C2–C18, C21.
    - `execute_command(expediente, command_name, data, user)` — orquesta: validar → mutar → event_log → side effects. Todo dentro de `transaction.atomic()`. Para C2–C18, C21.
  - [ ] `apps/expedientes/exceptions.py` — errores de dominio tipados:
    - `CommandValidationError` — input inválido o precondición no cumplida
    - `TransitionNotAllowedError` — transición prohibida por estado/bloqueo
    - `ArtifactMissingError` — artefacto requerido no existe
    - Views traducen: `CommandValidationError` → 400, `TransitionNotAllowedError` → 409, `ArtifactMissingError` → 409, DRF `PermissionDenied` → 403
  - [ ] `apps/expedientes/permissions.py` — wrappers HTTP (thin layer):
    - `IsCEO` permission (MVP: is_superuser)
    - `EnsureNotBlocked` — delega a services
    - `EnsureCommandAllowed` — delega a services
  - [ ] Guards devuelven errores descriptivos (qué falta, no solo "prohibido")

---

### Item 3: Command Endpoints — REGISTRO (C1–C5)
- **Agente:** AG-02 API Builder
- **Dependencia previa:** Items 1A + 1B + 2
- **Command ref:** State machine §F, C1–C5
- **Archivos a tocar:** `apps/expedientes/views.py`, `apps/expedientes/urls.py`
- **Archivos prohibidos:** models.py, tests/
- **Criterio de done:**
  - [ ] `POST /api/expedientes/` → C1 CreateExpediente. Crea expediente + event_log. Retorna expediente con status=REGISTRO.
  - [ ] `POST /api/expedientes/{id}/register-oc/` → C2 RegisterOC. Crea ART-01 + event_log. Precondición: status=REGISTRO, is_blocked=false.
  - [ ] `POST /api/expedientes/{id}/create-proforma/` → C3 CreateProforma. Crea ART-02 + event_log. Precondición: status=REGISTRO, ART-01 exists.
  - [ ] `POST /api/expedientes/{id}/decide-mode/` → C4 DecideModeBC. Crea ART-03 + event_log. Precondición: status=REGISTRO, ART-02 exists, CEO only.
  - [ ] `POST /api/expedientes/{id}/confirm-sap/` → C5 RegisterSAPConfirmation. Crea ART-04 + transición auto→PRODUCCION + event_log. Precondición: status=REGISTRO, ART-01+02+03 exist.
  - [ ] C1 usa `create_expediente()` de services.py; C2–C5 usan `can_execute_command()` + `execute_command()`
  - [ ] Todas las mutaciones dentro de `transaction.atomic()`
  - [ ] Respuestas incluyen expediente actualizado + evento creado

---

### Item 4: Command Endpoints — PRODUCCION + PREPARACION (C6–C10)
- **Agente:** AG-02 API Builder
- **Dependencia previa:** Item 3
- **Command ref:** State machine §F, C6–C10
- **Archivos a tocar:** `apps/expedientes/views.py` (extend), `apps/expedientes/urls.py` (extend)
- **Archivos prohibidos:** models.py, tests/
- **Criterio de done:**
  - [ ] `POST /api/expedientes/{id}/confirm-production/` → C6. Transición→PREPARACION. Precondición: status=PRODUCCION, is_blocked=false.
  - [ ] `POST /api/expedientes/{id}/register-shipment/` → C7. Crea ART-05 + event_log. Side effect: inicia credit clock si rule=on_shipment. Precondición: status=PREPARACION, is_blocked=false.
  - [ ] `POST /api/expedientes/{id}/register-freight-quote/` → C8. Crea ART-06. Precondición: status=PREPARACION, ART-05 exists.
  - [ ] `POST /api/expedientes/{id}/register-customs/` → C9. Crea ART-08. Precondición: status=PREPARACION, dispatch_mode=mwt, ART-05+06 exist.
  - [ ] `POST /api/expedientes/{id}/approve-dispatch/` → C10 (gate final). Crea ART-07 + transición→DESPACHO. Precondición: ART-05+06 exist, (ART-08 SI dispatch_mode=mwt), is_blocked=false.
  - [ ] Regla de orden PREPARACION respetada: C7→C8→C9→C10 (o C7→C8→C10 si dispatch_mode=client)
  - [ ] Todas las mutaciones atómicas

---

### Item 5: Command Endpoints — DESPACHO→CERRADO (C11–C14) + Pagos (C21)
- **Agente:** AG-02 API Builder
- **Dependencia previa:** Item 4
- **Command ref:** State machine §F, C11–C14, C21, §L
- **Archivos a tocar:** `apps/expedientes/views.py` (extend), `apps/expedientes/urls.py` (extend)
- **Archivos prohibidos:** models.py, tests/
- **Criterio de done:**
  - [ ] `POST /api/expedientes/{id}/confirm-departure/` → C11. Transición→TRANSITO.
  - [ ] `POST /api/expedientes/{id}/confirm-arrival/` → C12. Transición→EN_DESTINO.
  - [ ] `POST /api/expedientes/{id}/issue-invoice/` → C13. Crea ART-09 + event_log.
  - [ ] `POST /api/expedientes/{id}/register-payment/` → C21. Crea PaymentLine + actualiza payment_status + payment_registered_at/by. Regla acumulación §L3: SUM >= invoice_total → paid. Sobrepago permitido (§M regla MVP).
  - [ ] `POST /api/expedientes/{id}/close/` → C14. Transición→CERRADO. Precondición: ART-09 exists + payment_status=paid + is_blocked=false.
  - [ ] Todas las mutaciones atómicas

---

### Item 6: Command Endpoints — Costos + Cancelación + Bloqueo (C15–C18)
- **Agente:** AG-02 API Builder
- **Dependencia previa:** Item 3 (C15 puede ejecutarse desde REGISTRO)
- **Command ref:** State machine §F, C15–C18
- **Archivos a tocar:** `apps/expedientes/views.py` (extend), `apps/expedientes/urls.py` (extend)
- **Archivos prohibidos:** models.py, tests/
- **Criterio de done:**
  - [ ] `POST /api/expedientes/{id}/register-cost/` → C15. Crea CostLine (append-only). Precondición: status ≠ CERRADO, status ≠ CANCELADO.
  - [ ] `POST /api/expedientes/{id}/cancel/` → C16. Transición→CANCELADO. CEO only. Precondición: status ∈ {REGISTRO, PRODUCCION, PREPARACION}.
  - [ ] `POST /api/expedientes/{id}/block/` → C17. Sets is_blocked=true + blocked_reason/at/by. Precondición: is_blocked=false.
  - [ ] `POST /api/expedientes/{id}/unblock/` → C18. Clears is_blocked + campos bloqueo. CEO only. History en event_log.
  - [ ] Todas las mutaciones atómicas

---

### Item 7: URL Registry + Router config
- **Agente:** AG-02 API Builder
- **Dependencia previa:** Items 3-6 implementados con rutas definidas (puede consolidar incrementalmente)
- **Archivos a tocar:** `apps/expedientes/urls.py` (consolidar), `config/urls.py` (registrar)
- **Archivos prohibidos:** models.py, tests/
- **Criterio de done:**
  - [ ] Todos los endpoints registrados bajo `/api/expedientes/`
  - [ ] URL patterns limpios y consistentes
  - [ ] `config/urls.py` incluye `expedientes.urls`

---

### Item 8: Tests de transición (spec-based)
- **Agente:** AG-06 QA
- **Dependencia previa:** Puede iniciar en modo anticipado (👁) contra state machine congelada. Escritura completa después de Item 3 aprobado.
- **Command ref:** State machine §B (transiciones), §A (estados)
- **Archivos a tocar:** `tests/test_transitions.py`, `tests/factories.py`
- **Archivos prohibidos:** apps/*, docker-compose.yml
- **Criterio de done:**
  - [ ] Factory: `ExpedienteFactory` con status configurable + artifacts opcionales
  - [ ] Test happy path completo: REGISTRO→PRODUCCION→PREPARACION→DESPACHO→TRANSITO→EN_DESTINO→CERRADO (7 transiciones)
  - [ ] Test cada transición prohibida definida en state machine §B3: cada una debe fallar con error descriptivo
  - [ ] Test cancelación desde REGISTRO, PRODUCCION, PREPARACION (3 allowed)
  - [ ] Test cancelación desde DESPACHO, TRANSITO, EN_DESTINO, CERRADO (4 prohibited — must fail)
  - [ ] Test bloqueo impide cualquier transición
  - [ ] Test desbloqueo restaura capacidad de transición

---

### Item 9: Tests de commands (API-based)
- **Agente:** AG-06 QA
- **Dependencia previa:** Items 3-6 aprobados (endpoints estables)
- **Command ref:** State machine §F (C1–C18, C21)
- **Archivos a tocar:** `tests/test_commands.py`, `tests/test_permissions.py`, `tests/conftest.py`
- **Archivos prohibidos:** apps/*, docker-compose.yml
- **Criterio de done:**
  - [ ] Test C1: crear expediente retorna status=REGISTRO + campos inicializados (credit_clock_start_rule, is_blocked=false, payment_status=pending)
  - [ ] Test C2-C4: cada command crea artifact correcto + valida precondiciones (falla si artifact previo no existe)
  - [ ] Test C5: crea ART-04 + auto-transition a PRODUCCION
  - [ ] Test C6-C10: cada command valida precondiciones + transición correcta. Test C10 como gate (falla sin ART-05+06, o sin ART-08 si dispatch_mode=mwt)
  - [ ] Test C11-C14: flujo DESPACHO→CERRADO + C14 falla si payment_status ≠ paid
  - [ ] Test C15: CostLine append-only + falla en status CERRADO/CANCELADO
  - [ ] Test C16: cancelación CEO only + falla si status ∈ {DESPACHO, TRANSITO, EN_DESTINO}
  - [ ] Test C17/C18: block/unblock cycle + history en event_log
  - [ ] Test C21: payment acumulación + sobrepago + payment_status transitions (pending→partial→paid)
  - [ ] Test permissions: C4 (CEO only), C16 (CEO only), C18 (CEO only) — fail si no superuser
  - [ ] Test is_blocked: cualquier command operativo falla si expediente bloqueado
  - [ ] Test atomicidad (mecanismo explícito, 3 casos):
    - **C2 (command sin transición):** monkeypatch `ArtifactInstance.objects.create` → verificar no persiste event_log ni artifact
    - **C5 (command con transición):** monkeypatch fallo en artifact → verificar status sigue REGISTRO, no event_log, no artifact
    - **C15 o C21 (ledger append-only):** monkeypatch fallo en CostLine/PaymentLine create → verificar no persiste event_log ni cambio en payment_status

---

## Dependencias entre items (resumen visual)

```
LOTE_SM_SPRINT0 (aprobado)
    │
    ├── Item 1A: Read Serializers
    │       │
    │       └── Item 1B: Write Serializers
    │               │
    │               └── Item 2: Domain Logic (services.py) + API Guards (permissions.py)
    │                       │
    │                       ├── Item 3: Endpoints REGISTRO (C1-C5)
    │                       │       │
    │                       │       ├── Item 4: Endpoints PRODUCCION+PREPARACION (C6-C10)
    │                       │       │       │
    │                       │       │       └── Item 5: Endpoints DESPACHO→CERRADO (C11-C14, C21)
    │                       │       │
    │                       │       └── Item 6: Endpoints Costos+Cancel+Block (C15-C18)
    │                       │
    │                       └── Item 7: URL Registry (después de Items 3-6 implementados)
    │
    ├── Item 8: Tests transición (👁 anticipado contra spec, write después de Item 3)
    │
    └── Item 9: Tests commands (después de Items 3-6 aprobados)
```

---

## Qué queda explícitamente fuera de Sprint 1

| Feature | Por qué | Cuándo |
|---------|---------|--------|
| C19 SupersedeArtifact | Corrección artifacts — no happy path | Sprint 2 |
| C20 VoidArtifact | Anulación fiscal — no MVP | Sprint 2 |
| Frontend / UI | CEO usa Django Admin + API | Sprint 3 |
| Reloj crédito automático (alertas) | Necesita Celery Beat + event consumers | Sprint 2 |
| Event consumers (outbox → acciones) | Outbox se llena pero no se consume | Sprint 2 |
| Notificaciones push | Side effects async — manual en MVP | Sprint 2+ |
| Conector fiscal (FacturaProfesional) | Pendiente BIZ Z5 | Post-MVP |
| Multi-moneda real | MVP = 1 moneda por expediente | Post-MVP |
| RBAC formal | MVP = is_superuser | Post-MVP |

---

Stamp: DONE — CERRADO · 9/9 items · 0 pendientes · Confirmado auditoría 2026-03-12
Tareas pasadas: ninguna.
Origen: Derivado de ENT_OPS_STATE_MACHINE (FROZEN) + PLB_ORCHESTRATOR v1.2.2 (FROZEN) + 2 rondas audit ChatGPT
