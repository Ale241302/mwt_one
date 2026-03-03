# LOTE_SM_SPRINT5 — Liquidación Marluvas + Transfer Model + Extensiones Logísticas
sprint: 5
priority: P0
depends_on: LOTE_SM_SPRINT4 (todos los items aprobados)
refs: ENT_OPS_STATE_MACHINE v1.2.2 (FROZEN), PLB_ORCHESTRATOR v1.2.2 (FROZEN), ENT_PLAT_ARTEFACTOS v2.0, ENT_OPS_TRANSFERS v1.0, ENT_COMERCIAL_MODELOS v1.0, ARTIFACT_REGISTRY v2.0, ENT_PLAT_LEGAL_ENTITY v1.0
status: FROZEN v1.3 — Aprobado CEO 2026-03-02
visibility: [INTERNAL]
domain: Plataforma (IDX_PLATAFORMA)
version: 1.3
tipo: Lote ruteado (ref → PLB_ORCHESTRATOR §E)

---

## Objetivo Sprint 5

Dos pilares: (1) Cerrar ciclo financiero Modelo B con reconciliación real de liquidaciones Marluvas (matching por proforma, con visibilidad derivada a expediente), y (2) Construir la entidad Transfer como cimiento para Sprint 6 (Rana Walk). Secundario: extensiones logísticas sobre base Sprint 4 y Paperless-ngx integración.

**Precondición:** Sprint 4 DONE — Ciclo financiero modo FULL cerrado (costos doble vista, ART-09, pagos, comparativa B vs C, PDF client, Tecmater, ART-19 básico), 23 command endpoints POST (C1-C21 pre-Sprint 4 = 20 + C22-C24 Sprint 4 = 3), dashboard financiero básico.

### Incluido en Sprint 5

| # | Feature | Fuente | Prioridad |
|---|---------|--------|-----------|
| 1 | ART-10 Liquidación Marluvas — upload + parsing + reconciliación | ENT_PLAT_ARTEFACTOS.G | P0 — ciclo Modelo B |
| 2 | ART-12 Nota compensación | ENT_PLAT_ARTEFACTOS.B, ARTIFACT_REGISTRY | P1 — edge case CEO |
| 3 | Transfer model + state machine + migraciones | ENT_OPS_TRANSFERS v1.0 | P0 — cimiento Sprint 6 |
| 4 | Handoff Expediente→Transfer (N3) | ENT_OPS_STATE_MACHINE.N3 | P1 — conecta expediente con transfer |
| 5 | ART-19 RouteHistoricalStats auto-suggest | ENT_PLAT_ARTEFACTOS.F, LOTE_SM_SPRINT4 DA-05 | P2 — mejora logística |
| 6 | ART-19 tracking links + updates feed | ENT_PLAT_ARTEFACTOS.F | P2 — mejora logística |
| 7 | Paperless-ngx integración API Django | ENT_PLAT_INFRA, LOTE_SM_SPRINT4 Item 10 | P2 — no bloqueante |
| 8 | Semántica C21 modo B — refinar | ENT_OPS_STATE_MACHINE §L, ENT_PLAT_ARTEFACTOS.G7 | P1 — alinear pagos con liquidación |
| 9 | Tests Sprint 5 | — | P0 — obligatorio |

### Excluido de Sprint 5

| Feature | Razón | Cuándo |
|---------|-------|--------|
| Rana Walk flujo completo | Requiere Transfer en producción + brand config completa | Sprint 6 |
| Dashboard financiero completo (P&L por marca/cliente) | CEO difiere | Sprint 6 |
| Conector fiscal FacturaProfesional | Dependencia externa, factura nominal es suficiente | Post-MVP |
| Portal B2B (portal.mwt.one) | Solo CEO usa MVP | Post-MVP |
| RBAC formal multi-usuario | MVP = is_superuser | Post-MVP |
| Multi-moneda real | MVP = 1 moneda por expediente | Post-MVP |
| Forecast / inteligencia operativa | Necesita 6+ meses data histórica | Post-MVP |

---

## Decisiones asumidas Sprint 5

