---
# ASANA_TASK_SPRINT5 — Liquidación Marluvas + Transfer Model + Extensiones Logísticas

sprint: 5  
status: FROZEN v1.3 — Aprobado CEO 2026-03-02  
depends_on: Sprint 4 DONE (LOTE_SM_SPRINT4)  
domain: Plataforma (IDX_PLATAFORMA)

Fuente única de tareas: **LOTE_SM_SPRINT5.md** + **GUIA_EJECUCION_SPRINT5.md**.

---

## Objetivo Sprint 5

- Cerrar ciclo financiero **Modelo B (COMISION)** con reconciliación real de **Liquidaciones Marluvas (ART-10)**.
- Construir entidad **Transfer** (modelo + state machine + commands) como cimiento de Sprint 6 (Rana Walk).

---

## Lista de tareas Sprint 5

> Nota clave de bloqueo: el **parser real** de ART-10 (Fase B) está **bloqueado** hasta recibir una muestra real del Excel de Marluvas (anonimizada si hace falta).

### S5-01 — Transfer model + state machine + migraciones (Item 3)
- Agente: AG-01 Architect
- Prioridad: P0
- Dependencia: Sprint 4 DONE
- Branch sugerido: feature/sprint5-transfers-model
- Qué construir (mínimo):
  - apps/transfers/ (nuevo módulo)
  - Modelos: Node (stub), Transfer, TransferLine
  - Migraciones:
    - CostLine: agregar FK transfer nullable (CostLine pertenece a expediente XOR transfer)
    - Expediente: agregar FK nodo_destino (Node) nullable
- Done:
  - manage.py migrate y check sin errores
  - Modelos visibles en Django Admin
  - No romper CostLines existentes

### S5-02 — Transfer commands backend C30–C35 + reads (Item 3B)
- Agente: AG-02 API Builder
- Prioridad: P0
- Dependencia: S5-01 aprobado
- Branch sugerido: feature/sprint5-transfers-api
- Implementar commands:
  - C30 CreateTransfer (POST /api/transfers/)
  - C31 ApproveTransfer
  - C32 DispatchTransfer (regla puente: confirmación manual CEO; sin ART-15)
  - C33 ReceiveTransfer (regla puente: confirmación manual; sin ART-13)
  - C34 ReconcileTransfer (si discrepancias: solo CEO + exception_reason obligatorio)
  - C35 CancelTransfer
- Reads:
  - GET /api/transfers/ (CEO-ONLY)
  - GET /api/transfers/{id}/
- Eventos: transfer.created / approved / dispatched / received / reconciled / cancelled

### S5-03 — ART-10 Liquidación Marluvas: Fase A (modelo + upload + parser stub) (Item 1 parcial)
- Agente: AG-02 API Builder
- Prioridad: P0
- Dependencia: Sprint 4 DONE
- Branch sugerido: feature/sprint5-liquidations-phase-a
- Crear módulo apps/liquidations/ con:
  - Modelos Liquidation + LiquidationLine
  - C25 UploadLiquidation (POST /api/liquidations/upload/): guarda el archivo siempre, intenta parsear; si falla → lines vacías + error_log
  - Parser stub en parsers.py (retorna [] y loguea “awaiting sample file”)
  - Reads: GET /api/liquidations/, /{id}/, /{id}/lines/
- Restricción: ART-10 es CROSS, no tocar apps/expedientes/models.py

### S5-04 — ART-10 Liquidación Marluvas: Fase B (parser real + match + reconcile/dispute) (Item 1 completo)
- Agente: AG-02 API Builder
- Prioridad: P0
- Dependencia: S5-03 + **muestra real Excel Marluvas**
- Branch sugerido: feature/sprint5-liquidations-phase-b
- Implementar:
  - Parser real (mapeo de columnas reales; NO inventar)
  - C26 ManualMatchLine
  - C27 ReconcileLiquidation
  - C28 DisputeLiquidation
  - Match automático por marluvas_reference vs ART-02.payload.consecutive (si match único)
  - Tolerancias configurables:
    - monto: ±1% o ±$5 USD (mayor)
    - pct comisión: ±0.5 pp
  - Tracking acumulado por proforma: SUM commission_amount histórico

### S5-05 — ART-12 Nota compensación: backend + frontend (Item 2)
- Agente: AG-02 API Builder + AG-03 Frontend
- Prioridad: P1
- Dependencia: Sprint 4 DONE
- Branch sugerido: feature/sprint5-art12-compensation
- Implementar:
  - C29 RegisterCompensation: POST /api/expedientes/{id}/register-compensation/
  - C20 VoidArtifact ya existe: ART-12 debe ser voidable
  - CEO-ONLY: nunca en vista client ni PDF espejo
  - Frontend: card solo si ART-12 existe (no mostrar vacía)

