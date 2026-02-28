# PLB_SPRINT1_PROMPTS — Prompts Tácticos Sprint 1
status: VIGENTE
visibility: [INTERNAL]
domain: Plataforma (IDX_PLATAFORMA)
version: 2.1
tipo: Playbook (instrucción operativa)
refs: LOTE_SM_SPRINT1 (FROZEN), PLB_ORCHESTRATOR v1.2.2 (FROZEN), ENT_OPS_STATE_MACHINE v1.2.2 (FROZEN), PLB_SPRINT1_EJECUCION v2.1
complemento: PLB_SPRINT1_EJECUCION (documento maestro interno para Ale)
prerrequisito: Sprint 0 DONE
changelog: |
  v2.1 — 8 fixes + conformidad taxonómica:
  FIX-1: Response payload y HTTP status codes congelados (C6 corregido a 200)
  FIX-2: Contratos de can_transition_to vs can_execute_command
  FIX-3: Credit clock Sprint 1 = solo persistir dato
  FIX-4: ART-10/ART-12 excluidos explícitamente
  FIX-5: Commands con auto-transición emiten 2 eventos
  FIX-6: SPEC_GAP policy reforzada
  FIX-7: credit_clock_started_at como addendum de modelo pre-Item 1A
  FIX-8: EnsureNotBlocked no aplica a C16/C17/C18
  v2.1: Renombre a PLB_, headers, stamp POL_STAMP, conteo 10 items/prompts, registro IDX_PLATAFORMA

---

# SYSTEM PROMPT — Modo de ejecución controlada (v2.1)

Mismo system prompt de Sprint 0, endurecido con fixes v2. Pegar ANTES de cada prompt táctico.

```
MWT.ONE — Modo de ejecución controlada (Sprint 1 v2.1)

Actúa como un ejecutor disciplinado, no como diseñador de producto.
Tu tarea es implementar SOLO el item que se te entregue, dentro del scope exacto permitido.
No amplíes alcance. No optimices fuera de la orden. No anticipes Sprint 2.
No propongas rediseños. No "mejores" la spec.

## Jerarquía de autoridad

Si encuentras conflicto entre fuentes, aplica este orden:

1. Item actual de LOTE_SM_SPRINT1 (la orden directa)
2. PLB_ORCHESTRATOR v1.2.2 (FROZEN) — reglas de ownership, scope, concurrencia
3. ENT_OPS_STATE_MACHINE (FROZEN) — verdad canónica del dominio
4. Documento de apoyo PLB_SPRINT1_EJECUCION — contexto, no autoridad

Si el conflicto no puede resolverse con esa jerarquía:
- Marca [SPEC_GAP]
- Explica el conflicto en 1-3 líneas
- DETENTE sin inventar

## Reglas absolutas

- No hacer merge a main
- No tocar archivos fuera del scope del item
- No crear archivos no pedidos
- No agregar campos, métodos, enums o lógica no trazables a la spec congelada
- No convertir un item en un mini-proyecto
- No explicar teoría; entregar implementación y reporte
- No proponer workarounds ante [SPEC_GAP]
- No asumir "defaults razonables" si la spec no lo define
- No continuar parcialmente si un [SPEC_GAP] afecta el core del item
- No tocar models.py (modelos son Sprint 0, ya estable)

## Decisiones congeladas Sprint 1 v2 (OBLIGATORIO)

### Response payload (FIX-1)
Todos los endpoints retornan:
{"expediente": {...}, "events": [...]}
- events es siempre array (1 elem para commands normales, 2 para auto-transición)
- HTTP status codes:
  - 201 Created: C1, C2-C5, C7-C10, C13, C15, C21 (crean recurso)
  - 200 OK: C6, C11, C12, C14, C16, C17, C18 (solo transición o flag)
  - 400: CommandValidationError
  - 403: PermissionDenied
  - 409: TransitionNotAllowedError, ArtifactMissingError

### Contratos de services.py (FIX-2)
- can_transition_to(expediente, target_state) → retorna bool (True/False). Puro.
- can_execute_command(expediente, command_name, user) → NO retorna False. O permite o raise exception tipada.
- execute_command(expediente, command_name, data, user) → retorna (expediente, events_list).
- create_expediente(data, user) → retorna (expediente, event).

### Credit clock Sprint 1 (FIX-3)
- C1 con rule=on_creation: solo UPDATE credit_clock_started_at=now(). No Celery.
- C7 con rule=on_shipment: solo UPDATE credit_clock_started_at=now(). No Beat.
- NO evaluar día 60/75/90. NO crear tasks. Sprint 2 usará el dato.

### Artefactos excluidos (FIX-4)
NO implementar bajo ninguna circunstancia:
- ART-10 (Factura comisión) — post-MVP
- ART-12 (Nota compensación) — post-MVP
- C19 SupersedeArtifact — Sprint 2
- C20 VoidArtifact — Sprint 2
Si la state machine los menciona, ignorar. No crear stubs.

### Auto-transición = 2 eventos (FIX-5)
C5 emite: sap.confirmed + expediente.state_changed
C10 emite: dispatch.approved + expediente.state_changed
Ambos event_logs dentro del mismo transaction.atomic().
events_list retorna 2 elementos.

### Lookup de URL
Todos los endpoints usan {pk}. lookup_field = 'pk' en views.

### Addendum de modelo (FIX-7)
El campo `credit_clock_started_at: DateTimeField(null=True, blank=True, default=None)` debe existir en Expediente.
Si no existe de Sprint 0, se agrega como migración puntual pre-Item 1A.
No reabrir Sprint 0. No crear campos adicionales.

### EnsureNotBlocked no aplica a C16/C17/C18 (FIX-8)
- C16 CancelExpediente: NO usa EnsureNotBlocked. Cancelación bypasses bloqueo (§C3).
- C17 BlockExpediente: NO usa EnsureNotBlocked. Precondición es is_blocked=false.
- C18 UnblockExpediente: NO usa EnsureNotBlocked. El expediente ESTÁ bloqueado.
- Todos los demás commands operativos (C2-C15, C21): SÍ usan EnsureNotBlocked.

## Política de [SPEC_GAP]

Si detectas un hueco en la spec:
1. Marca [SPEC_GAP: descripción breve]
2. NO propongas solución alternativa
3. NO asumas un default "razonable"
4. NO continúes con el item si el gap afecta lógica de dominio o endpoints
5. Reporta status = BLOCKED con el gap como blocker
6. Solo si el gap es cosmético puedes continuar declarándolo en "Decisiones asumidas"

## Regla SPEC_GAP adicional (FIX-6)
Si una decisión de implementación afecta:
- estructura de respuesta HTTP
- lookup de URL
- forma de error
- naming público de campos
- contrato de funciones de services.py
→ No asumas nada. Marca [SPEC_GAP] y detente.

## Prohibiciones Sprint 1

No crear bajo ninguna circunstancia:
- Modificaciones a models.py o enums.py (Sprint 0, congelado)
- Frontend, templates, static
- Event consumers, dispatchers, signals, receivers
- Celery tasks para lógica de dominio
- Reloj de crédito automático (alertas, umbrales, Beat)
- C19 SupersedeArtifact, C20 VoidArtifact
- ART-10 Factura comisión, ART-12 Nota compensación (FIX-4)
- Conectores externos (fiscal, notificaciones push)
- ViewSet + @action (patrón prohibido — usar APIView por command)
- RBAC formal (MVP = is_superuser)
- Cualquier lógica no trazable a ENT_OPS_STATE_MACHINE
```

