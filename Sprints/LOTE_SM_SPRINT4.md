# LOTE_SM_SPRINT4 — Costos Doble Vista + Factura MWT + Artefactos Logísticos + Financiero + Tecmater
sprint: 4
priority: P0
depends_on: LOTE_SM_SPRINT3 (todos los items aprobados)
refs: ENT_OPS_STATE_MACHINE v1.2.2 (FROZEN), PLB_ORCHESTRATOR v1.2.2 (FROZEN), ENT_PLAT_ARTEFACTOS v1.0, ENT_COMERCIAL_MODELOS, SCH_PROFORMA_MWT v1.0, ENT_OPS_EXPEDIENTE v2.0, ENT_PLAT_MVP v1.0
status: FROZEN v1.3 — Aprobado CEO 2026-03-02
visibility: [INTERNAL]
domain: Plataforma (IDX_PLATAFORMA)
version: 1.3
tipo: Lote ruteado (ref → PLB_ORCHESTRATOR §E)

---

## Scope Sprint 4

**Objetivo:** Cerrar el ciclo financiero completo de un expediente — el CEO ve costos reales vs precio cliente, genera factura, compara modelos B vs C retroactivamente, y tiene un PDF espejo listo para el cliente. Además, se amplía el catálogo de artefactos operativos y se prepara la plataforma para Tecmater.

**Precondición:** Sprint 3 DONE — Frontend básico funcional (lista + detalle + timeline + semáforos), notificaciones email, event consumers reales, 20 command endpoints POST de Sprint 1-2 funcionales.

### Incluido en Sprint 4

| # | Feature | Fuente | Prioridad |
|---|---------|--------|-----------|
| 1 | Costos doble vista (CostLine.visibility filter + API + UI) | ENT_OPS_EXPEDIENTE.C1, LOTE_SM_SPRINT2 tabla final | P0 — visibilidad financiera |
| 2 | ART-09 Factura MWT generación (C13 payload + doble vista + PDF) | §F1 C13, ENT_PLAT_ARTEFACTOS.B | P0 — cierre ciclo cobro |
| 3 | C21 RegisterPayment (extensión: vista frontend) | §L, ya implementado Sprint 1 backend — frontend Sprint 4 | P0 — cierre expediente |
| 4 | Modelo financiero escenario 2 (comparativa retroactiva B vs C) | ENT_PLAT_MVP.D Sprint 4, ENT_COMERCIAL_MODELOS.D | P1 — decisiones CEO |
| 5 | ART-06 Cotización flete (artefacto formal) | ENT_PLAT_ARTEFACTOS.H | P1 — precondición T4 |
| 6 | ART-08 Docs aduanales (artefacto formal, condicional) | ENT_PLAT_ARTEFACTOS.H | P1 — dispatch_mode=mwt |
| 7 | ART-19 Decisión Logística (comparador multi-opción) | ENT_PLAT_ARTEFACTOS.F | P2 — requiere base histórica |
| 8 | Espejo documental PDF (vista client sin datos internos) | ENT_OPS_EXPEDIENTE.C6, ENT_PLAT_MVP.D | P1 — entregable al cliente |
| 9 | Tecmater prep (brand config + skip ART-03/ART-04) | ENT_OPS_STATE_MACHINE.N1, ENT_PLAT_ARTEFACTOS.C3 | P2 — extensión marca |
| 10 | Paperless-ngx Docker | ENT_PLAT_MVP.D Sprint 4, POL_ARCHIVO | P3 — no bloqueante |
| 11 | Dashboard financiero básico | ENT_PLAT_MVP.B4, ENT_PLAT_FRONTENDS.B2 | P1 — rentabilidad visible |
| 12 | Tests Sprint 4 | — | P0 — obligatorio |

### Excluido de Sprint 4

| Feature | Razón | Cuándo |
|---------|-------|--------|
| ART-10 Factura comisión (modo B) | Solo mode=COMISION, requiere conector fiscal | Sprint 5 |
| ART-12 Nota compensación | CEO-ONLY, edge case | Sprint 5 |
| Conector fiscal FacturaProfesional | Dependencia externa BIZ Z5 | Post-MVP |
| Portal B2B (portal.mwt.one) | Solo CEO usa MVP | Post-MVP |
| RBAC formal multi-usuario | MVP = is_superuser | Post-MVP |
| Rana Walk en flujos | Bifurcación post-tránsito requiere Transfer entity | Sprint 5+ |
| Redis Streams event bus | Overhead innecesario con 1 usuario | Post-MVP |
| Forecast / inteligencia operativa | Necesita 6+ meses data histórica | Post-MVP |

---

## Decisiones asumidas Sprint 4

**DA-01: CostLine.visibility ya existe en modelo.**
Sprint 0 creó CostLine con campo `visibility: enum (internal | client)`. Sprint 4 agrega: (a) filtro en API read endpoints, (b) UI toggle para CEO, (c) espejo PDF usa solo `visibility=client`.
Si el campo no existe → Item 1 incluye migración.

