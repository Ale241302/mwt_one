# STATE MACHINE FORMAL — Expediente de Importación (Marluvas)
status: FROZEN — Aprobado para Sprint 1
visibility: [INTERNAL]
domain: Operaciones (IDX_OPS)
version: 1.2.2 (FINAL)
resuelve: |
  R1: State machine, transaction boundaries, Artifact/Document/Event, commands, cancelación
  R2: Conteo estados, T4/C9/C10, credit_clock, corrección artifacts, auto-transitions, outbox, cobro, blocked_by
  R3: E1.1/C7/C8, VoidArtifact, pagos parciales, SupersedeArtifact, credit_clock config
  R4: C1 mutaciones, blocked_by en C1, formato F1, moneda PaymentLine, día 90
  R5: 75d/90d clarificación, sobrepago, C17 tipado, credit_clock_start_rule refs
refs: ENT_OPS_EXPEDIENTE.D1, ENT_OPS_EXPEDIENTE.E, ARTIFACT_REGISTRY, ENT_PLAT_EVENTOS.B

---

## A. Estados canónicos

6 estados operativos + 2 estados terminales = 8 estados totales.

| # | Estado | Código | Tipo | Descripción |
|---|--------|--------|------|-------------|
| 1 | Registro | REGISTRO | operativo | Expediente creado, recibiendo OC y generando proforma |
| 2 | Producción | PRODUCCION | operativo | Fábrica fabricando. Esperando fecha cumplida |
| 3 | Preparación | PREPARACION | operativo | Producto listo. Coordinando logística y docs |
| 4 | Despacho | DESPACHO | operativo | Docs completos, aprobación cliente obtenida, listo para embarcar |
| 5 | Tránsito | TRANSITO | operativo | Carga embarcada, en camino |
| 6 | En destino | EN_DESTINO | operativo | Carga llegó. Pendiente entrega + facturación + cobro |
| 7 | Cerrado | CERRADO | terminal | Entrega confirmada + factura emitida + cobro registrado |
| 8 | Cancelado | CANCELADO | terminal | Operación abortada. Inmutable. Registra razón |

Nota: ENT_OPS_EXPEDIENTE.D1 usa "Histórico" como estado final. Se renombra a "Cerrado" por claridad semántica — "Histórico" describe el uso del dato, no el estado del expediente. [PENDIENTE — CEO: confirmar renombre Histórico → Cerrado].

---

## B. Matriz de transiciones

### B1. Transiciones normales (flujo feliz)

| # | From | Trigger | Precondiciones | To | Artefactos requeridos | Evento emitido | Quién dispara | Reversible |
|---|------|---------|----------------|----|-----------------------|----------------|---------------|------------|
| T1 | — | CreateExpediente | client_id válido, brand=marluvas | REGISTRO | — | expediente.created | CEO | No |
| T2 | REGISTRO | ConfirmProduction | ART-01 completed + ART-02 completed + ART-03 completed + ART-04 completed | PRODUCCION | OC Cliente, Proforma MWT, Decisión B/C, Confirmación SAP | expediente.state_changed | Dentro de C5 handler (ref → sección J) | No |
| T3 | PRODUCCION | ProductionComplete | Fecha fabricación cumplida (manual o trigger) | PREPARACION | — | expediente.state_changed | CEO (confirma) | No |
| T4 | PREPARACION | DispatchApproved | ART-05 completed + ART-06 completed + (ART-08 completed SI dispatch_mode=mwt) + ART-07 completed | DESPACHO | AWB/BL, Cotización flete, (Docs aduanales), Aprobación despacho | expediente.state_changed | Dentro de C10 (ApproveDispatch handler) | No |
| T5 | DESPACHO | ShipmentDeparted | Confirmación embarque carrier | TRANSITO | — | expediente.state_changed | CEO (registra) | No |
| T6 | TRANSITO | ShipmentArrived | Tracking confirma llegada a destino | EN_DESTINO | — | expediente.state_changed | CEO (registra) | No |
| T7 | EN_DESTINO | CloseExpediente | Entrega confirmada + ART-09 completed + payment_status=paid | CERRADO | Factura MWT | expediente.completed | CEO (confirma) | No |