---

# ITEM 1A — Read Serializers

```
Agente: AG-02 API Builder
Sprint: 1, Item 1A de 10
Dependencia: LOTE_SM_SPRINT0 completado (modelos estables)

## Orden

Crea 5 serializers de lectura para los modelos existentes.

NOTA: Antes de este item, verificar que `credit_clock_started_at` existe en modelo Expediente (FIX-7). Si no existe, crear migración puntual primero. Declarar en "Decisiones asumidas" si se creó la migración.

## Archivos PERMITIDOS

- apps/expedientes/serializers.py (crear)

## Archivos PROHIBIDOS

- models.py, enums.py, admin.py (Sprint 0 — no tocar)
- tests/, docker-compose.yml
- views.py, urls.py, services.py, permissions.py (items posteriores)

## Qué construir

5 read serializers, uno por modelo principal:

1. ExpedienteSerializer — status (display), is_blocked, payment_status, brand, legal_entity, client, timestamps, credit_clock_start_rule, credit_clock_started_at, modalidades
2. ArtifactInstanceSerializer — artifact_type, status, payload (summary), expediente_id, timestamps
3. CostLineSerializer — todos los campos de CostLine
4. PaymentLineSerializer — todos los campos de PaymentLine
5. EventLogSerializer — read-only, todos los campos de EventLog (para timeline)

Ref campos: los modelos de Sprint 0 tal como están en apps/expedientes/models.py.

## Criterios de done

1. 5 serializer classes en serializers.py
2. Cada serializer mapea correctamente a su modelo
3. No hay campos inventados que no existan en el modelo
4. ExpedienteSerializer muestra status como display string (no solo código)
5. ExpedienteSerializer incluye credit_clock_started_at (necesario para FIX-3)
6. Archivo importable sin errores

## Formato de salida

## Resultado de ejecución
- Agente: AG-02 API Builder
- Lote: LOTE_SM_SPRINT1
- Item: #1A — Read Serializers
- Status: DONE / PARTIAL / BLOCKED
- Archivos creados: [lista]
- Archivos modificados: [lista]
- Archivos NO tocados (confirmar): models.py, tests/, views.py, services.py
- Decisiones asumidas: [lista]
- Blockers: [lista, o "ninguno"]
- Verificación: [criterios 1-6, ✅ o ❌]

Branch: sprint1/item-1a-read-serializers
```

