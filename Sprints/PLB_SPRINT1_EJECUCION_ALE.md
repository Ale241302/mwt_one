# PLB_SPRINT1_EJECUCION_ALE — Plan Operativo Sprint 1 (Simplificado)
status: DRAFT
visibility: [INTERNAL]
domain: Plataforma (IDX_PLATAFORMA)
version: 1.0
tipo: Playbook (instrucción operativa)
refs: LOTE_SM_SPRINT1 (FROZEN), PLB_SPRINT1_EJECUCION v2.1 (FROZEN), PLB_SPRINT1_PROMPTS v2.1 (FROZEN), ENT_OPS_STATE_MACHINE v1.2.2 (FROZEN)
prerrequisito: Sprint 0 DONE (5 items aprobados, 6 contenedores, modelos en PostgreSQL)
nota: Este es un resumen operativo para Ale. Los prompts tácticos completos están en PLB_SPRINT1_PROMPTS v2.1.

---

# QUÉ ES SPRINT 1

Sprint 1 construye toda la API: 18 command handlers (endpoints) que permiten al CEO operar expedientes de importación desde REGISTRO hasta CERRADO, incluyendo cancelación, bloqueo, costos y pagos. Todo via API — sin UI.

Al terminar Sprint 1, el CEO puede hacer el flujo completo via API o herramientas como Postman:
- Crear expediente (C1)
- Registrar artefactos en cada etapa (C2-C10)
- Registrar costos (C15) y pagos (C21)
- Cancelar (C16), bloquear (C17), desbloquear (C18)
- Cerrar expediente (C14)

Cada operación emite eventos en el EventLog (outbox). El reloj de crédito solo se persiste (credit_clock_started_at), no se evalúa — eso es Sprint 2.

---

# ITEMS (10 items, 2 agentes)

## Visión general

```
Sprint 0 DONE
    │
    ├── Item 1A: Read Serializers (AG-02)
    │       │
    │       └── Item 1B: Write Serializers (AG-02)
    │               │
    │               └── Item 2: Domain Logic services.py + permissions.py (AG-02) ← ITEM CRÍTICO
    │                       │
    │                       ├── Item 3: Endpoints REGISTRO C1-C5 (AG-02)
    │                       │       │
    │                       │       ├── Item 4: Endpoints PRODUCCION+PREPARACION C6-C10 (AG-02)
    │                       │       │       │
    │                       │       │       └── Item 5: Endpoints DESPACHO→CERRADO C11-C14, C21 (AG-02)
    │                       │       │
    │                       │       └── Item 6: Endpoints Costos+Cancel+Block C15-C18 (AG-02)
    │                       │
    │                       └── Item 7: URL Registry (AG-02)
    │
    ├── Item 8: Tests transición (AG-06) — puede arrancar en paralelo contra spec
    │
    └── Item 9: Tests commands (AG-06) — después de Items 3-6
```

---

## Item 1A: Read Serializers

**Agente:** AG-02 API Builder
**Qué hace:** Serializers de lectura — cómo se ven Expediente, ArtifactInstance, CostLine, PaymentLine, EventLog cuando el sistema responde.

**Archivos:** apps/expedientes/serializers.py.
**Verificación:** El archivo importa sin errores.

---

## Item 1B: Write Serializers por Command

**Agente:** AG-02 API Builder
**Dependencia:** Item 1A.
**Qué hace:** Serializers de escritura — qué datos recibe cada command como input. ExpedienteCreateSerializer (C1), RegisterCostSerializer (C15), RegisterPaymentSerializer (C21), más serializers para cada command con artifact payload (C2-C10).

**Archivos:** apps/expedientes/serializers.py (extender).

---

## Item 2: Domain Logic + API Guards ⚠️ ITEM CRÍTICO

**Agente:** AG-02 API Builder
**Dependencia:** Item 1B.
**Qué hace:** El corazón del sistema — services.py con la lógica de dominio. 4 funciones principales:
- `create_expediente(data, user)` → (expediente, event)
- `can_transition_to(expediente, target_status)` → bool
- `can_execute_command(expediente, command, user)` → raise o pass
- `execute_command(expediente, command, data, user)` → (expediente, events_list)

Más permissions.py con 3 permissions: IsCEO, IsAuthenticated, EnsureNotBlocked.

**Archivos:** apps/expedientes/services.py, apps/expedientes/permissions.py, apps/expedientes/exceptions.py.