**DA-02: ART-06 y ART-08 ya tienen command handlers (C8, C9) desde Sprint 1.**
Los endpoints `register-freight-quote` y `register-customs` ya existen. Sprint 4 los formaliza como artefactos con payload completo, validaciones ricas, y renderizado en frontend. No son endpoints nuevos — son extensiones de payload.

**DA-03: Factura MWT (ART-09) tiene payload doble vista.**
Vista client: líneas + precio negociado + total. Vista internal: líneas + FOB + costos acumulados + margen. Misma lógica que SCH_PROFORMA_MWT.B (CEO superset, client subset).

**DA-04: Tecmater usa la misma state machine Django parametrizada por brand, no una separada.**
ENT_OPS_STATE_MACHINE.N1 define 4 estados conceptuales para Tecmater: Orden → Preparación → Despacho → Tránsito. Sprint 4 implementa esto como **mapeo semántico sobre la máquina de 8 estados existente**, no como máquina nueva:

| Estado N1 (conceptual Tecmater) | Estado Django (real) | Comportamiento |
|---|---|---|
| Orden | REGISTRO | C1 crea con brand=tecmater, mode=FULL forzado |
| — | PRODUCCION (skip) | T2 salta directo a PREPARACION (no hay ART-03/04) |
| Preparación | PREPARACION | Flujo normal: ART-05, ART-06, ART-07 |
| Despacho | DESPACHO | Flujo normal |
| Tránsito | TRANSITO | Flujo normal |
| — | EN_DESTINO | Flujo normal (factura + cobro) |
| — | CERRADO | Terminal normal |

Lógica: `brand=tecmater` → T2 requiere solo ART-01+02 (no ART-03/04) → transición directa REGISTRO→PREPARACION (skip PRODUCCION). Los estados EN_DESTINO y CERRADO existen en Django pero N1 los agrupa conceptualmente bajo "post-tránsito". No se crean estados nuevos ni se elimina ninguno.

**DA-05: ART-19 es Sprint 4 scope pero con materialización básica.**
Sprint 4 implementa ART-19 con opciones manuales (CEO agrega). Base histórica automática (RouteHistoricalStats) es extensión post-Sprint 4 cuando haya data suficiente. Sprint 4 = estructura + manual input. Sprint 5+ = auto-suggest desde histórico.

**DA-06: Dashboard financiero = extensión del dashboard Sprint 3.**
No es pantalla nueva. Se agregan cards y métricas financieras al dashboard existente: margen por expediente, total costos vs facturado, comparativa B vs C.

---

## Items

### Item 1: Migraciones + Modelo Costos Doble Vista
- **Agente:** AG-01 Architect
- **Dependencia previa:** Sprint 3 DONE
- **Archivos a tocar:** apps/expedientes/models.py (verificar/extender CostLine), apps/expedientes/enums.py (si aplica)
- **Archivos prohibidos:** views.py, services.py, tests/
- **Criterio de done:**
  - [ ] Verificar CostLine tiene campo `visibility: enum (internal | client)`. Si falta → migración
  - [ ] Verificar CostLine tiene campo `phase: string` (para costos por etapa). Si falta → migración
  - [ ] ART-09 Factura MWT: NO crear modelo InvoiceData nuevo. Usar ArtifactInstance.payload (jsonb) enriquecido. El payload de ART-09 contiene:
    - `total_client_view: decimal` — monto factura vista cliente
    - `total_internal_view: decimal` — costo total real [CEO-ONLY]
    - `currency: enum (USD | CRC | BRL)`
    - `lines: array` — líneas detalladas
    - `issued_to_id: ref (LegalEntity)` — a quién se factura
    - `consecutive: string` — número consecutivo factura
    - `margin: decimal` [CEO-ONLY]
    - `margin_pct: decimal` [CEO-ONLY]
  - [ ] Agregar `LogisticsOption` model para ART-19 (ref → ENT_PLAT_ARTEFACTOS.F2):
    - `artifact_instance_id: FK(ArtifactInstance)`
    - `option_id: string`
    - `mode: enum (aereo | maritimo)`
    - `carrier: string`
    - `route: string`
    - `estimated_days: int`
    - `estimated_cost: decimal`
    - `currency: enum`
    - `valid_until: date | null`
    - `source: enum (historical | quote | manual)`
    - `is_selected: boolean (default false)`
  - [ ] Tecmater brand config: NO agregar campo `brand_config` nuevo al modelo Expediente. La parametrización por brand se implementa en `apps/expedientes/services.py` como lógica condicional sobre el campo `brand` existente. `brand=tecmater` → precondiciones reducidas en `can_transition_to()` y `can_execute_command()`. Si el campo `brand` no acepta valor `tecmater` en el enum → agregar al enum + migración.
  - [ ] `python manage.py migrate` sin errores
  - [ ] `python manage.py check` sin errores
  - [ ] Nuevos modelos visibles en Django Admin

---