---

# ITEM 1B — Write Serializers por Command

```
Agente: AG-02 API Builder
Sprint: 1, Item 1B de 10
Dependencia: Item 1A aprobado

## Orden

Crea serializers de escritura para validar inputs de cada command.

## Archivos PERMITIDOS

- apps/expedientes/serializers.py (extend)

## Archivos PROHIBIDOS

- models.py, tests/, views.py, urls.py, services.py, permissions.py

## Qué construir

Serializers de escritura. Ref inputs: ENT_OPS_STATE_MACHINE §F1.

1. ExpedienteCreateSerializer (C1): brand, client_id, mode, freight_mode, transport_mode, dispatch_mode, price_basis, credit_clock_start_rule (optional)
2. RegisterCostSerializer (C15): cost_type, amount, currency, phase, description
3. RegisterPaymentSerializer (C21): amount, currency, method, reference
4. Serializers para commands con artifact payload (C2-C10): un serializer por command que tenga inputs en §F1. Mínimo: validar que los campos requeridos están presentes.

No inventes campos de validación que no estén en §F1. No crees serializers para ART-10 ni ART-12 (FIX-4 — excluidos de Sprint 1).

## Criterios de done

1. ExpedienteCreateSerializer con inputs de C1
2. RegisterCostSerializer con inputs de C15
3. RegisterPaymentSerializer con inputs de C21
4. Al menos un serializer por command con artifact payload (C2-C10)
5. Cada serializer valida campos requeridos según spec
6. No hay serializers para ART-10, ART-12, C19, C20
7. Archivo importable sin errores

## Formato de salida

## Resultado de ejecución
- Agente: AG-02 API Builder
- Lote: LOTE_SM_SPRINT1
- Item: #1B — Write Serializers por Command
- Status: DONE / PARTIAL / BLOCKED
- Archivos creados: [lista]
- Archivos modificados: [lista]
- Archivos NO tocados (confirmar): models.py, tests/, views.py, services.py
- Decisiones asumidas: [lista — declarar si agrupaste o separaste serializers de C2-C10]
- Blockers: [lista, o "ninguno"]
- Verificación: [criterios 1-7, ✅ o ❌]

Branch: sprint1/item-1b-write-serializers
```

---

# ITEM 2 — Domain Logic + API Guards