### S5-06 — Handoff Expediente → Transfer (Item 4)
- Agente: AG-02 API Builder + AG-03 Frontend
- Prioridad: P1
- Dependencia: S5-02 aprobado
- Branch sugerido: feature/sprint5-handoff-expediente-transfer
- Comportamiento:
  - Al cerrar expediente (C14) si expediente.nodo_destino != null → crear sugerencia (NO automático)
  - Card en expediente cerrado: “¿Crear transfer?”
  - CEO confirma → ejecuta C30 CreateTransfer con source_expediente

### S5-07 — ART-19 RouteHistoricalStats auto-suggest (Item 5)
- Agente: AG-02 API Builder (+ frontend sección)
- Prioridad: P2
- Dependencia: Sprint 4 DONE (ART-19 básico)
- Branch sugerido: feature/sprint5-art19-autosuggest
- Implementar:
  - GET /api/expedientes/{id}/logistics-suggestions/ (CEO-ONLY)
  - Requiere mínimo 5 expedientes cerrados con ART-19 completed; si no → lista vacía + “Insufficient historical data”
  - Frontend: sección “Sugerencias basadas en histórico” solo si hay data; botón “Agregar como opción” ejecuta C23

### S5-08 — ART-19 tracking links + updates feed (Item 6)
- Agente: AG-02 API Builder + AG-03 Frontend
- Prioridad: P2
- Dependencia: Sprint 4 DONE (ART-05 + ART-19)
- Branch sugerido: feature/sprint5-shipment-updates
- Implementar:
  - Extender ART-05 payload: tracking_url, sub_legs[], updates[]
  - C36 AddShipmentUpdate: POST /api/expedientes/{id}/add-shipment-update/
  - Frontend: timeline de updates en TRANSITO + botón abre tracking_url
  - Scope: updates manuales (carrier APIs post-MVP)

### S5-09 — Paperless-ngx integración API (Item 7)
- Agente: AG-02 API Builder
- Prioridad: P2 (no bloqueante)
- Dependencia: Paperless standalone Sprint 4 Item 10
- Branch sugerido: feature/sprint5-paperless-integration
- Implementar:
  - Client HTTP apps/integrations/paperless.py
  - Hook: al completar ArtifactInstance con archivo adjunto (solo artefactos con FK expediente) → auto-upload con tags
  - Excluir ART-10 (CROSS)
  - Si Paperless falla/no corre → log y seguir (no bloquear)
  - Unidireccional Django → Paperless

### S5-10 — Refinar C21 modo B: pagos alineados con liquidación (Item 8)
- Agente: AG-02 API Builder + AG-03 Frontend
- Prioridad: P1
- Dependencia: S5-03 (estructura ART-10) idealmente S5-04 (reconciliación real)
- Branch sugerido: feature/sprint5-c21-comision-refine
- Cambios:
  - reference_total en COMISION = comisión esperada (ART-02.comision_pactada × ART-01.total_po / 100), NO total_po
  - Soportar pagos parciales múltiples
  - payment_status=paid cuando SUM(PaymentLines.amount) >= comisión_esperada
  - Desde Liquidation reconciliada: sugerir registrar pago (card) y al confirmar ejecutar C21 con method=liquidacion_marluvas, reference=liquidation_id
  - Frontend: badge y barra de progreso basados en comisión esperada
  - Backward compatible: pago manual sin liquidación sigue funcionando

### S5-11 — Tests Sprint 5 (Item 9)
- Agente: AG-04 QA
- Prioridad: P0
- Dependencia: S5-01 a S5-10
- Branch sugerido: feature/sprint5-tests
- Cobertura mínima:
  - ART-10: upload ok; upload parse fail guarda archivo + error_log; match auto; C26; C27; C28; tolerancias; premio no_match_needed
  - ART-12: C29 + void C20 + no visible client/PDF
  - Transfer: C30–C35 happy path + discrepancias + exception_reason
  - Handoff: con y sin nodo_destino
  - ART-19: autosuggest 5+ vs <5; C36 updates
  - C21 COMISION refinado + sugerencia desde liquidación + backward compatibility
  - Regresión: 23 endpoints Sprint 1–4 y frontend Sprint 3–4

---

## Orden recomendado (según GUIA_EJECUCION_SPRINT5)

1) S5-01 → 2) S5-02 → 3) S5-03 → 4) S5-05 → 5) S5-06 → 6) S5-04 (cuando haya Excel) → 7) S5-07/S5-08/S5-09 (paralelo) → 8) S5-10 → 9) S5-11

---

Stamp: ASANA_TASK_SPRINT5 v1.0 — 2026-03-03