### Item 2: Costos Doble Vista — API + Lógica
- **Agente:** AG-02 API Builder
- **Dependencia previa:** Item 1 aprobado
- **Command ref:** ENT_OPS_EXPEDIENTE.C1
- **Archivos a tocar:** apps/expedientes/serializers.py (extender), apps/expedientes/views.py (extender), apps/expedientes/services.py (extender)
- **Archivos prohibidos:** models.py, tests/
- **Criterio de done:**
  - [ ] `GET /api/expedientes/{id}/costs/` retorna CostLines filtradas:
    - Si `?view=internal` (CEO only): todas las CostLines
    - Si `?view=client`: solo CostLines con `visibility=client`
    - Default sin parámetro: internal (MVP = solo CEO)
  - [ ] `GET /api/expedientes/{id}/costs/summary/` retorna totales agregados:
    - `total_internal: SUM(amount WHERE visibility=internal OR client)` [CEO-ONLY]
    - `total_client: SUM(amount WHERE visibility=client)`
    - `margin: total_client_invoiced - total_internal` (si ART-09 existe)
    - `margin_pct: margin / total_client_invoiced * 100`
  - [ ] C15 (RegisterCostLine) extendido: acepta `visibility` en input (default: `internal`)
  - [ ] Serializer de CostLine incluye `visibility` en read y write
  - [ ] Permisos: solo CEO ve `visibility=internal`. Futuro portal client ve solo `visibility=client`

---

### Item 3: ART-09 Factura MWT — Generación + Doble Vista
- **Agente:** AG-02 API Builder
- **Dependencia previa:** Item 2 aprobado (costos doble vista estable)
- **Command ref:** State machine §F1 C13 IssueInvoice
- **Archivos a tocar:** apps/expedientes/services.py (extender execute_command para C13 enriched), apps/expedientes/serializers.py (InvoiceSerializer), apps/expedientes/views.py
- **Archivos prohibidos:** models.py, tests/
- **Criterio de done:**
  - [ ] `POST /api/expedientes/{id}/issue-invoice/` → C13 (ya existe de Sprint 1)
  - [ ] Input C13 se mantiene FROZEN: `expediente_id, total_client_view, currency` (no alterar contrato)
  - [ ] Nuevo endpoint helper (no command): `GET /api/expedientes/{id}/invoice-suggestion/` → pre-calcula total_client_view sugerido desde CostLines con `visibility=client` + markup según modelo. CEO revisa y ajusta antes de ejecutar C13.
  - [ ] Payload ART-09 almacenado en ArtifactInstance.payload (no modelo nuevo — usar payload jsonb existente):
    - `consecutive` (auto-generado, formato MWT-YYYY-NNNN)
    - `lines[]` con producto, qty, precio_unitario, subtotal
    - `total_client_view` (lo que el cliente ve y paga)
    - `total_internal_view` [CEO-ONLY] (costo real acumulado)
    - `currency`
    - `issued_to` (LegalEntity del cliente)
    - `margin` y `margin_pct` [CEO-ONLY]
  - [ ] `GET /api/expedientes/{id}/invoice/` → lee ART-09 payload:
    - Con `?view=internal`: muestra todo (CEO)
    - Con `?view=client`: solo campos client-facing
  - [ ] Regla facturación por modelo (ref → ENT_COMERCIAL_MODELOS.D):
    - Modelo C (FULL): ART-09 = MWT factura al cliente. Payload completo con doble vista.
    - Modelo B (COMISION): ART-09 NO se genera como factura al cliente (Marluvas factura directo). En Sprint 4, Modelo B no emite ART-09. La factura de comisión MWT→Marluvas es ART-10 (excluido Sprint 4). Si el CEO necesita registrar un snapshot financiero interno de la operación B, usa C15 (CostLine) como mecanismo de tracking, no ART-09.
    - Consecuencia cierre Modelo B (regla temporal Sprint 4): C14 CloseExpediente en Modelo B requiere solo `payment_status=paid` (no requiere ART-09). El pago en Modelo B se registra contra el monto de la OC (ART-01 total). Si el CEO refina esta regla, se ajusta en Sprint 5.
  - [ ] Evento: `invoice.issued` con payload completo
  - [ ] Consecutivo: persist + auto-increment por LegalEntity emisora

---

### Item 4: Pagos — Vista Frontend
- **Agente:** AG-03 Frontend
- **Dependencia previa:** Item 3 aprobado (ART-09 genera factura para FULL)
- **Command ref:** State machine §L (C21 RegisterPayment)
- **Archivos a tocar:** frontend/pages o components relacionados a expediente detalle
- **Archivos prohibidos:** apps/expedientes/models.py, apps/expedientes/services.py
- **Comportamiento por modo:**
  - **FULL:** Panel completo — ART-09 existe, currency pre-llenada desde ART-09, barra de progreso contra invoice_total.
  - **COMISION:** Panel simplificado — no hay ART-09. Currency se toma de ART-02 (Proforma). Monto de referencia para progreso = `total_po` de ART-01 (OC Cliente). Badge indica "Pago registrado contra OC (sin factura MWT — Marluvas factura directo)".