**⚠️ POR QUÉ ES CRÍTICO:** Todo el resto de los items (3-6) llaman a services.py. Si services.py tiene errores, toda la API falla. Ale debe pedir revisión profunda del CEO antes de avanzar a Item 3.

**Lo que Ale debe verificar con el CEO:**
- Los 4 contratos de funciones son correctos (FIX-2)
- transaction.atomic() en toda mutación
- Auto-transiciones C5/C10 emiten 2 eventos (FIX-5)
- EnsureNotBlocked excluye C16/C17/C18 (FIX-8)
- credit_clock_started_at solo se persiste, no se evalúa (FIX-3)
- event_log.emitted_by con formato "CX:CommandName" (§K)

---

## Item 3: Endpoints REGISTRO (C1-C5)

**Agente:** AG-02 API Builder
**Dependencia:** Item 2 aprobado.
**Qué hace:** 5 APIViews para los commands de la fase REGISTRO.

| Endpoint | Command | HTTP |
|----------|---------|------|
| POST /api/expedientes/ | C1 CreateExpediente | 201 |
| POST /api/expedientes/{pk}/register-oc/ | C2 RegisterOC | 201 |
| POST /api/expedientes/{pk}/register-proforma/ | C3 RegisterProforma | 201 |
| POST /api/expedientes/{pk}/confirm-sap/ | C4 ConfirmSAP | 201 |
| POST /api/expedientes/{pk}/approve-production/ | C5 ApproveProduction | 201 |

**Nota:** C5 tiene auto-transición (REGISTRO→PRODUCCION). Emite 2 eventos en el mismo atomic.

---

## Item 4: Endpoints PRODUCCION + PREPARACION (C6-C10)

**Agente:** AG-02 API Builder
**Dependencia:** Item 3 aprobado.

| Endpoint | Command | HTTP |
|----------|---------|------|
| POST /api/expedientes/{pk}/confirm-production/ | C6 ConfirmProduction | 200 |
| POST /api/expedientes/{pk}/register-shipment/ | C7 RegisterShipment | 201 |
| POST /api/expedientes/{pk}/register-freight-quote/ | C8 RegisterFreightQuote | 201 |
| POST /api/expedientes/{pk}/register-docs/ | C9 RegisterDocs | 201 |
| POST /api/expedientes/{pk}/approve-dispatch/ | C10 ApproveDispatch | 201 |

**Nota:** C10 tiene auto-transición (PREPARACION→DESPACHO). Emite 2 eventos.
**Nota:** C7 persiste credit_clock_started_at si credit_clock_start_rule=on_shipment (FIX-3).

---

## Item 5: Endpoints DESPACHO → CERRADO (C11-C14, C21)

**Agente:** AG-02 API Builder
**Dependencia:** Item 4 aprobado.

| Endpoint | Command | HTTP |
|----------|---------|------|
| POST /api/expedientes/{pk}/confirm-departure/ | C11 ConfirmDeparture | 200 |
| POST /api/expedientes/{pk}/confirm-arrival/ | C12 ConfirmArrival | 200 |
| POST /api/expedientes/{pk}/issue-invoice/ | C13 IssueInvoice | 201 |
| POST /api/expedientes/{pk}/register-payment/ | C21 RegisterPayment | 201 |
| POST /api/expedientes/{pk}/close/ | C14 CloseExpediente | 200 |

**Nota:** C21 acumula pagos: SUM(payments) >= total → payment_status=paid.
**Nota:** C14 solo ejecuta si payment_status=paid y ART-09 (factura) completed.

---

## Item 6: Endpoints Costos + Cancelación + Bloqueo (C15-C18)

**Agente:** AG-02 API Builder
**Dependencia:** Item 2 aprobado (puede correr en paralelo con Items 3-5).

| Endpoint | Command | HTTP | Nota |
|----------|---------|------|------|
| POST /api/expedientes/{pk}/register-cost/ | C15 RegisterCost | 201 | |
| POST /api/expedientes/{pk}/cancel/ | C16 CancelExpediente | 200 | CEO only, desde 3 estados |
| POST /api/expedientes/{pk}/block/ | C17 BlockExpediente | 200 | CEO only |
| POST /api/expedientes/{pk}/unblock/ | C18 UnblockExpediente | 200 | CEO only |

**Nota FIX-8:** C16, C17, C18 NO usan EnsureNotBlocked. Cancelación y bloqueo/desbloqueo ignoran el bloqueo.

---

## Item 7: URL Registry