**DA-01: ART-10 es artefacto CROSS (transversal), no de expediente.**
ART-10 Liquidación Marluvas no tiene FK a un expediente. Vive independiente, cruza N expedientes por período mensual. Es el primer artefacto transversal del sistema. Ref → ENT_PLAT_ARTEFACTOS.G, ARTIFACT_REGISTRY sección CROSS.

**DA-02: ART-10 parser depende de muestra real del Excel de Marluvas.**
[PENDIENTE — NO INVENTAR.] CEO debe proporcionar un ejemplo (anonimizado si necesario) del Excel de liquidación antes de que AG-02 complete el parser. Sin muestra, Item 1 no puede completarse, pero sí puede avanzar en Fase A (storage + stub + error handling). Fase B (mapeo real de columnas + parse exitoso) queda bloqueada hasta recibir muestra. Ref → ENT_PLAT_ARTEFACTOS.G8.

**DA-03: Transfer model se implementa como entidad Django, no como artefacto.**
Transfer es entidad estructural con state machine propia (6 estados). Tiene su propio modelo Django, no es ArtifactInstance.payload. Artefactos de transfer (ART-13 a ART-17) se implementan en Sprint 6 cuando Rana Walk entre. Sprint 5 = modelo + transiciones básicas + handoff desde expediente.

**DA-04: C21 en modo B se redefine como tracking de comisión cobrada.**
Sprint 4 definió C21 en COMISION como "pago registrado contra OC". Con ART-10 (liquidación entrante), la semántica correcta es: C21 en modo B registra el cobro de comisión de MWT desde la liquidación de Marluvas. El reference_total cambia de ART-01.total_po a la comisión esperada calculada desde comision_pactada × total_po. Item 8 implementa esta corrección.

**DA-05: ART-19 auto-suggest requiere mínimo 5 expedientes cerrados con ART-19 completado.**
RouteHistoricalStats necesita base de datos histórica. Si Sprint 4 no generó suficientes expedientes con ART-19, el auto-suggest no dará resultados útiles. El endpoint retorna sugerencias solo si hay data suficiente, o lista vacía si no.

**DA-06: Paperless-ngx integración es unidireccional Sprint 5.**
Django sube documentos a Paperless. Paperless no modifica datos en Django. La integración bidireccional (Paperless notifica Django de OCR completado, etc.) es Sprint 6+.

---

## Items