- **Criterio de done:**
  - [ ] Panel de pagos en vista detalle expediente:
    - Lista PaymentLines existentes (monto, método, referencia, fecha)
    - Barra de progreso: `amount_paid_total / reference_total` con colores (rojo < 50%, amarillo < 100%, verde = paid)
    - `reference_total` = ART-09.total_client_view (FULL) o ART-01.total_po (COMISION)
    - Badge payment_status (pending / partial / paid)
    - Si mode=COMISION: badge adicional "Marluvas factura directo — pago registrado contra OC"
  - [ ] Formulario para C21 RegisterPayment:
    - Campos: amount, currency (pre-llenado desde ART-09 en FULL, desde ART-02 en COMISION), method (dropdown), reference
    - Validación: currency debe coincidir con fuente (ART-09 o ART-02 según modo)
    - Submit → POST /api/expedientes/{id}/register-payment/
  - [ ] C21 backend: en COMISION, precondición ART-09 exists se relaja a ART-01 exists (OC como referencia de monto). Regla acumulación: SUM >= reference_total → paid.
  - [ ] Después de registrar pago: panel se actualiza, payment_status se refresca
  - [ ] Si payment_status=paid: habilitar botón "Cerrar expediente" (C14)

---

### Item 5: Modelo Financiero Escenario 2 — Comparativa B vs C
- **Agente:** AG-02 API Builder
- **Dependencia previa:** Item 2 aprobado (costos disponibles). Item 3 aprobado solo para FULL (ART-09).
- **Command ref:** ENT_COMERCIAL_MODELOS.D, ENT_PLAT_MVP.D
- **Archivos a tocar:** apps/expedientes/services.py (agregar módulo de cálculo), apps/expedientes/serializers.py, apps/expedientes/views.py
- **Archivos prohibidos:** models.py, tests/
- **Convención de nomenclatura:** En payloads API, tests y docs de este item: `B = COMISION`, `C = FULL`. Se usa el nombre del enum (`COMISION` / `FULL`) en código; las letras B/C solo en labels UI y comentarios.
- **Criterio de done:**
  - [ ] `GET /api/expedientes/{id}/financial-comparison/` → endpoint nuevo [CEO-ONLY]
  - [ ] Precondiciones diferenciadas por modo:
    - FULL: requiere ART-09 (factura emitida = datos reales de ingreso)
    - COMISION: requiere ART-02 (proforma con comision_pactada) + CostLines registradas. No requiere ART-09.
    - Si faltan datos mínimos para el modo actual → 409 "Insufficient data for comparison"
  - [ ] Calcula para un expediente real:
    - **Escenario real** (el modelo que se usó): ingresos, costos, margen, margin_pct
    - **Escenario contrafactual** (el modelo alternativo):
      - Si real=B → simula C: `ingreso_C = total_client_view` (MWT factura directo), `costo_C = SUM(CostLine.internal)`, `margin_C = ingreso_C - costo_C`
      - Si real=C → simula B: `ingreso_B = comision_pct * total_po`, `costo_B = 0` (MWT no compra), `margin_B = ingreso_B`
  - [ ] Response:
    ```json
    {
      "expediente_id": "...",
      "actual_mode": "FULL",
      "actual": { "revenue": X, "cost": Y, "margin": Z, "margin_pct": W },
      "counterfactual_mode": "COMISION",
      "counterfactual": { "revenue": X2, "cost": Y2, "margin": Z2, "margin_pct": W2 },
      "delta": { "margin": Z - Z2, "recommendation": "FULL was better by $N" }
    }
    ```
  - [ ] Datos de comisión: fuente única Sprint 4 = `comision_pactada` de ART-02 (Proforma, ref → SCH_PROFORMA_MWT.C2). Fórmula: `ingreso_B = comision_pactada * total_po / 100`. Si comision_pactada no existe en ART-02 payload → endpoint retorna 409 "Insufficient data for comparison".
  - [ ] Refinamiento de fórmula de comisión → Sprint 5 si CEO requiere lógica más compleja

---

### Item 6: ART-06 + ART-08 — Payload Enriquecido + Frontend
- **Agente:** AG-02 API Builder + AG-03 Frontend
- **Dependencia previa:** Item 1 aprobado
- **Command ref:** State machine §F1 C8 (ART-06), C9 (ART-08)
- **Archivos a tocar:** apps/expedientes/serializers.py (extender payload C8/C9), frontend components
- **Archivos prohibidos:** models.py
- **Criterio de done:**

  **ART-06 Cotización flete (C8 RegisterFreightQuote):**
  - [ ] Payload extendido:
    - `amount: decimal` (ya existe)
    - `currency: enum`
    - `freight_mode: enum (prepaid | postpaid)` (ya existe)
    - `transport_mode: enum (aereo | maritimo)`
    - `carrier: string`
    - `quote_reference: string` (número de cotización del carrier)
    - `valid_until: date | null`
    - `notes: string`
  - [ ] Frontend: card en vista PREPARACION con datos de cotización

  **ART-08 Docs aduanales (C9 RegisterCustomsDocs):**
  - [ ] Payload extendido:
    - `ncm_codes: jsonb[]` (array de {code, description, dai_pct})
    - `total_dai_pct: decimal` (calculado o manual)
    - `permits: string[]` (permisos requeridos)
    - `customs_agent: string` (despachante)
    - `estimated_cost: decimal`
    - `currency: enum`
    - `notes: string`
  - [ ] Frontend: card en vista PREPARACION, solo visible si `dispatch_mode=mwt`
  - [ ] Validación C9: `dispatch_mode` debe ser `mwt`. Si `client` → 409