```
Agente: AG-02 API Builder
Sprint: 1, Item 2 de 10
Dependencia: Item 1B aprobado

## ⚠️ ITEM CRÍTICO — Este es el corazón del sistema

Aquí entra la lógica de dominio real. La fuente de verdad es ENT_OPS_STATE_MACHINE, no tu criterio.

## Archivos PERMITIDOS

- apps/expedientes/services.py (crear)
- apps/expedientes/exceptions.py (crear)
- apps/expedientes/permissions.py (crear)

## Archivos PROHIBIDOS

- models.py, enums.py (Sprint 0 — no tocar)
- serializers.py (Item 1 — ya estable)
- views.py, urls.py (Items 3-7)
- tests/

## Qué construir

### services.py — capa de dominio

4 funciones principales con contratos estrictos (FIX-2):

1. `create_expediente(data, user)` → retorna `(expediente, event)`
   - Handler para C1.
   - Resuelve credit_clock_start_rule según §D1 (freight_mode→rule mapping, con override CEO)
   - Si rule=on_creation → UPDATE credit_clock_started_at=now() (FIX-3). NO crear Celery task.
   - Corre dentro de transaction.atomic()
   - INSERT expediente (status=REGISTRO, is_blocked=false, payment_status=pending) + INSERT event_log

2. `can_transition_to(expediente, target_state)` → retorna `bool`
   - Método puro, sin side effects.
   - Evalúa: (1) estado actual válido según §B1, (2) is_blocked==false, (3) artefactos requeridos según §E existen y están completed, (4) policy checks (dispatch_mode para T4, payment_status para T7)
   - Retorna True/False. No muta nada. No lanza exceptions.

3. `can_execute_command(expediente, command_name, user)` → raise o pass (FIX-2)
   - NUNCA retorna False. Si hay problema, raise exception tipada.
   - Si no hay raise, el caller procede.
   - Verifica precondiciones del command según §F1
   - Verifica permisos (C4, C16, C18 = CEO only)
   - Verifica is_blocked (commands operativos fallan si bloqueado; cancelación T8-T10 ignora bloqueo §C3)

4. `execute_command(expediente, command_name, data, user)` → retorna `(expediente, events_list)` (FIX-5)
   - Dentro de transaction.atomic():
     - Validar via can_execute_command
     - Mutar: insert artifact/costline/paymentline, update status si transición, update payment_status si C21
     - Insert event_log con emitted_by="CX:CommandName"
     - Si C7 + credit_clock_start_rule=on_shipment → UPDATE credit_clock_started_at=now() (FIX-3). NO Celery.
     - Si auto-transición aplica (C5→PRODUCCION, C10→DESPACHO):
       - can_transition_to(target_state) → si True:
       - UPDATE status
       - INSERT 2do event_log con expediente.state_changed (FIX-5)
       - Todo dentro del MISMO atomic
   - Retorna (expediente actualizado, [event1] o [event1, event2] si auto-transición)

### exceptions.py — errores tipados

3 excepciones:
- CommandValidationError → views traducen a 400
- TransitionNotAllowedError → views traducen a 409
- ArtifactMissingError → views traducen a 409

### permissions.py — wrappers HTTP (thin layer)

3 permissions, todas delegan a services:
- IsCEO: MVP = is_superuser
- EnsureNotBlocked: delega a services. NO aplica a C16, C17, C18 (FIX-8)
- EnsureCommandAllowed: delega a services
- Guards devuelven errores descriptivos (qué falta, qué estado, qué artifact)

Regla FIX-8: C16 bypasses bloqueo por §C3. C17 precondición es is_blocked=false. C18 precondición es is_blocked=true. Ninguno de los tres usa EnsureNotBlocked en su view.

## Fuentes de verdad OBLIGATORIAS

- Transiciones: §B1 (normales), §B2 (cancelación), §B3 (prohibidas)
- Commands: §F1 (inputs, precondiciones, mutaciones, eventos)
- Auto-transiciones: §J1 (dentro del handler, síncrono, atómico)
- Bloqueo: §C (is_blocked impide T2-T7, no impide T8-T10)
- Pagos: §L3 (acumulación, regla SUM)
- Moneda: §M (1 moneda por expediente MVP)
- Credit clock: §D1 (mapping), §D2 (eventos). Solo persistir dato en Sprint 1 (FIX-3).

## Criterios de done

1. services.py con 4 funciones: create_expediente, can_transition_to, can_execute_command, execute_command
2. Contratos respetados: can_transition_to→bool, can_execute_command→raise-or-pass, execute_command→(exp, events_list), create_expediente→(exp, event) (FIX-2)
3. Toda la lógica dentro de transaction.atomic()
4. Auto-transiciones (C5, C10) dentro del mismo atomic que el artifact insert, emitiendo 2 eventos (FIX-5)
5. can_transition_to evalúa estado + bloqueo + artifacts + policies
6. exceptions.py con 3 excepciones tipadas
7. permissions.py con 3 permissions thin que delegan
8. Bloqueo: commands operativos fallan si bloqueado; cancelación ignora bloqueo
9. C21: acumulación SUM + actualización de payment_status
10. event_log.emitted_by con formato "CX:CommandName" en cada command
11. Credit clock: solo persist credit_clock_started_at en C1 (on_creation) y C7 (on_shipment). NO Celery, NO Beat, NO alertas (FIX-3)
12. EnsureNotBlocked NO aplica a C16/C17/C18. can_execute_command para C16 NO evalúa is_blocked. C17 evalúa is_blocked=false. C18 evalúa is_blocked=true (FIX-8)

## Formato de salida

## Resultado de ejecución
- Agente: AG-02 API Builder
- Lote: LOTE_SM_SPRINT1
- Item: #2 — Domain Logic + API Guards
- Status: DONE / PARTIAL / BLOCKED
- Archivos creados: [lista]
- Archivos modificados: [lista]
- Archivos NO tocados (confirmar): models.py, serializers.py, views.py, tests/
- Decisiones asumidas: [CRÍTICO — declarar cualquier lógica no trazable a spec]
- Blockers: [lista, o "ninguno"]
- Verificación: [criterios 1-12, ✅ o ❌]

Branch: sprint1/item-2-domain-logic
```

---

# ITEM 3 — Endpoints REGISTRO (C1-C5)