**Agente:** AG-02 API Builder
**Dependencia:** Items 3-6 todos aprobados.
**Qué hace:** Registra todas las URLs en apps/expedientes/urls.py y verifica que config/urls.py las incluye. Verificar que no hay rutas para C19, C20 (Sprint 2).

**Verificación:**
```bash
docker-compose exec django python manage.py show_urls | grep expedientes
# Debe mostrar 18 rutas (no más, no menos)
```

---

## Item 8: Tests de Transición

**Agente:** AG-06 QA
**Dependencia:** Puede arrancar contra spec congelada; escribe después de Item 3 aprobado.
**Qué hace:** Tests de la state machine pura: happy path (7 transiciones REGISTRO→CERRADO), transiciones prohibidas (§B3), cancelación (3 permitidas + 4 prohibidas), bloqueo/desbloqueo.

**Archivos:** tests/test_transitions.py, tests/factories.py, tests/conftest.py.

---

## Item 9: Tests de Commands

**Agente:** AG-06 QA
**Dependencia:** Items 3-6 todos aprobados.
**Qué hace:** Tests de cada command individual: happy path + failure case. Tests de auto-transición C5/C10 (2 eventos), tests de permisos CEO-only, tests de bloqueo, tests de atomicidad, tests de response format, tests de credit_clock, tests de EnsureNotBlocked bypass (FIX-8).

**Archivos:** tests/test_commands.py.
**Total esperado:** ~30 tests.

---

# ORDEN DE EJECUCIÓN RECOMENDADO

```
Día 1-2:
  → Item 1A (Read Serializers) — rápido
  → Item 1B (Write Serializers) — secuencial

Día 2-3:
  → Item 2 (services.py) — ⚠️ CRÍTICO, tomarse el tiempo
  ✋ PAUSA: CEO revisa services.py antes de continuar

Día 3-5:
  → Item 3 (endpoints C1-C5) — primer batch de API
  → Item 6 (costos + cancelación C15-C18) — puede ir en paralelo con Item 4
  → Item 4 (endpoints C6-C10) — segundo batch
  → Item 5 (endpoints C11-C14, C21) — tercer batch

Día 5-6:
  → Item 7 (URL registry) — rápido
  → Item 8 (tests transición) — AG-06
  → Item 9 (tests commands) — AG-06

Día 7-8:
  → Revisión final: happy path completo C1→...→C14 via API
  → Todos los tests passing
```

**Tiempo realista:** 5-8 días (DRF tiene curva, Item 2 requiere revisión CEO).

---

# CADA ENDPOINT RETORNA ESTO (FIX-1)

```json
{
  "expediente": { ... serialized expediente ... },
  "events": [ ... lista de eventos emitidos ... ]
}
```

HTTP 201 para commands que crean recursos nuevos.
HTTP 200 para commands que modifican recursos existentes.

---

# QUÉ NO EXISTE EN SPRINT 1

- C19 SupersedeArtifact — Sprint 2
- C20 VoidArtifact — Sprint 2
- Frontend / UI — Sprint 3
- Reloj de crédito automático (evaluación) — Sprint 2 (Sprint 1 solo persiste credit_clock_started_at)
- Event consumers — Sprint 2 (outbox se llena pero no se consume)
- Notificaciones — Sprint 2+

---

# CUÁNDO ESCALAR AL CEO

- Item 2 terminado → SIEMPRE escalar para revisión de services.py
- Antigravity genera ViewSet en vez de APIView → corregir, no usar ViewSet
- Antigravity genera lógica en views.py → corregir, toda lógica va en services.py
- Antigravity crea campos que no existen en los modelos → escalar
- Tests fallan por motivos no claros → escalar
- Antigravity intenta crear C19, C20, notificaciones, dashboard → detener
- [SPEC_GAP] en cualquier item → escalar

---

# CRITERIO DE CIERRE SPRINT 1

Sprint 1 está DONE cuando:
1. 18 endpoints POST funcionales (20 URLs contando read)
2. Happy path completo: C1→C2→C3→C4→C5→C6→C7→C8→C9→C10→C11→C12→C13→C21→C14 funcional via API
3. Cancelación funcional: C16 desde REGISTRO, PRODUCCION, PREPARACION
4. Bloqueo/desbloqueo funcional: C17/C18
5. Costos: C15 registra, C21 acumula pagos
6. Todos los tests passing (Sprint 0 + Sprint 1)
7. 0 endpoints para C19, C20
8. manage.py check sin errores

---

Stamp: DRAFT — Pendiente aprobación CEO