---

### Item 7: ART-19 Decisión Logística — Backend + Frontend Básico
- **Agente:** AG-02 API Builder + AG-03 Frontend
- **Dependencia previa:** Item 1 aprobado (LogisticsOption model existe)
- **Command ref:** ENT_PLAT_ARTEFACTOS.F (spec completa ART-19)
- **Archivos a tocar:** apps/expedientes/services.py (nuevos commands), apps/expedientes/serializers.py, apps/expedientes/views.py, apps/expedientes/urls.py, frontend components
- **Archivos prohibidos:** (ninguno adicional)
- **Criterio de done:**

  **Nuevos commands:**
  - [ ] `POST /api/expedientes/{id}/materialize-logistics/` → C22 MaterializeLogistics
    - Precondiciones: ART-04 exists (Confirmación SAP), status ∈ {PRODUCCION, PREPARACION}
    - Mutaciones: INSERT ArtifactInstance (type=ART-19, status=pending, payload con snapshots de ART-01/ART-04)
    - Evento: `logistics.materialized`
  - [ ] `POST /api/expedientes/{id}/add-logistics-option/` → C23 AddLogisticsOption
    - Precondiciones: ART-19 exists con status=pending, CEO only
    - Input: mode, carrier, route, estimated_days, estimated_cost, currency, valid_until, source
    - Mutaciones: INSERT LogisticsOption
    - Evento: `logistics.option_added`
  - [ ] `POST /api/expedientes/{id}/decide-logistics/` → C24 DecideLogistics
    - Precondiciones: ART-19 exists con status=pending, al menos 1 opción exists
    - Input: selected_option_id
    - Mutaciones: UPDATE LogisticsOption.is_selected=true + UPDATE ART-19 status→completed + UPDATE ART-19 payload (selected_option_id, decided_by, decided_at)
    - Evento: `logistics.decided`
    - Side effect: pre-llena datos para ART-05 (carrier, mode) si se crea después

  **Frontend:**
  - [ ] Dashboard ART-19 en vista expediente (post-PRODUCCION):
    - Cards por opción: modo, carrier, costo, días estimados, válido hasta
    - Agrupado por modo (aéreo vs marítimo)
    - Badge de source (manual / cotización / histórico)
    - Botón "Decidir" que ejecuta C24
    - Stats: total opciones, breakeven pairs (si calculable)
  - [ ] Breakeven básico: `breakeven_pairs = maritimo_flat_cost / aereo_per_pair_cost_delta`
    - Si hay al menos 1 opción aérea + 1 marítima → calcular y mostrar
    - Si no → no mostrar (no inventar)

  **NO hacer en este item:**
  - RouteHistoricalStats auto-suggest (requiere data histórica — post-Sprint 4)
  - Vista portal client de ART-19 (post-MVP)
  - Tracking links (Sprint 5)
  - Sub-tramos de itinerario (Sprint 5)

---

### Item 8: Espejo Documental PDF
- **Agente:** AG-02 API Builder
- **Dependencia previa:** Item 2 aprobado (costos doble vista). Item 3 solo aporta bloque de factura cuando mode=FULL y ART-09 existe.
- **Command ref:** ENT_OPS_EXPEDIENTE.C6
- **Archivos a tocar:** apps/expedientes/services.py (módulo PDF), apps/expedientes/views.py (endpoint), nueva dependencia: weasyprint
- **Archivos prohibidos:** models.py
- **Criterio de done:**
  - [ ] `GET /api/expedientes/{id}/mirror-pdf/` → genera PDF espejo del expediente
  - [ ] PDF contiene SOLO datos `visibility=client`:
    - Header: marca, consecutivo expediente, cliente, fecha
    - Líneas producto (código cliente, no código fábrica — usa SKUAlias si disponible)
    - Costos visibles al cliente (CostLine con visibility=client)
    - Factura resumen (ART-09 total_client_view) si existe
    - Timeline: estados con fechas (sin datos internos)
    - Tracking info si disponible (ART-05 carrier + tracking number)
  - [ ] PDF NO contiene:
    - FOB prices [CEO-ONLY]
    - Costos con visibility=internal
    - Margen, comisión, arbitraje
    - Notas operativas internas
    - ART-12 Nota compensación
  - [ ] PDF branded: logo MWT, colores Navy #013A57 + Mint #75CBB3 (ref → ENT_PLAT_DESIGN_TOKENS)
  - [ ] PDF generado dinámicamente (no cached). Response: `Content-Type: application/pdf`
  - [ ] Dependencia: weasyprint (HTML→PDF). Template HTML inline en Django.