### B2. Transiciones de cancelación

| # | From | Trigger | Precondiciones | To | Evento emitido | Quién dispara |
|---|------|---------|----------------|----|----------------|---------------|
| T8 | REGISTRO | CancelExpediente | Razón obligatoria | CANCELADO | expediente.cancelled | CEO |
| T9 | PRODUCCION | CancelExpediente | Razón obligatoria. [PENDIENTE — CEO: ¿penalización Marluvas si cancela en producción?] | CANCELADO | expediente.cancelled | CEO |
| T10 | PREPARACION | CancelExpediente | Razón obligatoria. Costos ya incurridos se congelan (ref → POL_INMUTABILIDAD) | CANCELADO | expediente.cancelled | CEO |

Regla de cancelación: **No se puede cancelar desde DESPACHO, TRÁNSITO ni EN_DESTINO.** Una vez que la carga está en camino, el expediente debe cerrarse normalmente o resolverse por excepción.

[PENDIENTE — CEO: ¿existe caso real donde se necesite cancelar después de despacho? Si sí, se agrega con condiciones.]

### B3. Transiciones prohibidas (explícitas)

| Transición | Razón |
|-----------|-------|
| Cualquier estado → REGISTRO | No se puede volver al inicio |
| CERRADO → cualquiera | Estado terminal. Inmutable |
| CANCELADO → cualquiera | Estado terminal. Inmutable |
| TRANSITO → PRODUCCION | No se retrocede en flujo operativo |
| TRANSITO → PREPARACION | No se retrocede en flujo operativo |
| EN_DESTINO → DESPACHO | Carga ya llegó |
| Saltar estados (ej: REGISTRO → DESPACHO) | Cada estado tiene precondiciones que verificar |

Regla general: **No hay retroceso.** El flujo es estrictamente hacia adelante. Si algo sale mal, se resuelve con bloqueo + excepción, no con retroceso de estado.

---

## C. Mecanismo de bloqueo

### C1. Definición

Cualquier expediente en estado operativo (REGISTRO a EN_DESTINO) puede entrar en estado **bloqueado**. El bloqueo es un flag paralelo al estado, no un estado propio.

```
Modelo:
  is_blocked: boolean (default false)
  blocked_reason: string (nullable)
  blocked_at: datetime (nullable)
  blocked_by_type: enum (CEO / SYSTEM)
  blocked_by_id: string (nullable)  # user_id si CEO, rule_name si SYSTEM
```

### C2. Qué causa bloqueo

| Causa | Ejemplo | Quién bloquea |
|-------|---------|---------------|
| Documento faltante pasado plazo | AWB no llega y fábrica ya tiene listo | Sistema (SLA vencido) |
| Reloj crédito en riesgo | >75 días de los 90d sin despacho | Sistema (auto) |
| Problema operativo | Carrier cancela espacio, fábrica retrasa | CEO (manual) |
| Discrepancia documental | OC no coincide con factura | CEO (manual) |
| Cliente no responde aprobación | Aprobación despacho pendiente >X días | Sistema (SLA) |

### C3. Reglas de bloqueo

- Expediente bloqueado **no avanza** de estado. Transiciones T2-T7 verifican `is_blocked == false` como precondición.
- Expediente bloqueado **sí puede cancelarse** (T8-T10 ignoran bloqueo).
- Desbloqueo: solo CEO. Registra razón de resolución.
- Evento al bloquear: `expediente.blocked { expediente_id, reason, state_at_block }`
- Evento al desbloquear: `expediente.unblocked { expediente_id, resolution }`

### C4. Semáforo visual

| Color | Condición |
|-------|----------|
| 🟢 Verde | Expediente en flujo normal, dentro de tiempos esperados |
| 🟡 Amarillo | Expediente en flujo pero acercándose a SLA o reloj crédito >60d |
| 🔴 Rojo | Expediente bloqueado O reloj crédito >75d |

---