### Item 1: ART-10 Liquidación Marluvas — Backend Completo
- **Agente:** AG-02 API Builder
- **Dependencia previa:** Sprint 4 DONE. Fase B requiere muestra Excel de Marluvas (DA-02). Fase A puede avanzar sin muestra.
- **Command ref:** ENT_PLAT_ARTEFACTOS.G (spec completa)
- **Archivos a tocar:** apps/liquidations/ (nuevo módulo Django), apps/liquidations/models.py, apps/liquidations/services.py, apps/liquidations/serializers.py, apps/liquidations/views.py, apps/liquidations/urls.py, apps/liquidations/parsers.py
- **Archivos prohibidos:** apps/expedientes/models.py (ART-10 no es artefacto de expediente)
- **Criterio de done:**

  **Modelo:**
  - [ ] Liquidation model: liquidation_id (auto LIQ-YYYY-MM-NNN), period (YYYY-MM), brand="marluvas", source_file (FileField), status (enum: pending, in_review, reconciled, disputed), totales calculados, timestamps
  - [ ] LiquidationLine model: FK Liquidation, marluvas_reference, concept (enum: comision, premio, ajuste, otro), client_payment_amount, commission_pct_reported, commission_amount, currency, is_partial_payment, matched_proforma_id (nullable FK ArtifactInstance donde type=ART-02), matched_expediente_id (nullable FK Expediente), commission_pct_expected (nullable), match_status (enum: matched, discrepancy, unmatched, no_match_needed), observation

  **Commands (nuevos):**
  - [ ] `POST /api/liquidations/upload/` → C25 UploadLiquidation
    - Input: file (Excel), period (YYYY-MM)
    - Precondiciones: file es xlsx válido, period formato correcto, no existe liquidación reconciled para mismo período
    - Mutaciones: INSERT Liquidation (status=pending) + parsear Excel → INSERT LiquidationLines + intento de match automático por marluvas_reference contra ART-02 consecutivos
    - Evento: liquidation.received
  - [ ] `POST /api/liquidations/{id}/match-line/` → C26 ManualMatchLine
    - Input: line_id, proforma_id (ART-02 ArtifactInstance)
    - Precondiciones: Liquidation status ∈ {pending, in_review}, line.match_status ∈ {unmatched}
    - Mutaciones: UPDATE LiquidationLine (matched_proforma_id, matched_expediente_id desde proforma.expediente, commission_pct_expected desde ART-02.payload.comision_pactada, recalcular match_status)
    - Evento: ninguno (operación interna)
  - [ ] `POST /api/liquidations/{id}/reconcile/` → C27 ReconcileLiquidation
    - Input: liquidation_id
    - Precondiciones: Liquidation status ∈ {pending, in_review}, todas las líneas concept=comision tienen match_status ∈ {matched, no_match_needed} (premiaciones no necesitan match)
    - Mutaciones: UPDATE status→reconciled, reconciled_at, reconciled_by + recalcular totales
    - Evento: liquidation.reconciled
  - [ ] `POST /api/liquidations/{id}/dispute/` → C28 DisputeLiquidation
    - Input: liquidation_id, observations (text)
    - Precondiciones: Liquidation status ∈ {pending, in_review}
    - Mutaciones: UPDATE status→disputed, observations
    - Evento: liquidation.disputed

  **Read endpoints:**
  - [ ] `GET /api/liquidations/` → lista paginada [CEO-ONLY]
  - [ ] `GET /api/liquidations/{id}/` → detalle con líneas, totales, delta, match status por línea
  - [ ] `GET /api/liquidations/{id}/lines/` → líneas con datos de match expandidos

  **Parser (dos fases):**

  *Fase A — ejecutable sin muestra:*
  - [ ] parsers.py: interfaz/stub que define contrato: recibe archivo Excel → retorna lista de dicts con campos mapeados
  - [ ] Manejo de errores: si columnas no coinciden → Liquidation se crea con status=pending pero lines vacías + error_log con detalle de parsing failure
  - [ ] Upload + storage del archivo funcional (el Excel se guarda aunque no se parsee)

  *Fase B — requiere muestra real (bloqueante DA-02):*
  - [ ] Mapeo real de columnas del Excel de Marluvas → campos de LiquidationLine
  - [ ] Parse exitoso de muestra real con líneas extraídas correctamente
  - [ ] Formato de columnas: [PENDIENTE — NO INVENTAR. Se define cuando CEO proporcione muestra. Ref → DA-02.]

  **Match automático:**
  - [ ] Al crear Liquidation, para cada línea con concept=comision: buscar ART-02 ArtifactInstance donde payload.consecutive ILIKE marluvas_reference
  - [ ] Si match único → auto-asignar matched_proforma_id + calcular commission_pct_expected desde ART-02.payload.comision_pactada
  - [ ] Si match múltiple o ninguno → match_status=unmatched (CEO resuelve manual con C26)
  - [ ] Premiaciones (concept=premio) → match_status=no_match_needed automáticamente

  **Tolerancias:**
  - [ ] Monto: ±1% o ±$5 USD (lo que sea mayor). Configurable en settings.
  - [ ] Porcentaje comisión: ±0.5 puntos porcentuales. Configurable en settings.
  - [ ] Dentro de tolerancia → matched. Fuera → discrepancy.

  **Tracking acumulado:**
  - [ ] Vista que muestra por proforma: total liquidado históricamente (SUM de commission_amount en todas las liquidaciones donde matched_proforma_id = X)

---