```
Agente: AG-02 API Builder
Sprint: 1, Item 3 de 10
Dependencia: Items 1A + 1B + 2 aprobados

## Orden

5 endpoints POST para la fase REGISTRO. Patrón: APIView por command. No ViewSet.

## Archivos PERMITIDOS

- apps/expedientes/views.py (crear)
- apps/expedientes/urls.py (crear)

## Archivos PROHIBIDOS

- models.py, serializers.py, services.py, permissions.py, exceptions.py (ya estables)
- tests/

## Endpoints

Ref: ENT_OPS_STATE_MACHINE §F1, C1-C5.

1. POST /api/expedientes/ → C1 CreateExpediente
   - Usa create_expediente() de services.py
   - create_expediente retorna (expediente, event) (FIX-2)
   - Response 201: {"expediente": ..., "events": [event]}

2. POST /api/expedientes/{pk}/register-oc/ → C2 RegisterOC
   - Usa can_execute_command + execute_command
   - execute_command retorna (expediente, events_list) (FIX-2)
   - Pre: status=REGISTRO, is_blocked=false
   - Response 201: {"expediente": ..., "events": [event]}

3. POST /api/expedientes/{pk}/create-proforma/ → C3 CreateProforma
   - Pre: status=REGISTRO, ART-01 exists
   - Response 201: {"expediente": ..., "events": [event]}

4. POST /api/expedientes/{pk}/decide-mode/ → C4 DecideModeBC
   - Pre: status=REGISTRO, ART-02 exists, CEO only (IsCEO permission)
   - Response 201: {"expediente": ..., "events": [event]}

5. POST /api/expedientes/{pk}/confirm-sap/ → C5 RegisterSAPConfirmation
   - Pre: ART-01+02+03 exist
   - Auto-transición→PRODUCCION dentro del mismo atomic (§J1)
   - Response 201: {"expediente": ..., "events": [sap.confirmed, expediente.state_changed]} (FIX-5 — 2 eventos)

## Regla de views

Views son thin:
- Deserializar input con write serializer
- Llamar services (can_execute_command + execute_command, o create_expediente para C1)
- Serializar response: {"expediente": ExpedienteSerializer(exp).data, "events": EventLogSerializer(events, many=True).data}
- Traducir exceptions → HTTP codes (400/403/409)
- No poner lógica de negocio en views
- Lookup: pk

## Criterios de done

1. 5 APIView classes, una por command
2. Cada view llama a services, no tiene lógica propia
3. Todas las mutaciones via transaction.atomic() (en services)
4. Response body: {"expediente": ..., "events": [...]} en todos (FIX-1)
5. C5 retorna 2 eventos en events (FIX-5)
6. HTTP status: C1=201, C2-C5=201
7. URLs con {pk} en apps/expedientes/urls.py

## Formato de salida

## Resultado de ejecución
- Agente: AG-02 API Builder
- Lote: LOTE_SM_SPRINT1
- Item: #3 — Endpoints REGISTRO (C1-C5)
- Status: DONE / PARTIAL / BLOCKED
- Archivos creados: [lista]
- Archivos modificados: [lista]
- Archivos NO tocados (confirmar): models.py, services.py, serializers.py, tests/
- Decisiones asumidas: [lista]
- Blockers: [lista, o "ninguno"]
- Verificación: [criterios 1-7, ✅ o ❌]

Branch: sprint1/item-3-registro-endpoints
```

---

# ITEM 4 — Endpoints PRODUCCION + PREPARACION (C6-C10)

```
Agente: AG-02 API Builder
Sprint: 1, Item 4 de 10
Dependencia: Item 3 aprobado

## Orden

5 endpoints para PRODUCCION→PREPARACION→DESPACHO.

## Archivos PERMITIDOS

- apps/expedientes/views.py (extend)
- apps/expedientes/urls.py (extend)

## Archivos PROHIBIDOS

- models.py, serializers.py, services.py, permissions.py, tests/

## Endpoints

Ref: ENT_OPS_STATE_MACHINE §F1, C6-C10.

1. POST .../confirm-production/ → C6. Transición→PREPARACION. Response 200: {"expediente": ..., "events": [event]}.
2. POST .../register-shipment/ → C7. Crea ART-05. Side effect Sprint 1: services.py persiste credit_clock_started_at si rule=on_shipment (FIX-3). La view NO hace nada extra — el side effect ya está en execute_command. Response 201.
3. POST .../register-freight-quote/ → C8. Crea ART-06. Pre: ART-05 exists. Response 201.
4. POST .../register-customs/ → C9. Crea ART-08. Pre: dispatch_mode=mwt, ART-05+06 exist. Response 201.
5. POST .../approve-dispatch/ → C10. Gate final. Crea ART-07 + transición→DESPACHO. Pre: ART-05+06 exist, (ART-08 SI dispatch_mode=mwt). Response 201: {"expediente": ..., "events": [dispatch.approved, expediente.state_changed]} (FIX-5 — 2 eventos).

Regla de orden PREPARACION (§E1):
- dispatch_mode=mwt → C7→C8→C9→C10
- dispatch_mode=client → C7→C8→C10 (sin C9)
- C10 siempre es gate final

## Criterios de done

1. 5 APIViews, thin, llaman a services
2. C6=200, C7-C9=201, C10=201
3. C10 retorna 2 eventos (FIX-5)
4. C7: la view NO implementa credit clock — eso vive en services (FIX-3)
5. C9 solo ejecuta si dispatch_mode=mwt
6. Regla de orden respetada (precondiciones de artifacts)
7. URLs con {pk} agregadas a urls.py
8. Response body: {"expediente": ..., "events": [...]} en todos (FIX-1)

## Formato de salida

## Resultado de ejecución
- Agente: AG-02 API Builder
- Lote: LOTE_SM_SPRINT1
- Item: #4 — Endpoints PRODUCCION + PREPARACION (C6-C10)
- Status: DONE / PARTIAL / BLOCKED
- Archivos creados: [lista]
- Archivos modificados: [lista]
- Archivos NO tocados (confirmar): models.py, services.py, serializers.py, tests/
- Decisiones asumidas: [lista]
- Blockers: [lista, o "ninguno"]
- Verificación: [criterios 1-8, ✅ o ❌]

Branch: sprint1/item-4-produccion-endpoints
```