## D. Reloj de crédito (integración con state machine)

ref → ENT_COMERCIAL_FINANZAS para definición completa del reloj 90d.

### D1. Regla de arranque del reloj

La regla de arranque del reloj (`credit_clock_start_rule`) es una decisión comercial separada de freight_mode. Hoy están correlacionadas pero no son lo mismo:

- `freight_mode` = quién paga flete y cuándo (prepaid: MWT adelanta; postpaid: cliente paga al recibir)
- `credit_clock_start_rule` = cuándo empieza a contar el plazo de crédito al cliente

Correlación actual (Marluvas MVP) implementada como campo configurable:

```
Expediente:
  credit_clock_start_rule: enum (on_creation / on_shipment)
  # Se asigna automáticamente al crear expediente:
  # freight_mode=prepaid → credit_clock_start_rule=on_creation
  # freight_mode=postpaid → credit_clock_start_rule=on_shipment
  # CEO puede override manual si caso particular lo requiere
```

Esta correlación es la regla por defecto. Si en el futuro la relación freight_mode↔reloj cambia, se modifica la regla de asignación sin tocar la state machine.

### D2. Eventos de reloj por transición

| Evento state machine | Efecto en reloj |
|---------------------|-----------------|
| expediente.created (T1) | Reloj inicia si credit_clock_start_rule=on_creation |
| shipment.created (parte de T4→T5) | Reloj inicia si credit_clock_start_rule=on_shipment |
| expediente.completed (T7) | Reloj se detiene |
| expediente.cancelled (T8-T10) | Reloj se detiene. Costos congelados |
| expediente.blocked | Reloj **NO se detiene**. Tiempo sigue corriendo |

Umbrales:
- Día 60: alerta amarilla → notificación CEO
- Día 75: alerta roja → expediente.blocked automático (si no está ya bloqueado)
- Día 90: ver sección M2.

---

## E. Artefactos por estado — mapa completo

| Estado | Artefactos que se crean/completan en este estado | Obligatorio para avanzar |
|--------|--------------------------------------------------|-------------------------|
| REGISTRO | ART-01 OC Cliente, ART-02 Proforma MWT, ART-03 Decisión B/C | Sí (todos para T2) |
| REGISTRO | ART-04 Confirmación SAP | Sí (para T2) |
| PRODUCCION | — (esperando fábrica) | Solo fecha fabricación |
| PREPARACION | ART-05 AWB/BL, ART-06 Cotización flete | Sí (para T4) |
| PREPARACION | ART-07 Aprobación despacho | Sí (para T4) |
| PREPARACION | ART-08 Docs aduanales | Solo si dispatch_mode=mwt |
| DESPACHO | — (esperando embarque) | Solo confirmación carrier |
| TRANSITO | — (esperando llegada) | Solo tracking llegada |
| EN_DESTINO | ART-09 Factura MWT | Sí (para T7) |
| EN_DESTINO | ART-10 Factura comisión | Solo si mode=COMISION |
| EN_DESTINO | ART-12 Nota compensación | Opcional [CEO-ONLY] |
| Cualquier estado | ART-11 Registro costos | No — se puede registrar costos en cualquier momento |

### E1. Invariantes de artefactos

Reglas que siempre deben cumplirse:

1. **ART-07 (Aprobación despacho) no puede completarse sin ART-05 (AWB/BL) + ART-06 (Cotización flete).** El cliente aprueba viendo shipment + costo. Flujo en PREPARACION: primero C7 (shipment), luego C8 (freight quote), luego C9 (customs si aplica), luego C10 (approve = gate).
2. **ART-07 (Aprobación despacho) requiere además ART-08 si dispatch_mode=mwt.** Si cliente usa su despachante, MWT no genera docs aduanales.
3. **ART-08 (Docs aduanales) solo aplica si dispatch_mode=mwt.** Si cliente usa su despachante, MWT no genera docs aduanales.
4. **ART-09 (Factura MWT) no puede emitirse antes de EN_DESTINO.** No se factura antes de que la carga llegue.
5. **ART-10 (Factura comisión) solo existe si mode=COMISION.** En modo FULL no hay comisión.
6. **ART-11 (Registro costos) es append-only.** Cada línea de costo se agrega, nunca se modifica ni elimina (ref → POL_INMUTABILIDAD). ART-11 es el comando de captura; CostLine es la persistencia canónica. ART-11 no almacena totales.
7. **ART-12 (Nota compensación) es [CEO-ONLY].** Nunca visible en vista client.