### Item 2: ART-12 Nota Compensación — Backend + Frontend
- **Agente:** AG-02 API Builder + AG-03 Frontend
- **Dependencia previa:** Sprint 4 DONE
- **Command ref:** ENT_PLAT_ARTEFACTOS.B fila ART-12 (Nota compensación), ARTIFACT_REGISTRY sección EXPEDIENTE fila ART-12
- **Archivos a tocar:** apps/expedientes/services.py, apps/expedientes/serializers.py, apps/expedientes/views.py, frontend components
- **Archivos prohibidos:** apps/expedientes/models.py (usa ArtifactInstance existente)
- **Criterio de done:**
  - [ ] `POST /api/expedientes/{id}/register-compensation/` → C29 RegisterCompensation
    - Input: expediente_id, items[] (description, quantity, estimated_value), notes
    - Precondiciones: expediente exists, status ≠ CERRADO, status ≠ CANCELADO, CEO only
    - Mutaciones: INSERT ArtifactInstance (type=ART-12, status=completed, payload con items + notes + total_estimated_value) + INSERT event_log
    - Evento: compensation.noted
  - [ ] ART-12 es voidable (C20 VoidArtifact ya existe desde Sprint 2)
  - [ ] Visibilidad: [CEO-ONLY] completa. No aparece en vista client ni en PDF espejo.
  - [ ] Frontend: card en vista detalle expediente, solo visible si usuario es CEO. Muestra items, valor estimado, notas.
  - [ ] Si no hay ART-12 → card no aparece (no mostrar card vacía)

---

### Item 3: Transfer Model + State Machine + Migraciones
- **Agente:** AG-01 Architect
- **Dependencia previa:** Sprint 4 DONE
- **Command ref:** ENT_OPS_TRANSFERS v1.0
- **Archivos a tocar:** apps/transfers/ (nuevo módulo Django), apps/transfers/models.py, apps/transfers/enums.py, apps/transfers/admin.py, apps/expedientes/models.py (solo para agregar campo nodo_destino)
- **Archivos prohibidos:** apps/expedientes/services.py, apps/expedientes/views.py, apps/expedientes/serializers.py
- **Criterio de done:**

  **Modelos:**
  - [ ] Transfer model: transfer_id (auto TRF-YYYYMMDD-XXX), from_node (FK Node), to_node (FK Node), ownership_before (FK LegalEntity), ownership_after (FK LegalEntity), ownership_changes (boolean), legal_context (enum: internal, nationalization, reexport, distribution, consignment), customs_required (boolean), pricing_context (jsonb nullable), source_expediente (FK Expediente nullable), status (enum: planned, approved, in_transit, received, reconciled, cancelled), timestamps
  - [ ] TransferLine model: FK Transfer, sku (string ref), quantity_dispatched (int), quantity_received (int nullable), discrepancy (int nullable computed), condition (enum: good, damaged, partial, nullable)
  - [ ] CostLine reutilizada: mismo modelo CostLine de expedientes pero con FK Transfer nullable. Un CostLine pertenece a expediente XOR transfer, nunca a ambos.
  - [ ] Node model stub: node_id, name, legal_entity (FK LegalEntity), node_type (enum: fiscal, owned_warehouse, fba, third_party, factory), location, status. [PENDIENTE — detalles completos en ENT_OPS_NODOS. Sprint 5 = modelo mínimo funcional.]

  **State machine Transfer:**
  - [ ] Transiciones válidas (ref → ENT_OPS_TRANSFERS.D):
    - planned → approved (Sprint 5: CEO only siempre. Refinamiento futuro: condicional solo si ownership_changes o monto > umbral.)
    - approved → in_transit (regla puente Sprint 5: ART-15 no existe aún — se sustituye por confirmación manual CEO + event_log. Sprint 6 reemplaza por ART-15 completado.)
    - in_transit → received (regla puente Sprint 5: ART-13 no existe aún — se sustituye por confirmación manual de recepción con payload de cantidades. Sprint 6 reemplaza por ART-13 completado.)
    - received → reconciled (todas las líneas con quantity_received informada y quantity_dispatched == quantity_received; si no, solo CEO con exception_reason obligatorio)
    - cualquier → cancelled (CEO only, registra razón)
  - [ ] Validación en transitions: misma lógica que expediente state machine (precondiciones, event_log, is_blocked)

  **Migraciones:**
  - [ ] Django migrations para Transfer, TransferLine, Node
  - [ ] CostLine: agregar FK transfer nullable (migration)
  - [ ] Expediente: agregar campo nodo_destino = FK Node nullable (migration). Usado por Item 4 (Handoff).
  - [ ] No romper CostLines existentes de expedientes ni expedientes existentes

  **NO hacer en este item:**
  - Commands y endpoints de Transfer no se implementan en Item 3; se implementan en Item 3B. Item 4 solo consume C30 para el handoff.
  - Artefactos de Transfer (ART-13 a ART-17) — Sprint 6
  - Frontend Transfer — Sprint 6