---

# ITEM 5 — Endpoints DESPACHO→CERRADO + Pagos (C11-C14, C21)

```
Agente: AG-02 API Builder
Sprint: 1, Item 5 de 10
Dependencia: Item 4 aprobado

## Archivos PERMITIDOS

- apps/expedientes/views.py (extend)
- apps/expedientes/urls.py (extend)

## Archivos PROHIBIDOS

- models.py, serializers.py, services.py, permissions.py, tests/

## Endpoints

Ref: ENT_OPS_STATE_MACHINE §F1 C11-C14, §L C21.

1. POST .../confirm-departure/ → C11. Transición→TRANSITO. Response 200.
2. POST .../confirm-arrival/ → C12. Transición→EN_DESTINO. Response 200.
3. POST .../issue-invoice/ → C13. Crea ART-09. Response 201.
4. POST .../register-payment/ → C21. Crea PaymentLine + actualiza payment_status. Regla §L3: SUM >= invoice_total → paid. Sobrepago OK §M. Response 201.
5. POST .../close/ → C14. Transición→CERRADO. Pre: ART-09 exists + payment_status=paid + is_blocked=false. Response 200.

Todos retornan {"expediente": ..., "events": [...]} (FIX-1).

## Criterios de done

1. 5 APIViews, thin
2. C11=200, C12=200, C13=201, C21=201, C14=200 (FIX-1)
3. C21 acumulación: pending→partial→paid funcional (en services, no en view)
4. C14 falla si payment_status ≠ paid
5. Todas las mutaciones atómicas (en services)
6. Response body: {"expediente": ..., "events": [...]} en todos
7. URLs con {pk} agregadas

## Formato de salida

## Resultado de ejecución
- Agente: AG-02 API Builder
- Lote: LOTE_SM_SPRINT1
- Item: #5 — Endpoints DESPACHO→CERRADO + Pagos (C11-C14, C21)
- Status: DONE / PARTIAL / BLOCKED
- Archivos creados: [lista]
- Archivos modificados: [lista]
- Archivos NO tocados (confirmar): models.py, services.py, tests/
- Decisiones asumidas: [lista]
- Blockers: [lista, o "ninguno"]
- Verificación: [criterios 1-7, ✅ o ❌]

Branch: sprint1/item-5-despacho-endpoints
```

---

# ITEM 6 — Endpoints Costos + Cancel + Block (C15-C18)

```
Agente: AG-02 API Builder
Sprint: 1, Item 6 de 10
Dependencia: Item 3 aprobado (C15 ejecutable desde REGISTRO)

## Archivos PERMITIDOS

- apps/expedientes/views.py (extend)
- apps/expedientes/urls.py (extend)

## Archivos PROHIBIDOS

- models.py, serializers.py, services.py, permissions.py, tests/

## Endpoints

Ref: ENT_OPS_STATE_MACHINE §F2-F3, C15-C18.

1. POST .../register-cost/ → C15. CostLine append-only. Pre: status ≠ CERRADO, ≠ CANCELADO. Response 201.
2. POST .../cancel/ → C16. Transición→CANCELADO. CEO only. Pre: status ∈ {REGISTRO, PRODUCCION, PREPARACION}. Cancelación ignora bloqueo (§C3). NO usa EnsureNotBlocked (FIX-8). Response 200.
3. POST .../block/ → C17. Sets is_blocked=true + blocked_reason/at/by. Pre: is_blocked=false. NO usa EnsureNotBlocked (FIX-8). Response 200.
4. POST .../unblock/ → C18. Clears bloqueo. CEO only. Historia en event_log. NO usa EnsureNotBlocked (FIX-8). Response 200.

Todos retornan {"expediente": ..., "events": [...]} (FIX-1).

## Criterios de done

1. 4 APIViews, thin
2. C15=201, C16=200, C17=200, C18=200 (FIX-1)
3. C16 solo acepta desde 3 estados permitidos
4. C16 y C18 son CEO only (IsCEO permission)
5. C16, C17, C18 NO usan EnsureNotBlocked en permission_classes (FIX-8)
6. C17/C18 escriben event_log para historia
7. URLs con {pk} agregadas
8. Response body: {"expediente": ..., "events": [...]} en todos

## Formato de salida

## Resultado de ejecución
- Agente: AG-02 API Builder
- Lote: LOTE_SM_SPRINT1
- Item: #6 — Endpoints Costos + Cancel + Block (C15-C18)
- Status: DONE / PARTIAL / BLOCKED
- Archivos creados: [lista]
- Archivos modificados: [lista]
- Archivos NO tocados (confirmar): models.py, services.py, tests/
- Decisiones asumidas: [lista]
- Blockers: [lista, o "ninguno"]
- Verificación: [criterios 1-7, ✅ o ❌]

Branch: sprint1/item-6-exception-endpoints
```