---

## F. Command Handlers del MVP

Derivados de la state machine. Estos son los comandos que Sprint 1-3 debe implementar.

### F1. Commands de expediente

| # | Command | Input | Precondiciones | Mutaciones (atómicas) | Side effects (async) | Evento(s) |
|---|---------|-------|----------------|----------------------|---------------------|-----------|
| C1 | CreateExpediente | brand, client_id, mode, freight_mode, transport_mode, dispatch_mode, price_basis, credit_clock_start_rule (optional override) | client_id válido, brand=marluvas (MVP) | INSERT expediente (status=REGISTRO, credit_clock_start_rule=resolved_rule, is_blocked=false, payment_status=pending) + INSERT event_log | — | expediente.created |
| C2 | RegisterOC | expediente_id, items[], document_file | status=REGISTRO, is_blocked=false | INSERT ART-01 instance (completed) + INSERT event_log | Notificación | oc.received |
| C3 | CreateProforma | expediente_id, lineas[], montos, consecutivo | status=REGISTRO, ART-01 exists | INSERT ART-02 instance + INSERT event_log | Notificación | proforma.created |
| C4 | DecideModeBC | expediente_id, mode_decision | status=REGISTRO, ART-02 exists, CEO only | INSERT ART-03 instance (completed) + INSERT event_log | — | mode.selected |
| C5 | RegisterSAPConfirmation | expediente_id, sap_id, fecha_fabricacion | status=REGISTRO, ART-01+02+03 exist | INSERT ART-04 instance (completed) + UPDATE status→PRODUCCION + INSERT event_log | Notificación cliente | sap.confirmed + expediente.state_changed |
| C6 | ConfirmProductionComplete | expediente_id | status=PRODUCCION, is_blocked=false | UPDATE status→PREPARACION + INSERT event_log | — | expediente.state_changed |
| C7 | RegisterShipment | expediente_id, tipo, carrier, origen, destino, tracking, itinerario[] | status=PREPARACION, is_blocked=false | INSERT ART-05 instance (completed) + INSERT event_log | Inicia reloj crédito si credit_clock_start_rule=on_shipment | shipment.created |
| C8 | RegisterFreightQuote | expediente_id, monto, modo, freight_mode | status=PREPARACION, ART-05 exists | INSERT ART-06 instance (completed) + INSERT event_log | — | freight.quoted |
| C9 | RegisterCustomsDocs | expediente_id, ncm[], dai_pct, permisos[] | status=PREPARACION, dispatch_mode=mwt, ART-05+06 exist | INSERT ART-08 instance (completed) + INSERT event_log | — | customs.ready |
| C10 | ApproveDispatch | expediente_id, approved_by | status=PREPARACION, ART-05+06 exist, (ART-08 exists SI dispatch_mode=mwt), is_blocked=false | INSERT ART-07 instance (completed) + UPDATE status→DESPACHO + INSERT event_log | Notificación | dispatch.approved + expediente.state_changed |

> **Regla de orden en PREPARACION:**
> - Si dispatch_mode=mwt → C7 → C8 → C9 → C10. Customs antes de approve.
> - Si dispatch_mode=client → C7 → C8 → C10. Sin customs.
> - C10 (ApproveDispatch) es siempre el gate final que mueve a DESPACHO.