---

### Item 3B: Transfer Commands — Backend
- **Agente:** AG-02 API Builder
- **Dependencia previa:** Item 3 aprobado (modelos estables)
- **Archivos a tocar:** apps/transfers/services.py, apps/transfers/serializers.py, apps/transfers/views.py, apps/transfers/urls.py
- **Archivos prohibidos:** apps/transfers/models.py, apps/expedientes/
- **Criterio de done:**
  - [ ] `POST /api/transfers/` → C30 CreateTransfer
    - Input: from_node, to_node, legal_context, items[] (sku, quantity), source_expediente (opcional)
    - Precondiciones: from_node y to_node existen, from_node ≠ to_node, legal_context válido
    - Mutaciones: INSERT Transfer (status=planned) + INSERT TransferLines + INSERT event_log
    - Auto-calcular: ownership_before/after desde Node.legal_entity, ownership_changes = ownership_before ≠ ownership_after, customs_required según regla de legal_context
    - Evento: transfer.created
  - [ ] `POST /api/transfers/{id}/approve/` → C31 ApproveTransfer
    - Precondiciones: status=planned, CEO only
    - Mutaciones: UPDATE status→approved + timestamps
    - Evento: transfer.approved
  - [ ] `POST /api/transfers/{id}/dispatch/` → C32 DispatchTransfer
    - Precondiciones: status=approved
    - Regla puente Sprint 5: ART-15 no existe — CEO confirma despacho manualmente. Sprint 6 reemplaza por ART-15 completado.
    - Mutaciones: UPDATE status→in_transit + timestamps
    - Evento: transfer.dispatched
  - [ ] `POST /api/transfers/{id}/receive/` → C33 ReceiveTransfer
    - Input: lines[] (sku, quantity_received, condition)
    - Precondiciones: status=in_transit
    - Regla puente Sprint 5: ART-13 no existe — CEO confirma recepción manualmente con payload de cantidades. Sprint 6 reemplaza por ART-13 completado.
    - Mutaciones: UPDATE TransferLines (quantity_received, condition, discrepancy) + UPDATE status→received
    - Evento: transfer.received
  - [ ] `POST /api/transfers/{id}/reconcile/` → C34 ReconcileTransfer
    - Precondiciones: status=received, todas las líneas con quantity_received informada y quantity_dispatched == quantity_received; si no, solo CEO con exception_reason obligatorio
    - Si hay discrepancias: solo CEO puede reconciliar. Input adicional: exception_reason (string, obligatorio). Se registra en event_log.
    - Mutaciones: UPDATE status→reconciled
    - Evento: transfer.reconciled
  - [ ] `POST /api/transfers/{id}/cancel/` → C35 CancelTransfer
    - Input: reason
    - Precondiciones: status ∈ {planned, approved}, CEO only
    - Mutaciones: UPDATE status→cancelled + reason
    - Evento: transfer.cancelled

  **Read endpoints:**
  - [ ] `GET /api/transfers/` → lista paginada [CEO-ONLY]
  - [ ] `GET /api/transfers/{id}/` → detalle con líneas, costos, status, nodos

  **Total nuevos commands: C30-C35 = 6 commands**

---

### Item 4: Handoff Expediente→Transfer
- **Agente:** AG-02 API Builder + AG-03 Frontend
- **Dependencia previa:** Item 3B aprobado
- **Command ref:** ENT_OPS_STATE_MACHINE.N3
- **Archivos a tocar:** apps/expedientes/services.py (extender C14 CloseExpediente o nuevo side effect), frontend components
- **Archivos prohibidos:** apps/expedientes/models.py, apps/transfers/models.py
- **Criterio de done:**
  - [ ] Cuando expediente transiciona a CERRADO (C14) y tiene nodo_destino asignado:
    - Sistema genera sugerencia de Transfer: from_node=nodo_destino, items=líneas del expediente
    - Sugerencia aparece como card en vista del expediente cerrado: "Producto entregado a [nodo]. ¿Crear transfer?"
    - CEO confirma → ejecuta C30 CreateTransfer con source_expediente=expediente_id
    - CEO ignora → nada pasa (sugerencia desaparece o persiste como badge informativo)
  - [ ] No es automático. CEO siempre confirma.
  - [ ] Si expediente no tiene nodo_destino → no se sugiere transfer
  - [ ] nodo_destino: campo FK Node nullable agregado en Item 3 (migración). CEO lo asigna al crear o durante el expediente.