---

### Item 9: Tecmater Prep — Brand Parametrización
- **Agente:** AG-02 API Builder
- **Dependencia previa:** Item 1 aprobado
- **Command ref:** ENT_OPS_STATE_MACHINE.N1, ENT_PLAT_ARTEFACTOS.C3
- **Archivos a tocar:** apps/expedientes/services.py (parametrizar precondiciones), apps/expedientes/enums.py (si brand config), apps/expedientes/serializers.py
- **Archivos prohibidos:** tests/ (hasta Item 12)
- **Criterio de done:**
  - [ ] C1 CreateExpediente acepta `brand=tecmater`
  - [ ] Configuración Tecmater (ref → DA-04, ENT_PLAT_ARTEFACTOS.C3):
    - mode siempre = FULL (C1 fuerza, no acepta COMISION)
    - ART-03 (Decisión B/C) skip — no se requiere como precondición
    - ART-04 (Confirmación SAP) skip — no hay SAP
    - ART-10 (Factura comisión) skip — no aplica
    - ART-19 (Decisión Logística) skip — producto en stock, sin fase producción
  - [ ] Transición T2 parametrizada (mapeo semántico sobre máquina existente, ref → DA-04):
    - Marluvas: REGISTRO→PRODUCCION requiere ART-01+02+03+04
    - Tecmater: REGISTRO→PREPARACION directa (skip PRODUCCION), requiere solo ART-01+02
    - Los estados PRODUCCION, EN_DESTINO, CERRADO siguen existiendo en Django; Tecmater simplemente no pasa por PRODUCCION
  - [ ] `can_transition_to()` y `execute_command()` respetan brand config
  - [ ] Endpoints existentes funcionan con brand=tecmater sin cambios de URL
  - [ ] Validaciones: si brand=tecmater y CEO intenta C4 (DecideModeBC) → 409 "Not applicable for Tecmater"

---

