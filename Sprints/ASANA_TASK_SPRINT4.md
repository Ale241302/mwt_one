# ASANA_TASK_SPRINT4.md

```
sprint: 4
status: FROZEN v1.3 — Aprobado CEO 2026-03-02
domain: Plataforma (IDX_PLATAFORMA)
depends_on: LOTE_SM_SPRINT3 (todos los items aprobados)
refs: ENT_OPS_STATE_MACHINE v1.2.2, PLB_ORCHESTRATOR v1.2.2, ENT_PLAT_ARTEFACTOS v1.0, ENT_COMERCIAL_MODELOS, SCH_PROFORMA_MWT v1.0, ENT_OPS_EXPEDIENTE v2.0, ENT_PLAT_MVP v1.0
```

# ASANA_TASK_SPRINT4 — Costos Doble Vista + Factura MWT + Artefactos Logísticos + Financiero + Tecmater

**Objetivo:** Cerrar el ciclo financiero completo de un expediente — el CEO ve costos reales vs precio cliente, genera factura, compara modelos B vs C retroactivamente, y tiene un PDF espejo listo para el cliente. Se amplía el catálogo de artefactos operativos y se prepara la plataforma para Tecmater.

**Precondición:** Sprint 3 DONE — Frontend básico funcional, 20 command endpoints funcionales.

## Resumen de Items

| ID | Tarea | Agente | Prioridad | Branch |
| --- | --- | --- | --- | --- |
| S4-01 | Migraciones + Modelo Costos Doble Vista | AG-01 Architect | P0 | feature/sprint4-cost-model |
| S4-02 | Costos Doble Vista: API + Lógica | AG-02 API Builder | P0 | feature/sprint4-costs-api |
| S4-03 | ART-09 Factura MWT: Generación + Doble Vista | AG-02 API Builder | P0 | feature/sprint4-invoice-art09 |
| S4-04 | Pagos: Vista Frontend | AG-03 Frontend | P0 | feature/sprint4-payments-frontend |
| S4-05 | Modelo Financiero Escenario 2: Comparativa B vs C | AG-02 API Builder | P1 | feature/sprint4-financial-comparison |
| S4-06 | ART-06 + ART-08: Payload Enriquecido + Frontend | AG-02 + AG-03 | P1 | feature/sprint4-art06-art08 |
| S4-07 | ART-19 Decisión Logística: Backend + Frontend Básico | AG-02 + AG-03 | P2 | feature/sprint4-art19-logistics |
| S4-08 | Espejo Documental PDF | AG-02 API Builder | P1 | feature/sprint4-mirror-pdf |
| S4-09 | Tecmater Prep: Brand Parametrización | AG-02 API Builder | P2 | feature/sprint4-tecmater |
| S4-10 | Paperless-ngx Docker | AG-07 DevOps | P3 | feature/sprint4-paperless |
| S4-11 | Dashboard Financiero Básico | AG-03 Frontend | P1 | feature/sprint4-dashboard-financiero |
| S4-12 | Tests Sprint 4 | AG-06 QA | P0 | feature/sprint4-tests |

## Ruta Crítica

```
S4-01 → S4-02 → S4-03 → S4-05 → S4-11 → S4-12
```

Paralelismo posible:

- S4-10 (Paperless) — 100% independiente, sin bloqueo
- S4-06, S4-07, S4-09 — dependen solo de S4-01, paralelos entre sí
- S4-04 y S4-05 — ambos dependen de S4-03, pueden correr en paralelo
- S4-08 — depende de S4-02 (S4-03 solo aporta bloque factura opcional)

## S4-01 — Migraciones + Modelo Costos Doble Vista

- **Agente:** AG-01 Architect | **Prioridad:** P0
- **Branch:** `feature/sprint4-cost-model`
- **Dependencia:** Sprint 3 DONE
- **Archivos:** `models.py`, `enums.py` — Prohibidos: `views.py`, `services.py`, `tests/`

**Criterios de Done:**