| # | Command | Input | Precondiciones | Mutaciones (atómicas) | Side effects (async) | Evento(s) |
|---|---------|-------|----------------|----------------------|---------------------|-----------|
| C11 | ConfirmShipmentDeparted | expediente_id | status=DESPACHO, is_blocked=false | UPDATE status→TRANSITO + INSERT event_log | — | expediente.state_changed |
| C12 | ConfirmShipmentArrived | expediente_id | status=TRANSITO, is_blocked=false | UPDATE status→EN_DESTINO + INSERT event_log | — | expediente.state_changed |
| C13 | IssueInvoice | expediente_id, total_client_view, currency | status=EN_DESTINO, is_blocked=false | INSERT ART-09 instance (completed) + INSERT event_log | Conector fiscal (si existe) | invoice.issued |
| C14 | CloseExpediente | expediente_id | status=EN_DESTINO, ART-09 exists, payment_status=paid, is_blocked=false | UPDATE status→CERRADO + INSERT event_log | Detiene reloj crédito | expediente.completed |

### F2. Commands de costos (transversal — cualquier estado)

| # | Command | Input | Precondiciones | Mutaciones (atómicas) | Side effects (async) | Evento(s) |
|---|---------|-------|----------------|----------------------|---------------------|-----------|
| C15 | RegisterCostLine | expediente_id, cost_type, amount, currency, phase, description | expediente exists, status ≠ CERRADO, status ≠ CANCELADO | INSERT CostLine + INSERT event_log | — | cost.registered |

Regla: ART-11 (Registro costos) = C15. ART-11 es el comando de captura. CostLine es la entidad de persistencia. No se duplica estado.

### F3. Commands de excepción

| # | Command | Input | Precondiciones | Mutaciones (atómicas) | Side effects (async) | Evento(s) |
|---|---------|-------|----------------|----------------------|---------------------|-----------|
| C16 | CancelExpediente | expediente_id, reason | status ∈ {REGISTRO, PRODUCCION, PREPARACION}, CEO only | UPDATE status→CANCELADO + INSERT event_log | Detiene reloj crédito, notificación. Costos congelados = C15 queda invalidado por estado terminal (no se aceptan nuevos CostLine en CANCELADO) | expediente.cancelled |
| C17 | BlockExpediente | expediente_id, reason | status ∈ estados operativos, is_blocked=false | UPDATE is_blocked=true, blocked_reason=reason, blocked_at=now(), blocked_by_type+blocked_by_id (resuelto desde contexto: CEO autenticado o SYSTEM rule_name) + INSERT event_log | Notificación CEO | expediente.blocked |
| C18 | UnblockExpediente | expediente_id, resolution | is_blocked=true, CEO only | UPDATE is_blocked=false, clear blocked_reason/blocked_at/blocked_by_type/blocked_by_id + INSERT event_log (historia preservada en log) | — | expediente.unblocked |

### F4. Regla de atomicidad (Transaction Boundaries)

**Dentro de la misma transacción PostgreSQL (atómico):**
- Cambio de status del expediente
- Inserción de ArtifactInstance
- Inserción en event_log (outbox)
- Inserción de CostLine (si aplica)

**Fuera de la transacción (async, retryable via Celery):**
- Notificaciones (email, push)
- Actualización de reloj crédito (si es cálculo derivado)
- Conector fiscal (FacturaProfesional)
- Cualquier side effect que toque sistema externo

**Regla:** Si falla lo atómico, todo hace rollback. Si falla lo async, se reintenta. El event_log (outbox) garantiza que los side effects eventualmente se ejecuten.

---

## G. Regla Artifact / Document / Event

Resuelve: H3 (Claude) + Crítico #3 (ChatGPT).

```
Document   = archivo físico en MinIO. Inmutable una vez almacenado.
             Ejemplo: el PDF del AWB/BL escaneado.

ArtifactInstance = registro de negocio en PostgreSQL. Tiene payload tipado,
                   estado propio (draft→completed), y puede tener Document(s)
                   adjuntos via FK. ES LA FUENTE DE VERDAD del acto de negocio.
                   Ejemplo: el registro ART-05 con carrier, tracking, itinerario.

Event      = notificación inmutable en event_log/outbox. Se emite cuando
             ArtifactInstance cambia de estado. Para auditoría y side effects.
             Ejemplo: shipment.created con payload mínimo.
```