---

### Item 5: ART-19 RouteHistoricalStats — Auto-suggest
- **Agente:** AG-02 API Builder
- **Dependencia previa:** Sprint 4 DONE (ART-19 básico funcional con opciones manuales)
- **Command ref:** ENT_PLAT_ARTEFACTOS.F (ART-19 spec), LOTE_SM_SPRINT4 DA-05
- **Archivos a tocar:** apps/expedientes/services.py (extender ART-19), apps/expedientes/views.py
- **Archivos prohibidos:** apps/expedientes/models.py
- **Criterio de done:**
  - [ ] `GET /api/expedientes/{id}/logistics-suggestions/` → endpoint nuevo [CEO-ONLY]
    - Busca expedientes cerrados con ART-19 completed que compartan: misma ruta origen→destino, mismo tipo de producto (brand), similar volumen (±30%)
    - Retorna top 3-5 opciones históricas rankeadas por: frecuencia de uso, costo promedio, días promedio
    - Si < 5 expedientes históricos con match → retorna lista vacía con mensaje "Insufficient historical data"
  - [ ] Frontend: en vista ART-19 (panel de opciones logísticas), sección "Sugerencias basadas en histórico" arriba de opciones manuales
    - Cards con datos del histórico: carrier, modo, costo promedio, días promedio, veces usado
    - Botón "Agregar como opción" → ejecuta C23 AddLogisticsOption pre-llenando datos del histórico
  - [ ] Si no hay sugerencias → sección no aparece (no mostrar sección vacía)

---

### Item 6: ART-19 Tracking Links + Updates Feed
- **Agente:** AG-02 API Builder + AG-03 Frontend
- **Dependencia previa:** Sprint 4 DONE (ART-19 + ART-05 funcionales)
- **Archivos a tocar:** apps/expedientes/services.py (extender ART-05 payload), frontend components
- **Archivos prohibidos:** apps/expedientes/models.py
- **Criterio de done:**
  - [ ] ART-05 payload extendido con:
    - tracking_url: string (URL de tracking del carrier)
    - sub_legs[]: array de {leg_id, origin, destination, carrier, status, eta, actual_arrival}
    - updates[]: array de {timestamp, description, source} (feed cronológico de eventos del envío)
  - [ ] `POST /api/expedientes/{id}/add-shipment-update/` → C36 AddShipmentUpdate
    - Input: description, source (manual | carrier_api)
    - Precondiciones: ART-05 exists, expediente status ∈ {DESPACHO, TRANSITO, EN_DESTINO}
    - Mutaciones: APPEND to ART-05.payload.updates[]
    - Evento: shipment.updated
  - [ ] Frontend: en vista expediente TRANSITO, timeline de updates del envío con sub-tramos visuales
  - [ ] Tracking link: botón que abre tracking_url en nueva pestaña
  - [ ] Sprint 5 = updates manuales. Integración con APIs de carriers (DHL, MSC, etc.) = Post-MVP.

---

### Item 7: Paperless-ngx Integración API
- **Agente:** AG-02 API Builder
- **Dependencia previa:** Sprint 4 Item 10 (Paperless standalone corriendo)
- **Archivos a tocar:** apps/integrations/paperless.py (nuevo), apps/expedientes/services.py (hook en artifact creation)
- **Archivos prohibidos:** docker-compose.yml de Paperless (ya configurado Sprint 4)
- **Criterio de done:**
  - [ ] Client HTTP para Paperless-ngx API: upload documento, crear tag, asignar correspondiente
  - [ ] Hook: cuando ArtifactInstance de expediente se completa y tiene archivo adjunto → auto-upload a Paperless con tags: [expediente_id, artifact_type, brand, period]
  - [ ] Scope Sprint 5: hook aplica solo a artefactos con FK expediente. Artefactos CROSS (ART-10 Liquidación) se excluyen del hook — upload manual o extensión Sprint 6.
  - [ ] Manejo de errores: si Paperless no responde → log error, no bloquear la operación del expediente
  - [ ] Unidireccional: Django → Paperless. Paperless no modifica datos en Django (DA-06).
  - [ ] Si Paperless no está corriendo → silently skip (no bloqueante, como Sprint 4)