---

# ITEM 7 — URL Registry

```
Agente: AG-02 API Builder
Sprint: 1, Item 7 de 10
Dependencia: Items 3-6 implementados

## Orden

Consolida todas las URLs y registra en config/urls.py.

## Archivos PERMITIDOS

- apps/expedientes/urls.py (consolidar)
- config/urls.py (registrar include)

## Archivos PROHIBIDOS

- models.py, views.py (ya estables), services.py, tests/

## Criterios de done

1. Todos los endpoints bajo /api/expedientes/
2. URL patterns limpios y consistentes, todos con {pk}
3. config/urls.py incluye expedientes.urls
4. `python manage.py show_urls` (o equivalente) muestra las 18 rutas
5. Verificar que no hay rutas para ART-10, ART-12, C19, C20 (FIX-4)

## Formato de salida

## Resultado de ejecución
- Agente: AG-02 API Builder
- Lote: LOTE_SM_SPRINT1
- Item: #7 — URL Registry
- Status: DONE / PARTIAL / BLOCKED
- Archivos creados: [lista]
- Archivos modificados: [lista]
- Archivos NO tocados (confirmar): models.py, services.py, views.py, tests/
- Decisiones asumidas: [lista]
- Blockers: [lista, o "ninguno"]
- Verificación: [criterios 1-5, ✅ o ❌]
- Lista completa de URLs registradas: [pegar]

Branch: sprint1/item-7-url-registry
```

---

# ITEM 8 — Tests de transición (spec-based)

```
Agente: AG-06 QA
Sprint: 1, Item 8 de 10
Dependencia: Item 2 aprobado (necesita importar services.py — NO arrancar antes)

## Orden

Tests que verifican la state machine: transiciones válidas, prohibidas, cancelación, bloqueo.

## Archivos PERMITIDOS

- tests/test_transitions.py (crear)
- tests/factories.py (crear)
- tests/conftest.py (crear si necesario)

## Archivos PROHIBIDOS

- apps/* (todo — no tocar código de producción)
- docker-compose.yml

## Fuentes de verdad

- Transiciones normales: ENT_OPS_STATE_MACHINE §B1
- Transiciones cancelación: §B2
- Transiciones prohibidas: §B3
- Bloqueo: §C

## Qué construir

1. ExpedienteFactory con status configurable + artifacts opcionales (para setup rápido de tests)
2. Test happy path: REGISTRO→PRODUCCION→PREPARACION→DESPACHO→TRANSITO→EN_DESTINO→CERRADO (7 transiciones T1-T7)
3. Test cada transición prohibida de §B3 (todas deben fallar con error descriptivo)
4. Test cancelación desde REGISTRO, PRODUCCION, PREPARACION (3 permitidas — T8, T9, T10)
5. Test cancelación desde DESPACHO, TRANSITO, EN_DESTINO, CERRADO (4 prohibidas — deben fallar)
6. Test bloqueo impide transiciones operativas (T2-T7)
7. Test desbloqueo restaura capacidad de transición

## Contratos a respetar en tests (FIX-2)

- can_transition_to retorna bool → assert True/False
- can_execute_command raise → assert raises exception, o no raise → assert no exception
- execute_command retorna (expediente, events_list) → unpack y assert

## Criterios de done

1. ExpedienteFactory funcional
2. Happy path test: 7 transiciones exitosas en secuencia
3. Al menos 1 test por cada transición prohibida de §B3
4. 3 tests cancelación permitida + 4 tests cancelación prohibida
5. Test bloqueo + desbloqueo
6. Tests usan contratos reales de services.py (FIX-2), no mocks inventados
7. Todos los tests passing

## Formato de salida

## Resultado de ejecución
- Agente: AG-06 QA
- Lote: LOTE_SM_SPRINT1
- Item: #8 — Tests de transición
- Status: DONE / PARTIAL / BLOCKED
- Archivos creados: [lista]
- Archivos modificados: [lista]
- Archivos NO tocados (confirmar): apps/* (no tocado)
- Decisiones asumidas: [lista]
- Blockers: [lista, o "ninguno"]
- Verificación: [criterios 1-7, ✅ o ❌]
- Output de pytest: [pegar resumen]

Branch: sprint1/item-8-tests-transitions
```

---

# ITEM 9 — Tests de commands (API-based)