**Regla de consulta:** El dashboard consulta ArtifactInstance. Document es storage. Event es auditoría. Nunca se consulta Document o Event para mostrar estado de negocio.

**Regla de duplicación:** Los datos de negocio viven en ArtifactInstance. El Document es evidencia adjunta. El Event es notificación. No se copian campos entre ellos.

---

## H. Diagrama visual

```
                    ┌─────────────┐
                    │  CANCELADO  │ (terminal)
                    └──────▲──────┘
                           │ T8/T9/T10
         ┌─────────────────┼─────────────────┐
         │                 │                  │
    ┌────┴────┐      ┌─────┴─────┐     ┌─────┴──────┐
    │REGISTRO │─T2──▶│PRODUCCION │─T3─▶│PREPARACION │
    │         │      │           │     │            │
    │ART-01   │      │(esperando │     │ART-05,06   │
    │ART-02   │      │ fábrica)  │     │ART-07,08   │
    │ART-03   │      │           │     │            │
    │ART-04   │      └───────────┘     └─────┬──────┘
    └─────────┘                              │ T4
                                       ┌─────▼──────┐
                                       │  DESPACHO   │
                                       │(embarque)   │
                                       └─────┬──────┘
                                             │ T5
                                       ┌─────▼──────┐
                                       │  TRANSITO   │
                                       │(en camino)  │
                                       └─────┬──────┘
                                             │ T6
                                       ┌─────▼──────┐
                                       │ EN_DESTINO  │
                                       │ART-09,10,12 │
                                       └─────┬──────┘
                                             │ T7
                                       ┌─────▼──────┐
                                       │  CERRADO    │ (terminal)
                                       └─────────────┘

    ╔═══════════════════════════════════╗
    ║ 🔒 BLOQUEO = flag paralelo       ║
    ║ Cualquier estado operativo puede  ║
    ║ bloquearse. No es estado propio.  ║
    ╚═══════════════════════════════════╝
```

---

## I. Política de corrección de artefactos (sin retroceso)

No hay retroceso de estado. Pero sí hay errores operativos. Esta es la política:

### I1. Regla general

Un ArtifactInstance en estado `completed` **no se edita ni se elimina** (ref → POL_INMUTABILIDAD). Si hay error, se corrige creando una nueva instancia que reemplaza la anterior.

### I2. Mecanismo: Supersede

```
artifact_original.status = superseded
artifact_original.superseded_by = artifact_nuevo.id
artifact_nuevo.supersedes = artifact_original.id
artifact_nuevo.status = completed
```

El artifact original queda en el log para auditoría. El nuevo es la fuente de verdad.

### I3. Command de corrección

| # | Command | Input | Precondiciones | Mutaciones (atómicas) | Evento |
|---|---------|-------|----------------|----------------------|--------|
| C19 | SupersedeArtifact | expediente_id, original_artifact_id, new_payload, reason | original.status=completed, CEO only, expediente.status ≠ CERRADO, mismo artifact_type, ver reglas I3.1 | UPDATE original.status→superseded + INSERT new ArtifactInstance (completed) + INSERT event_log | artifact.superseded |

### I3.1. Reglas de supersede

1. **Mismo tipo obligatorio.** ART-05 solo puede ser superseded por otro ART-05. No se cambia tipo.
2. **Revalidar precondiciones.** El nuevo payload debe cumplir las mismas validation_rules del artifact_type.
3. **Protección post-transición.** Si el artefacto fue precondición de una transición ya ejecutada (ej: ART-04 habilitó T2), supersede requiere expediente bloqueado. Flujo: BlockExpediente → SupersedeArtifact → sistema revalida que la transición sigue siendo válida con el nuevo payload → UnblockExpediente.
4. **Artefactos en estados tempranos.** Si la transición habilitada por el artefacto aún no ocurrió, supersede es libre (CEO only, sin bloqueo).

### I4. Casos de uso

- AWB con tracking incorrecto → supersede ART-05 con datos corregidos
- Cotización mal capturada → supersede ART-06
- Factura con error → void ART-09 + emitir nueva (ART-09 nueva instancia)