- [ ]  CostLine.visibility: enum (internal | client) — si falta, migración
- [ ]  CostLine.phase: string — si falta, migración
- [ ]  NO crear modelo InvoiceData — usar ArtifactInstance.payload (jsonb)
- [ ]  Modelo LogisticsOption creado: artifact_instance_id, option_id, mode, carrier, route, estimated_days, estimated_cost, currency, valid_until, source, is_selected
- [ ]  brand=tecmater en enum Expediente — si falta, migración
- [ ]  [manage.py](http://manage.py) migrate sin errores
- [ ]  [manage.py](http://manage.py) check sin errores
- [ ]  Nuevos modelos visibles en Django Admin

**Riesgos:** Si CostLine.visibility ya existe, verificar integridad antes de migrar.

## S4-02 — Costos Doble Vista: API + Lógica

- **Agente:** AG-02 API Builder | **Prioridad:** P0
- **Branch:** `feature/sprint4-costs-api`
- **Dependencia:** S4-01 aprobado
- **Archivos:** `serializers.py`, `views.py`, `services.py` — Prohibidos: `models.py`, `tests/`

**Criterios de Done:**

- [ ]  GET /api/expedientes/{id}/costs/?view=internal → todas las CostLines (CEO-only)
- [ ]  GET /api/expedientes/{id}/costs/?view=client → solo visibility=client
- [ ]  Default sin parámetro → internal (MVP)
- [ ]  GET /api/expedientes/{id}/costs/summary/ → total_internal, total_client, margin, margin_pct
- [ ]  C15 RegisterCostLine acepta visibility en input (default: internal)
- [ ]  Serializer incluye visibility en read y write

**Riesgos:** Validar campo visibility en modelo antes de filtrar.

## S4-03 — ART-09 Factura MWT: Generación + Doble Vista

- **Agente:** AG-02 API Builder | **Prioridad:** P0
- **Branch:** `feature/sprint4-invoice-art09`
- **Dependencia:** S4-02 aprobado
- **Archivos:** `services.py`, `serializers.py`, `views.py` — Prohibidos: `models.py`, `tests/`

**Criterios de Done:**

- [ ]  POST /api/expedientes/{id}/issue-invoice/ → C13 (contrato FROZEN)
- [ ]  GET /api/expedientes/{id}/invoice-suggestion/ → helper pre-calcula total sugerido
- [ ]  Payload ART-09 en ArtifactInstance.payload: consecutive (MWT-YYYY-NNNN), lines[], total_client_view, total_internal_view [CEO-ONLY], currency, issued_to, margin [CEO-ONLY], margin_pct [CEO-ONLY]
- [ ]  GET /api/expedientes/{id}/invoice/?view=internal|client → doble vista
- [ ]  Modelo COMISION → C13 retorna 409 "ART-09 not applicable for mode COMISION"
- [ ]  Evento invoice.issued disparado
- [ ]  Consecutivo persiste y auto-incrementa por LegalEntity

**Riesgos:** NO crear InvoiceData. Contrato C13 FROZEN: expediente_id, total_client_view, currency.

## S4-04 — Pagos: Vista Frontend

- **Agente:** AG-03 Frontend | **Prioridad:** P0
- **Branch:** `feature/sprint4-payments-frontend`
- **Dependencia:** S4-03 aprobado
- **Archivos:** `frontend/pages` o `components` — Prohibidos: `models.py`, `services.py`

**Criterios de Done:**

- [ ]  Panel pagos: lista PaymentLines (monto, método, referencia, fecha)
- [ ]  Barra progreso: rojo <50%, amarillo <100%, verde =paid
- [ ]  reference_total = [ART-09.total](http://ART-09.total)_client_view (FULL) o [ART-01.total](http://ART-01.total)_po (COMISION)
- [ ]  Badge COMISION: "Marluvas factura directo — pago registrado contra OC"
- [ ]  Formulario C21: amount, currency pre-llenado, method dropdown, reference
- [ ]  C21 backend en COMISION: precondición ART-09 se relaja a ART-01
- [ ]  Panel se actualiza tras registrar pago
- [ ]  payment_status=paid → botón "Cerrar expediente" (C14) habilitado

## S4-05 — Modelo Financiero Escenario 2: Comparativa B vs C

- **Agente:** AG-02 API Builder | **Prioridad:** P1
- **Branch:** `feature/sprint4-financial-comparison`
- **Dependencia:** S4-02 aprobado; S4-03 para FULL
- **Archivos:** `services.py`, `serializers.py`, `views.py` — Prohibidos: `models.py`, `tests/`

**Criterios de Done:**

- [ ]  GET /api/expedientes/{id}/financial-comparison/ [CEO-ONLY]
- [ ]  FULL requiere ART-09; COMISION requiere ART-02 + CostLines
- [ ]  Sin datos mínimos → 409 "Insufficient data for comparison"
- [ ]  Response: actual_mode, actual {revenue, cost, margin, margin_pct}, counterfactual_mode, counterfactual, delta {margin, recommendation}
- [ ]  Fórmula: ingreso_B = comision_pactada * total_po / 100 (fuente: ART-02)
- [ ]  Sin comision_pactada → 409
- [ ]  Código: COMISION/FULL (no B/C)

## S4-06 — ART-06 + ART-08: Payload Enriquecido + Frontend

- **Agente:** AG-02 + AG-03 | **Prioridad:** P1
- **Branch:** `feature/sprint4-art06-art08`
- **Dependencia:** S4-01 aprobado
- **Archivos:** `serializers.py`, frontend components — Prohibidos: `models.py`

**Criterios de Done — ART-06 (C8):**

- [ ]  Payload extendido: transport_mode (aereo|maritimo), carrier, quote_reference, valid_until, notes
- [ ]  Frontend: card en vista PREPARACION

**Criterios de Done — ART-08 (C9):**

- [ ]  Payload: ncm_codes jsonb[], total_dai_pct, permits[], customs_agent, estimated_cost, currency, notes
- [ ]  Card solo visible si dispatch_mode=mwt
- [ ]  C9 con dispatch_mode=client → 409

**Riesgos:** No crear endpoints nuevos — extensiones de C8/C9 existentes (DA-02).

## S4-07 — ART-19 Decisión Logística: Backend + Frontend Básico

- **Agente:** AG-02 + AG-03 | **Prioridad:** P2
- **Branch:** `feature/sprint4-art19-logistics`
- **Dependencia:** S4-01 aprobado
- **Archivos:** `services.py`, `serializers.py`, `views.py`, `urls.py`, frontend

**Criterios de Done:**

- [ ]  C22 MaterializeLogistics: POST /api/expedientes/{id}/materialize-logistics/ — precond: ART-04 exists, status ∈ {PRODUCCION, PREPARACION}
- [ ]  C23 AddLogisticsOption: POST /api/expedientes/{id}/add-logistics-option/ — inserta LogisticsOption
- [ ]  C24 DecideLogistics: POST /api/expedientes/{id}/decide-logistics/ — is_selected=true + ART-19 status→completed
- [ ]  Frontend: cards por opción, badge source, botón Decidir
- [ ]  Breakeven básico si ≥1 aérea + ≥1 marítima
- [ ]  Eventos: logistics.materialized, logistics.option_added, logistics.decided

**NO hacer:** RouteHistoricalStats auto-suggest, portal client, tracking links, sub-tramos.

## S4-08 — Espejo Documental PDF

- **Agente:** AG-02 API Builder | **Prioridad:** P1
- **Branch:** `feature/sprint4-mirror-pdf`
- **Dependencia:** S4-02 aprobado
- **Archivos:** `services.py` (módulo PDF), `views.py`, + weasyprint — Prohibidos: `models.py`

**Criterios de Done:**

- [ ]  GET /api/expedientes/{id}/mirror-pdf/ genera PDF dinámico
- [ ]  Solo datos visibility=client: header, líneas producto (SKUAlias), costos client, factura resumen (si ART-09), timeline, tracking
- [ ]  NO contiene: FOB, costos internal, margen, comisión, notas internas, ART-12
- [ ]  Branded: Navy #013A57 + Mint #75CBB3
- [ ]  Content-Type: application/pdf
- [ ]  Sin datos → 404 con mensaje

**Riesgos:** weasyprint requiere instalación en Dockerfile.

## S4-09 — Tecmater Prep: Brand Parametrización

- **Agente:** AG-02 API Builder | **Prioridad:** P2
- **Branch:** `feature/sprint4-tecmater`
- **Dependencia:** S4-01 aprobado
- **Archivos:** `services.py`, `enums.py`, `serializers.py` — Prohibidos: `tests/`

**Criterios de Done:**

- [ ]  C1 acepta brand=tecmater
- [ ]  brand=tecmater → mode=FULL forzado (no acepta COMISION)
- [ ]  Skip ART-03, ART-04, ART-10, ART-19 en Tecmater
- [ ]  T2 Tecmater = REGISTRO→PREPARACION directo (skip PRODUCCION)
- [ ]  can_transition_to() y execute_command() respetan brand config
- [ ]  C4 + tecmater → 409; C5 + tecmater → 409
- [ ]  Happy path: REGISTRO→PREPARACION→DESPACHO→TRANSITO→EN_DESTINO→CERRADO (6 estados)

**Riesgos:** Solo lógica condicional en [services.py](http://services.py), sin máquina de estados nueva (DA-04).

## S4-10 — Paperless-ngx Docker

- **Agente:** AG-07 DevOps | **Prioridad:** P3 — NO BLOQUEANTE
- **Branch:** `feature/sprint4-paperless`
- **Dependencia:** Ninguna — 100% paralelo
- **Archivos:** `docker-compose.yml`, `.env` — Prohibidos: `apps/*`, `tests/*`

**Criterios de Done:**

- [ ]  Contenedor Paperless-ngx en docker-compose
- [ ]  Volumen persistente
- [ ]  Accesible via nginx /paperless/
- [ ]  Usuario admin creado
- [ ]  API token configurable en .env
- [ ]  Health check funcional
- [ ]  NO integrado con Django — standalone
- [ ]  README con instrucciones

**Nota:** Si no alcanza, Drive sigue válido. Integración API → Sprint 5.

## S4-11 — Dashboard Financiero Básico

- **Agente:** AG-03 Frontend | **Prioridad:** P1
- **Branch:** `feature/sprint4-dashboard-financiero`
- **Dependencia:** S4-02, S4-03, S4-05 aprobados
- **Archivos:** frontend dashboard — Prohibidos: `models.py`

**Criterios de Done:**

- [ ]  Extensión dashboard Sprint 3 (NO pantalla nueva)
- [ ]  Card Margen: verde >15%, amarillo 5-15%, rojo <5%
- [ ]  Card Totales activos: facturas + comisiones proyectadas + costos + margen
- [ ]  Card Cuentas por cobrar: payment_status ≠ paid, días desde factura/OC, monto pendiente
- [ ]  Card Comparativa B vs C: delta para expedientes cerrados
- [ ]  Filtros: marca, estado, rango de fechas
- [ ]  Semáforo: margen <5% → ⚠️ Margen bajo; cobro >60d → ⚠️ Cobro atrasado

## S4-12 — Tests Sprint 4

- **Agente:** AG-06 QA | **Prioridad:** P0
- **Branch:** `feature/sprint4-tests`
- **Dependencia:** S4-01 a S4-09 aprobados
- **Archivos:** `tests/test_costs_dual_view.py`, `test_invoice.py`, `test_financial.py`, `test_logistics.py`, `test_tecmater.py`, `test_mirror_pdf.py` — Prohibidos: `apps/*`

**Criterios de Done:**

- [ ]  Tests costos: visibility=internal invisible en ?view=client; visibility=client visible en ambas; summary calcula margin_pct; C15 persiste visibility
- [ ]  Tests ART-09: C13 crea ART-09 en EN_DESTINO (FULL); consecutivo auto-incrementa; vista client oculta [CEO-ONLY]; Modelo B → 409
- [ ]  Tests financiero: FULL con ART-09 simula B; COMISION sin ART-09 simula C; sin datos → 409
- [ ]  Tests ART-19: C22/C23/C24 happy path; failures correctos; breakeven
- [ ]  Tests ART-06/08: payload extendido persiste; dispatch_mode=client → 409
- [ ]  Tests Tecmater: brand forzado FULL; T2 skip PRODUCCION; C4/C5 → 409; happy path 6 estados
- [ ]  Tests PDF: solo datos client; NO FOB/margen; Content-Type correcto; sin datos → 404
- [ ]  Regresión: 20 endpoints Sprint 1-2 funcionales; frontend Sprint 3 sin regresión

## Criterio de Cierre Sprint 4

Sprint 4 está DONE cuando los 13 criterios de cierre definidos en LOTE_SM_[SPRINT4.md](http://SPRINT4.md) están cumplidos. El sistema tendrá 23 command endpoints POST (20 previos + C22, C23, C24). En FULL: CEO genera factura, cobra, cierra y tiene PDF para el cliente. En COMISION: registra costos, cobra contra OC, compara escenarios. Tecmater opera en flujo simplificado.

```
Stamp: ASANA_TASK_SPRINT4 v1.0 — Generado 2026-03-02
Origen: LOTE_SM_SPRINT4 FROZEN v1.3
Notion DB: https://www.notion.so/da371f66c043401b823996e8e23efaf5?v=d9cbefcb5b5246cd8e5e9fa1051bac7d
```