### Item 10: Paperless-ngx Docker
- **Agente:** AG-07 DevOps
- **Dependencia previa:** Ninguna (puede correr en paralelo con todo)
- **Command ref:** ENT_PLAT_MVP.D Sprint 4, POL_ARCHIVO
- **Archivos a tocar:** docker-compose.yml (agregar servicio), .env (config Paperless)
- **Archivos prohibidos:** apps/*, tests/*
- **Criterio de done:**
  - [ ] Contenedor Paperless-ngx corriendo en docker-compose
  - [ ] Volumen persistente para documentos
  - [ ] Accesible via nginx (subdomain o path: /paperless/)
  - [ ] Usuario admin creado
  - [ ] Consume API token configurable (para futura integración con Django)
  - [ ] Health check funcional
  - [ ] NO integrado con Django en Sprint 4 — standalone. Integración API en Sprint 5.
  - [ ] Documentación: README con instrucciones de uso manual (upload via web UI)

**Nota:** Este item es no-bloqueante. Si no alcanza, Drive sigue como destino válido. No afecta ningún otro item.

---

### Item 11: Dashboard Financiero Básico
- **Agente:** AG-03 Frontend
- **Dependencia previa:** Items 2, 3, 5 aprobados (costos + factura + comparativa disponibles via API)
- **Command ref:** ENT_PLAT_MVP.B4, ENT_PLAT_FRONTENDS.B2
- **Archivos a tocar:** frontend/pages o components dashboard
- **Archivos prohibidos:** apps/expedientes/models.py
- **Criterio de done:**
  - [ ] Extensión del dashboard Sprint 3 (no pantalla nueva) con sección financiera:
  - [ ] Card "Margen por expediente": lista de expedientes con datos financieros suficientes (ART-09 en FULL / ART-02+CostLines en COMISION). Columnas: cliente, modo, total referencia, costo real, margen, margin_pct. Coloreado: verde > 15%, amarillo 5-15%, rojo < 5%
  - [ ] Card "Totales activos": suma de facturas emitidas (FULL) + comisiones proyectadas (COMISION), suma costos registrados, margen agregado
  - [ ] Card "Cuentas por cobrar": expedientes con payment_status ≠ paid y referencia válida (ART-09 en FULL / ART-01 en COMISION), días desde factura o desde OC, monto pendiente
  - [ ] Card "Comparativa B vs C": para expedientes cerrados, muestra delta "Ganaste $X más con modelo Y" (consume endpoint Item 5)
  - [ ] Filtros: por marca (marluvas / tecmater), por estado, por rango de fechas
  - [ ] Semáforo financiero integrado con semáforo de tiempos de Sprint 3:
    - Expediente con margen < 5% → badge "⚠️ Margen bajo"
    - Expediente con payment > 60d → badge "⚠️ Cobro atrasado"

---

### Item 12: Tests Sprint 4
- **Agente:** AG-06 QA
- **Dependencia previa:** Items 1-9 aprobados
- **Archivos a tocar:** tests/test_costs_dual_view.py, tests/test_invoice.py, tests/test_financial.py, tests/test_logistics.py, tests/test_tecmater.py, tests/test_mirror_pdf.py
- **Archivos prohibidos:** apps/* (no tocar código producción)
- **Criterio de done:**

  **Tests costos doble vista:**
  - [ ] CostLine con visibility=internal → visible en ?view=internal, invisible en ?view=client
  - [ ] CostLine con visibility=client → visible en ambas vistas
  - [ ] Summary endpoint: total_internal incluye ambas, total_client solo client
  - [ ] Margin calcula correctamente cuando ART-09 existe
  - [ ] C15 con visibility=client → persiste correctamente

  **Tests ART-09 Factura MWT:**
  - [ ] C13 con expediente en EN_DESTINO → ART-09 created con payload completo
  - [ ] Consecutivo auto-incrementa: MWT-2026-0001, MWT-2026-0002...
  - [ ] Vista client de ART-09: no incluye campos [CEO-ONLY]
  - [ ] C13 falla si status ≠ EN_DESTINO
  - [ ] C13 falla si is_blocked=true
  - [ ] Modelo B (COMISION): C13 retorna 409 "ART-09 not applicable for mode COMISION" (Marluvas factura directo; MWT no emite ART-09 en modo B)

  **Tests modelo financiero:**
  - [ ] Comparativa con mode=FULL: escenario contrafactual COMISION calcula comisión correctamente. Requiere ART-09.
  - [ ] Comparativa con mode=COMISION: escenario contrafactual FULL calcula margen. Usa ART-02 + CostLines, sin requerir ART-09.
  - [ ] FULL sin ART-09 → 409 "Insufficient data"
  - [ ] COMISION sin ART-02 → 409 "Insufficient data"
  - [ ] Delta calcula correctamente la diferencia entre escenarios

  **Tests ART-19 Decisión Logística:**
  - [ ] C22 materializa ART-19 con snapshots de ART-01 y ART-04
  - [ ] C22 falla si ART-04 no existe
  - [ ] C23 agrega opción → LogisticsOption persiste
  - [ ] C24 decide → ART-19 status=completed, opción marcada is_selected=true
  - [ ] C24 falla si no hay opciones
  - [ ] C24 falla si ART-19 ya completed
  - [ ] Breakeven calcula correctamente con 1 aérea + 1 marítima

  **Tests ART-06 + ART-08 enriched:**
  - [ ] C8 con payload extendido → todos los campos persisten
  - [ ] C9 con dispatch_mode=client → 409
  - [ ] C9 con dispatch_mode=mwt → OK + ncm_codes persisten

  **Tests Tecmater:**
  - [ ] C1 con brand=tecmater → mode forzado FULL, no acepta COMISION
  - [ ] Expediente Tecmater: T2 usa precondiciones reducidas (ART-01+02 solo, sin ART-03/04)
  - [ ] Expediente Tecmater: REGISTRO→PREPARACION directa (skip PRODUCCION). Estado PRODUCCION nunca se visita.
  - [ ] C4 DecideModeBC con brand=tecmater → 409 "Not applicable for Tecmater"
  - [ ] C5 RegisterSAPConfirmation con brand=tecmater → 409 "Not applicable for Tecmater"
  - [ ] Happy path completo Tecmater: REGISTRO→PREPARACION→DESPACHO→TRANSITO→EN_DESTINO→CERRADO (6 estados, skip PRODUCCION)

  **Tests espejo PDF:**
  - [ ] PDF generado contiene solo datos visibility=client
  - [ ] PDF NO contiene FOB, margen, comisión, notas internas
  - [ ] PDF retorna Content-Type: application/pdf
  - [ ] PDF falla gracefully si no hay datos suficientes (retorna 404 con mensaje)

  **Tests regresión:**
  - [ ] Los 20 command endpoints POST de Sprint 1-2 siguen funcionales (no regresión)
  - [ ] Frontend Sprint 3 no tiene regresión visual (smoke test manual)

---

## Dependencias entre items

```
LOTE_SM_SPRINT3 (aprobado)
    │
    ├── Item 1: Migraciones + Modelos (AG-01) ─── puede correr primero
    │       │
    │       ├── Item 2: Costos Doble Vista API (AG-02)
    │       │       │
    │       │       ├── Item 3: ART-09 Factura MWT (AG-02)
    │       │       │       │
    │       │       │       ├── Item 4: Pagos Frontend (AG-03)
    │       │       │       │
    │       │       │       └── Item 5: Modelo Financiero B vs C (AG-02)
    │       │       │
    │       │       └── Item 8: Espejo PDF (AG-02)
    │       │
    │       ├── Item 6: ART-06 + ART-08 Enriched (AG-02 + AG-03)
    │       │
    │       ├── Item 7: ART-19 Decisión Logística (AG-02 + AG-03)
    │       │
    │       └── Item 9: Tecmater Prep (AG-02)
    │
    ├── Item 10: Paperless-ngx (AG-07) ─── paralelo, sin dependencias
    │
    ├── Item 11: Dashboard Financiero (AG-03, después de Items 2+3+5)
    │
    └── Item 12: Tests Sprint 4 (AG-06, después de Items 1-9)
```

**Paralelismo posible:**
- Item 10 (Paperless) es 100% independiente, puede correr en paralelo con todo
- Items 6, 7, 9 dependen solo de Item 1, pueden correr en paralelo entre sí
- Items 2→3→5 y 2→8 son cadenas secuenciales
- Item 4 (frontend pagos) puede correr en paralelo con Item 5 (ambos dependen de Item 3)
- Item 11 (dashboard) necesita esperar Items 2+3+5 (datos financieros disponibles)
- Item 12 (tests) va al final de todo

**Ruta crítica:** Item 1 → Item 2 → Item 3 → Item 5 → Item 11 → Item 12

---

## Criterio de cierre de Sprint 4

Sprint 4 está DONE cuando:

1. Costos doble vista funcional: CEO ve internal, PDF/API client ve solo client
2. ART-09 Factura MWT se genera para expedientes FULL, con payload doble vista + consecutivo automático. En COMISION no se emite ART-09.
3. Pagos con barra de progreso + formulario en frontend
4. Comparativa B vs C retorna escenario real + contrafactual con delta
5. ART-06 y ART-08 con payloads enriquecidos y renderizado en frontend
6. ART-19 funcional: materializar → agregar opciones → decidir (sin auto-suggest)
7. Espejo PDF genera documento limpio solo con datos client-facing
8. Expedientes Tecmater se crean y fluyen sin ART-03/04, REGISTRO→PREPARACION directo
9. Paperless-ngx corriendo (standalone) — si no alcanza, no bloqueante
10. Dashboard con sección financiera: margen, cuentas por cobrar, comparativa
11. Todos los tests de Item 12 passing
12. 20 command endpoints anteriores (Sprint 1-2) siguen funcionales (no regresión)
13. Frontend Sprint 3 sin regresión

**Lo que significa "Sprint 4 DONE":**
- En FULL: el CEO genera factura, cobra, cierra y tiene PDF para el cliente. En COMISION: registra costos, cobra contra OC, compara escenarios; ART-10 (factura comisión) queda para Sprint 5
- Tecmater puede operar en la plataforma (flujo simplificado)
- El sistema tiene 20 + 3 (C22, C23, C24) = 23 command endpoints POST
- Decisiones logísticas se documentan formalmente (no en cabeza del CEO)

**Lo que NO debe existir al cerrar Sprint 4:**
- ART-10 Factura comisión (Sprint 5)
- ART-12 Nota compensación (Sprint 5)
- Conector fiscal FacturaProfesional (Post-MVP)
- RouteHistoricalStats auto-suggest (Sprint 5)
- Portal B2B client-facing (Post-MVP)
- Rana Walk en flujos (Sprint 5+)
- RBAC multi-usuario (Post-MVP)

---

## Qué queda para Sprint 5+

| Feature | Sprint |
|---------|--------|
| ART-10 Factura comisión (modo B completo) | 5 |
| ART-12 Nota compensación | 5 |
| ART-19 auto-suggest desde RouteHistoricalStats | 5 |
| ART-19 tracking links + updates feed | 5 |
| Rana Walk flujo + bifurcación CR/USA | 5+ |
| Paperless-ngx integración API con Django | 5 |
| Conector fiscal FacturaProfesional | Post-MVP |
| Portal B2B (portal.mwt.one → mwt.one RBAC) | Post-MVP |
| Dashboard financiero completo (P&L por marca/cliente) | 5+ |
| Multi-moneda real | Post-MVP |
| Forecast / inteligencia operativa | Post-MVP (6+ meses data) |

---

Stamp: FROZEN v1.3 — Aprobado CEO 2026-03-02
Origen: Derivado de ENT_OPS_STATE_MACHINE v1.2.2 (FROZEN) + PLB_ORCHESTRATOR v1.2.2 (FROZEN) + ENT_PLAT_MVP v1.0 + ENT_PLAT_ARTEFACTOS v1.0 + priorización CEO 2026-03-02
Auditoría: 3 rondas ChatGPT — R1: 8.4/10 (10 fixes) → R2: 9.2/10 (5 fixes) → R3: 9.6/10 (2 fixes). Calificación final 9.6/10.
Changelog: v1.0→v1.1 (endpoint count, ART-09 Modelo B, C13 FROZEN, fórmula comisión, mapping B/C, Tecmater DA-04, InvoiceData→payload, brand_config→services, weasyprint) → v1.2 (C14 COMISION cerrado, pagos dual-mode, comparativa por modo, criterio cierre FULL-only, claim matizado) → v1.3 (dashboard dual-mode, espejo PDF dependencia relajada)