### I5. Void (anulación sin reemplazo)

Para artefactos que deben anularse sin sustituto (ej: factura emitida por error antes de tiempo):

| # | Command | Input | Precondiciones | Mutaciones | Evento |
|---|---------|-------|----------------|-----------|--------|
| C20 | VoidArtifact | expediente_id, artifact_id, reason | artifact.status=completed, CEO only, artifact_type ∈ voidable_list, ver reglas I5.1 | UPDATE artifact.status→void + INSERT event_log | artifact.voided |

### I5.1. Reglas de void

**Artefactos voidables en MVP:** ART-09 (Factura MWT), ART-10 (Factura comisión), ART-12 (Nota compensación). Estos son documentos fiscales/financieros que pueden tener errores.

**Artefactos NO voidables:** ART-01 a ART-08. Son artefactos operativos que habilitan transiciones. Si tienen error → usar SupersedeArtifact (C19), no void.

**Regla de protección post-transición:** No se puede void ni supersede de un artefacto que fue precondición de una transición ya ejecutada, SALVO que el expediente esté bloqueado (is_blocked=true). Flujo: BlockExpediente → SupersedeArtifact → UnblockExpediente.

Regla: void de ART-09 (Factura) puede requerir nota crédito en sistema fiscal externo. El sistema registra el void; el conector fiscal maneja la consecuencia externa.

---

## J. Mecanismo de transición automática

Resuelve: "Sistema (auto)" como actor.

### J1. Regla de implementación

Las transiciones automáticas ocurren **dentro del command handler que completa el último artefacto requerido**, no en un servicio separado ni en un job asíncrono.

```python
# Ejemplo conceptual: handler de C5 (RegisterSAPConfirmation)
def handle_register_sap(expediente_id, sap_id, fecha_fabricacion):
    with transaction.atomic():
        art04 = ArtifactInstance.create(type=ART_04, ...)
        transitioned = expediente.can_transition_to(PRODUCCION)
        if transitioned:
            expediente.transition_to(PRODUCCION)
        EventLog.create(type='sap.confirmed', ...)
        if transitioned:
            EventLog.create(type='expediente.state_changed', ...)
```

### J2. Regla

- `can_transition_to()` es un método puro del modelo Expediente que evalúa: (1) estado actual válido para la transición, (2) is_blocked==false, (3) artefactos requeridos existen y están completed, (4) policy checks (dispatch_mode, payment_status, etc.).
- La transición se ejecuta dentro de la misma transacción atómica del command handler.
- No hay servicio externo, no hay signal, no hay job. Es síncrono dentro del handler.
- Esto aplica a T2 (auto al completar ART-04) y T4 (auto al completar C10/ApproveDispatch).

---

## K. Schema del Event Log (Outbox)

| Campo | Tipo | Descripción |
|-------|------|-------------|
| event_id | uuid | PK, generado al insertar |
| event_type | string | ej: "expediente.state_changed", "oc.received" |
| aggregate_type | enum | expediente / transfer / node / artifact |
| aggregate_id | uuid | FK al aggregate que originó el evento |
| payload | jsonb | Datos del evento (ref → ENT_PLAT_EVENTOS.B para payloads) |
| occurred_at | datetime | Timestamp del evento |
| emitted_by | string | Command que lo generó (ej: "C5:RegisterSAPConfirmation") |
| processed_at | datetime | Null hasta que dispatcher lo envíe. Para outbox pattern |
| retry_count | int | Default 0. Incrementa en cada reintento de dispatch |
| correlation_id | uuid | Request ID del command que originó la cadena. Para trazabilidad |

Índices recomendados: `(aggregate_type, aggregate_id)`, `(processed_at)` para outbox polling, `(correlation_id)`.

---

## L. Campo cobro_registrado

T7 (CloseExpediente) y C14 requieren "cobro registrado" como precondición. Definición concreta:

### L1. Modelo

```
Expediente:
  payment_status: enum (pending / partial / paid)
  payment_registered_at: datetime (nullable, último pago)
  payment_registered_by_type: enum (CEO / SYSTEM)
  payment_registered_by_id: string (nullable)
```