---

### Item 8: Semántica C21 Modo B — Refinar Pagos con Liquidación
- **Agente:** AG-02 API Builder + AG-03 Frontend
- **Dependencia previa:** Item 1 aprobado (ART-10 funcional)
- **Command ref:** ENT_OPS_STATE_MACHINE §L (C21), ENT_PLAT_ARTEFACTOS.G7
- **Archivos a tocar:** apps/expedientes/services.py (ajustar C21 precondiciones modo B), frontend panel pagos
- **Archivos prohibidos:** apps/expedientes/models.py
- **Criterio de done:**
  - [ ] C21 en modo COMISION: reference_total cambia de ART-01.total_po a comisión esperada (comision_pactada × total_po / 100 desde ART-02)
  - [ ] C21 en COMISION debe soportar múltiples registros parciales (un expediente puede aparecer en múltiples liquidaciones mensuales por pagos parciales del cliente a Marluvas)
  - [ ] payment_status=paid cuando SUM(PaymentLines.amount) >= comisión_esperada. Una liquidación parcial no cierra el expediente por sí sola si no alcanza el total.
  - [ ] Cuando ART-10 liquidación se reconcilia y tiene línea matched a una proforma de este expediente → sistema sugiere registrar pago
    - Card en vista expediente: "Liquidación LIQ-2026-01 reconciliada. Comisión $X confirmada para proforma Y. ¿Registrar pago?"
    - CEO confirma → C21 se ejecuta con amount=commission_amount de la línea, method="liquidacion_marluvas", reference=liquidation_id
    - Si es pago parcial, la sugerencia indica el acumulado: "Pago parcial. Acumulado: $X de $Y esperado."
  - [ ] Badge en panel pagos modo B: "Comisión — referencia liquidación Marluvas" (en vez de "Pago registrado contra OC")
  - [ ] Barra de progreso modo B: amount_paid_total / comisión_esperada (no / total_po)
  - [ ] Si no hay liquidación reconciliada → CEO puede registrar pago manual como antes (backward compatible)

---

### Item 9: Tests Sprint 5
- **Agente:** AG-04 QA
- **Dependencia previa:** Items 1-8 aprobados
- **Archivos a tocar:** apps/liquidations/tests/, apps/transfers/tests/, apps/expedientes/tests/
- **Criterio de done:**

  **ART-10 Liquidación (Item 1):**
  - [ ] Upload Excel → Liquidation creada con líneas parseadas
  - [ ] Upload con columnas no mapeables → Liquidation creada, source_file guardado, lines vacías, error_log poblado (valida Fase A)
  - [ ] Match automático por consecutivo proforma → matched
  - [ ] Match manual (C26) → actualiza línea
  - [ ] Reconcile (C27) → status=reconciled, evento emitido
  - [ ] Dispute (C28) → status=disputed con observations
  - [ ] Upload a período ya reconciliado → rechazado
  - [ ] Línea con discrepancia en % → match_status=discrepancy
  - [ ] Premiación → match_status=no_match_needed automático

  **ART-12 Compensación (Item 2):**
  - [ ] C29 RegisterCompensation → ArtifactInstance creada, CEO-ONLY
  - [ ] Void ART-12 (C20) → funcional
  - [ ] No visible en vista client / PDF espejo

  **Transfer (Items 3-3B):**
  - [ ] C30 CreateTransfer → Transfer creada con status=planned
  - [ ] C31-C34 happy path → planned→approved→in_transit→received→reconciled
  - [ ] C35 Cancel → solo desde planned/approved
  - [ ] Discrepancia en recepción → received pero no reconcilable sin excepción
  - [ ] C34 con discrepancias + CEO + exception_reason → status=reconciled + event_log registra excepción
  - [ ] CostLine en Transfer → no afecta CostLines de expediente

  **Handoff (Item 4):**
  - [ ] Expediente con nodo_destino cierra → sugerencia de transfer aparece
  - [ ] Expediente sin nodo_destino cierra → sin sugerencia
  - [ ] Confirmar sugerencia → Transfer creada con source_expediente

  **ART-19 extensiones (Items 5-6):**
  - [ ] Auto-suggest con 5+ expedientes históricos → retorna sugerencias
  - [ ] Auto-suggest con < 5 → lista vacía
  - [ ] C36 AddShipmentUpdate → update agregado a ART-05.payload.updates[]
  - [ ] Tracking link presente en frontend

  **C21 refinado (Item 8):**
  - [ ] C21 modo B: reference_total = comisión esperada, no total_po
  - [ ] Liquidación reconciliada → sugerencia de pago aparece
  - [ ] Backward compatible: pago manual sin liquidación sigue funcionando

  **Regresión:**
  - [ ] 23 command endpoints Sprint 1-4 funcionales
  - [ ] Frontend Sprint 3-4 sin regresión
  - [ ] ART-09, ART-19 básico, dashboard financiero básico intactos

  **Total post-Sprint 5: 23 + 12 (C25-C36) = 35 command endpoints POST**