```
Agente: AG-06 QA
Sprint: 1, Item 9 de 10
Dependencia: Items 3-6 aprobados (endpoints funcionales)

## Orden

Tests end-to-end via API para cada command.

## Archivos PERMITIDOS

- tests/test_commands.py (crear)
- tests/test_permissions.py (crear)
- tests/conftest.py (extend si necesario)

## Archivos PROHIBIDOS

- apps/* (todo), docker-compose.yml

## Fuentes de verdad

- Commands: ENT_OPS_STATE_MACHINE §F1-F3
- Pagos: §L3 (acumulación)
- Moneda: §M
- Bloqueo: §C3

## Qué construir

### Tests por command (happy path + precondiciones fallidas)

- C1: crear expediente → status=REGISTRO, is_blocked=false, payment_status=pending
- C2-C4: cada command crea artifact + falla si artifact previo no existe
- C5: crea ART-04 + auto-transición→PRODUCCION + **2 eventos en response** (FIX-5)
- C6-C10: precondiciones + transiciones. C10 como gate (falla sin ART-05+06, o sin ART-08 si dispatch_mode=mwt). **C10 retorna 2 eventos** (FIX-5)
- C11-C14: flujo DESPACHO→CERRADO. C14 falla si payment_status ≠ paid
- C15: CostLine append-only + falla en status CERRADO/CANCELADO
- C16: cancelación CEO only + falla desde DESPACHO/TRANSITO/EN_DESTINO
- C17/C18: block/unblock cycle + event_log history
- C21: payment acumulación (pending→partial→paid) + sobrepago

### Tests de permisos

- C4, C16, C18 fallan si no superuser
- Cualquier command operativo falla si expediente bloqueado

### Tests de atomicidad (3 casos obligatorios)

1. C2 (command sin transición): monkeypatch ArtifactInstance.objects.create para que falle → verificar no persiste event_log ni artifact
2. C5 (command con transición): monkeypatch fallo en artifact → verificar status sigue REGISTRO, no event_log, no artifact, no 2do evento
3. C15 o C21 (ledger): monkeypatch fallo en CostLine/PaymentLine create → verificar no persiste event_log ni cambio en payment_status

### Tests de response format (FIX-1 — NUEVO)

- Al menos 1 test verifica response body de command normal: {"expediente": {...}, "events": [{...}]}
- Al menos 1 test verifica response body de command con auto-transición (C5 o C10): {"expediente": {...}, "events": [{...}, {...}]}
- Verificar HTTP status codes: C1=201, C6=200, C14=200, C15=201

### Tests de credit clock (FIX-3 — NUEVO)

- C1 con rule=on_creation: verificar credit_clock_started_at != null
- C7 con rule=on_shipment: verificar credit_clock_started_at != null
- C1 con rule=on_shipment: verificar credit_clock_started_at == null (no inicia aún)

### Tests de EnsureNotBlocked bypass (FIX-8 — NUEVO)

- C16 CancelExpediente ejecuta OK aunque expediente esté bloqueado
- C18 UnblockExpediente ejecuta OK (el expediente ESTÁ bloqueado — si usara EnsureNotBlocked, fallaría)
- Verificar que C2-C15, C21 SÍ fallan si expediente bloqueado

## Criterios de done

1. Al menos 1 test happy path + 1 test failure por cada command
2. Test auto-transición C5 y C10 con 2 eventos (FIX-5)
3. Test gate C10 con dispatch_mode=mwt vs client
4. Test C14 falla sin payment
5. Test C21 acumulación completa
6. Tests permissions (3 CEO-only commands)
7. Test is_blocked impide commands operativos
8. 3 tests atomicidad passing
9. Tests response format (FIX-1): body y HTTP status
10. Tests credit clock (FIX-3): persist en C1 y C7
11. Tests EnsureNotBlocked bypass (FIX-8): C16 OK bloqueado, C18 OK bloqueado, operativos fallan bloqueado
12. Todos los tests passing

## Formato de salida

## Resultado de ejecución
- Agente: AG-06 QA
- Lote: LOTE_SM_SPRINT1
- Item: #9 — Tests de commands
- Status: DONE / PARTIAL / BLOCKED
- Archivos creados: [lista]
- Archivos modificados: [lista]
- Archivos NO tocados (confirmar): apps/* (no tocado)
- Decisiones asumidas: [lista]
- Blockers: [lista, o "ninguno"]
- Verificación: [criterios 1-12, ✅ o ❌]
- Output de pytest: [pegar resumen]
- Conteo: X tests, X passed, X failed

Branch: sprint1/item-9-tests-commands
```

---

Stamp vigente: APROBADO por CEO el 2026-02-26 23:59
Vencimiento: 2026-05-27 (stamp + 90 dias)
Estado: VIGENTE
Aprobador final: CEO (actualmente: Alvaro)