```
PaymentLine (append-only, misma lógica que CostLine):
  payment_line_id: uuid
  expediente_id: ref
  amount: decimal
  currency: enum
  method: string (transferencia / cheque / otro)
  reference: string (número de comprobante)
  registered_at: datetime
  registered_by_type: enum (CEO / SYSTEM)
  registered_by_id: string
```

### L2. Command

| # | Command | Input | Precondiciones | Mutaciones (atómicas) | Evento |
|---|---------|-------|----------------|----------------------|--------|
| C21 | RegisterPayment | expediente_id, amount, currency, method, reference | ART-09 exists (factura emitida), status=EN_DESTINO | INSERT PaymentLine + UPDATE payment_status (ver L3) + UPDATE payment_registered_at=now(), payment_registered_by_type+id (contexto) + INSERT event_log | payment.registered |

### L3. Regla de acumulación y cierre

```
amount_paid_total = SUM(PaymentLine.amount WHERE expediente_id = X)
invoice_total = ART-09.total_client_view

Si amount_paid_total == 0 → payment_status = pending
Si 0 < amount_paid_total < invoice_total → payment_status = partial
Si amount_paid_total >= invoice_total → payment_status = paid
```

Regla MVP de sobrepago: se permite. Si `amount_paid_total > invoice_total`, el sistema marca `paid` y la diferencia se trata fuera del cierre del expediente (ajuste contable manual o nota de crédito).

C21 calcula `amount_paid_total` después de insertar el PaymentLine y actualiza `payment_status` automáticamente.

### L4. Precondición de cierre actualizada

C14 (CloseExpediente) requiere: `payment_status = paid`.

[PENDIENTE — CEO: ¿aceptar cierre con payment_status=partial? ¿O siempre debe ser paid completo?]

---

## M. Regla de moneda en pagos (MVP)

En MVP, toda la operación Marluvas se factura y cobra en una sola moneda por expediente. Regla:

- `PaymentLine.currency` debe coincidir con `ART-09.currency` (moneda de la factura).
- Si un pago llega en moneda diferente, el CEO registra el monto ya convertido a moneda de factura.
- Post-MVP: si se requiere multi-moneda real, se agrega tabla de conversión y `amount_in_base_currency`.

---

## M2. Comportamiento día 90 del reloj de crédito (MVP default)

Día 90 = el reloj venció. Comportamiento MVP por defecto:

1. Sistema emite evento `credit_clock.expired { expediente_id, days_elapsed: 90, amount_exposed }`.
2. Sistema revalida bloqueo: si no estaba bloqueado (excepción operativa donde día 75 no disparó), lo bloquea ahora (`blocked_by_type=SYSTEM, blocked_by_id="credit_clock_90d"`). En condiciones normales ya estará bloqueado desde día 75.
3. **No hay acción automática de cobro ni reclamo.** El CEO debe resolver manualmente.
4. Dashboard muestra el expediente en rojo con badge "CRÉDITO VENCIDO".

[PENDIENTE — CEO: ¿política de escalamiento post-90d? ¿Reclamo formal? ¿Suspensión de nuevos expedientes al mismo cliente? Se define cuando haya experiencia operativa real.]

---

## N. Extensiones futuras (no MVP)

### N1. Tecmater
4 estados: Orden → Preparación → Despacho → Tránsito. Sin Producción ni SAP. State machine separada o parametrizada por brand.

### N2. Rana Walk
Bifurcación post-Tránsito: Nacionalización CR vs Reexportación USA. Requiere Transfer como entidad para modelar el split.

### N3. Handoff Expediente → Transfer
Regla prevista: cuando expediente llega a EN_DESTINO con nodo_destino asignado, sistema sugiere crear Transfer al siguiente nodo. CEO confirma. Se implementa cuando Transfer entre en producción.

---

Stamp: CONGELADO v1.2.2 — Aprobado para Sprint 1
Origen: 5 rondas de auditoría dual Claude + ChatGPT — sesión 2026-02-26