---

## Criterio de cierre Sprint 5

1. ART-10 funcional: upload Excel → parse → match por proforma → reconcile/dispute
2. ART-12 funcional: registro + void + CEO-ONLY
3. Transfer model en producción: 6 estados, TransferLine, CostLine compartida
4. Transfer commands funcionales: C30-C35 happy path
5. Handoff funcional: expediente cerrado con nodo → sugerencia → crear transfer
6. ART-19 auto-suggest funcional (con data suficiente) o degradado graceful
7. Tracking links + updates feed funcional
8. Paperless-ngx sube docs automáticamente (si no alcanza, no bloqueante)
9. C21 modo B alineado con liquidación Marluvas
10. Tests Item 9 passing
11. 23 command endpoints anteriores funcionales (no regresión)
12. Frontend Sprint 3-4 sin regresión

**Lo que significa "Sprint 5 DONE":**
- El CEO reconcilia liquidaciones de Marluvas contra proformas modo B del sistema (con visibilidad derivada a expediente)
- Transfer existe como entidad para Sprint 6 (Rana Walk)
- El sistema sugiere crear transfers cuando expedientes cierran
- Logística tiene historial y tracking
- El ciclo financiero modo B está cerrado end-to-end: proforma/operación modo B → Marluvas liquida → CEO reconcilia por proforma → pagos parciales/acumulados se registran y reflejan en el expediente asociado

**Lo que NO debe existir al cerrar Sprint 5:**
- Rana Walk flujos (Sprint 6)
- Artefactos de Transfer ART-13 a ART-17 (Sprint 6)
- Dashboard P&L completo (Sprint 6)
- Conector fiscal FacturaProfesional (Post-MVP)
- Portal B2B (Post-MVP)
- RBAC multi-usuario (Post-MVP)

---

## Qué queda para Sprint 6+

| Feature | Sprint |
|---------|--------|
| Rana Walk flujo completo (brand config + bifurcación CR/USA + 3 transfers tipo) | 6 |
| Artefactos Transfer (ART-13 Recepción, ART-14 Preparación, ART-15 Despacho, ART-16 Transfer pricing) | 6 |
| Dashboard financiero completo (P&L por marca/cliente/período) | 6 |
| Paperless-ngx bidireccional (OCR → Django) | 6+ |
| Conector fiscal FacturaProfesional | Post-MVP |
| Portal B2B (portal.mwt.one → mwt.one RBAC) | Post-MVP |
| Multi-moneda real | Post-MVP |
| Forecast / inteligencia operativa | Post-MVP (6+ meses data) |

---

Stamp: FROZEN v1.3 — Aprobado CEO 2026-03-02
Origen: Derivado de LOTE_SM_SPRINT4 (FROZEN v1.3) + ENT_OPS_TRANSFERS v1.0 + ENT_PLAT_ARTEFACTOS v2.0 (rediseño ART-10) + decisiones CEO sesión 2026-03-02
Auditoría: 3 rondas ChatGPT (8.3→9.4→9.7/10, 17 fixes total)
