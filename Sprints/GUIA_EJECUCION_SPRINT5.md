# Guía de Ejecución — Sprint 5
**Para:** Alejandro (AG-03)
**De:** Alvaro (CEO / Orquestador)
**Fecha:** 2026-03-03
**Spec de referencia:** LOTE_SM_SPRINT5 v1.3 (FROZEN)

---

## Contexto rápido

Sprint 5 tiene dos pilares:
1. **Liquidación Marluvas (ART-10):** Subir el Excel mensual de Marluvas, parsear líneas, hacer match contra proformas del sistema, reconciliar.
2. **Transfer model:** Nueva entidad con su propia state machine (6 estados). Es el cimiento para Rana Walk en Sprint 6.

Secundarios: ART-12 compensación, extensiones ART-19 (auto-suggest + tracking), Paperless integración, y refinamiento de pagos modo B.

**Total nuevos endpoints:** 12 commands (C25-C36). Post-Sprint 5 = 35 POST totales.

---

## Precondiciones antes de arrancar

- [ ] Sprint 4 desplegado y funcional (23 POST endpoints, dashboard financiero, ART-19 básico, Tecmater, PDF espejo)
- [ ] Branch limpio desde main (post-Sprint 4)
- [ ] Paperless-ngx standalone corriendo (Sprint 4 Item 10). Si no → Item 7 se salta sin bloquear nada.
- [ ] Pedir a Alvaro muestra del Excel de Marluvas **antes de llegar a Fase B del Item 1**. Sin muestra, el parser queda como stub.

---

## Orden de ejecución

```
Fase 1 — Modelos (AG-01 role)
    │
    ├── PASO 1: Item 3 — Transfer model + migraciones
    │       └── PASO 2: Item 3B — Transfer commands (C30-C35)
    │               └── PASO 5: Item 4 — Handoff expediente→transfer
    │
    ├── PASO 3: Item 1 Fase A — ART-10 Liquidation model + upload stub
    │       └── PASO 6: Item 1 Fase B — Parser real (BLOQUEADO hasta muestra Excel)
    │               └── PASO 8: Item 8 — C21 modo B refinado
    │
    └── PASO 4: Item 2 — ART-12 compensación

Fase 2 — Extensiones (paralelo posible)
    ├── PASO 7: Item 5 — ART-19 auto-suggest
    ├── PASO 7: Item 6 — Tracking links + updates
    └── PASO 7: Item 7 — Paperless integración (si aplica)

Fase 3 — Cierre
    └── PASO 9: Item 9 — Tests
```

---

## PASO 1 — Transfer model + state machine (Item 3)

**Qué hacer:** Crear módulo Django `apps/transfers/` con modelos y migraciones.

**Archivos a crear:**
- `apps/transfers/__init__.py`
- `apps/transfers/models.py`
- `apps/transfers/enums.py`
- `apps/transfers/admin.py`
- `apps/transfers/apps.py`

**Modelos a implementar:**

1. **Node** (stub mínimo):
   - `node_id`, `name`, `legal_entity` (FK LegalEntity), `node_type` (enum: fiscal, owned_warehouse, fba, third_party, factory), `location`, `status`

2. **Transfer:**
   - `transfer_id` (auto TRF-YYYYMMDD-XXX)
   - `from_node`, `to_node` (FK Node)
   - `ownership_before`, `ownership_after` (FK LegalEntity)
   - `ownership_changes` (boolean, calculado)
   - `legal_context` (enum: internal, nationalization, reexport, distribution, consignment)
   - `customs_required` (boolean)
   - `pricing_context` (jsonb nullable)
   - `source_expediente` (FK Expediente nullable)
   - `status` (enum: planned, approved, in_transit, received, reconciled, cancelled)
   - timestamps

3. **TransferLine:**
   - FK Transfer, `sku`, `quantity_dispatched`, `quantity_received` (nullable), `discrepancy` (computed), `condition` (enum: good, damaged, partial, nullable)

4. **CostLine** — agregar FK transfer nullable al CostLine existente. Un CostLine pertenece a expediente XOR transfer, nunca ambos.

5. **Expediente** — agregar campo `nodo_destino` (FK Node, nullable). Migración no destructiva.

**Criterio de done:**
- `python manage.py migrate` sin errores
- `python manage.py check` sin errores
- Modelos visibles en Django Admin
- CostLines existentes de expedientes no rotos
- NO tocar: views.py, services.py, serializers.py, tests

---

## PASO 2 — Transfer commands (Item 3B)

**Qué hacer:** Endpoints CRUD + state machine para Transfer.

**Archivos a crear:**
- `apps/transfers/services.py`
- `apps/transfers/serializers.py`
- `apps/transfers/views.py`
- `apps/transfers/urls.py`

**6 commands nuevos:**

| Command | Endpoint | Precondición | Mutación |
|---------|----------|--------------|----------|
| C30 CreateTransfer | `POST /api/transfers/` | from ≠ to, nodos existen | INSERT Transfer (planned) + lines. Auto-calcula ownership_before/after y customs_required |
| C31 ApproveTransfer | `POST /api/transfers/{id}/approve/` | status=planned, CEO only | → approved |
| C32 DispatchTransfer | `POST /api/transfers/{id}/dispatch/` | status=approved | → in_transit (regla puente: confirmación manual, no ART-15) |
| C33 ReceiveTransfer | `POST /api/transfers/{id}/receive/` | status=in_transit | Input: lines[] con quantity_received + condition. → received |
| C34 ReconcileTransfer | `POST /api/transfers/{id}/reconcile/` | status=received, ver regla abajo | → reconciled |
| C35 CancelTransfer | `POST /api/transfers/{id}/cancel/` | status ∈ {planned, approved}, CEO only | → cancelled + reason |

**Regla reconcile (C34) — IMPORTANTE:**
- Si todas las líneas: quantity_received informada Y quantity_dispatched == quantity_received → cualquier usuario puede reconciliar.
- Si hay discrepancias → **solo CEO** + `exception_reason` obligatorio. Registrar en event_log.

**Read endpoints:**
- `GET /api/transfers/` — lista paginada [CEO-ONLY]
- `GET /api/transfers/{id}/` — detalle con líneas, costos, nodos

**Eventos a emitir:** transfer.created, transfer.approved, transfer.dispatched, transfer.received, transfer.reconciled, transfer.cancelled

**NO hacer:** Artefactos de Transfer (ART-13 a ART-17) — Sprint 6. Frontend Transfer — Sprint 6.

---

## PASO 3 — ART-10 Liquidación Marluvas, Fase A (Item 1 parcial)

**Qué hacer:** Crear módulo `apps/liquidations/` con modelo, upload y stub de parser.

**Archivos a crear:**
- `apps/liquidations/__init__.py`, `models.py`, `services.py`, `serializers.py`, `views.py`, `urls.py`, `parsers.py`, `admin.py`, `apps.py`

**Modelos:**

1. **Liquidation:**
   - `liquidation_id` (auto LIQ-YYYY-MM-NNN)
   - `period` (YYYY-MM), `brand` = "marluvas"
   - `source_file` (FileField — el Excel original)
   - `status` (enum: pending, in_review, reconciled, disputed)
   - totales calculados, timestamps

2. **LiquidationLine:**
   - FK Liquidation
   - `marluvas_reference`, `concept` (enum: comision, premio, ajuste, otro)
   - `client_payment_amount`, `commission_pct_reported`, `commission_amount`, `currency`
   - `is_partial_payment`
   - `matched_proforma_id` (nullable FK ArtifactInstance donde type=ART-02)
   - `matched_expediente_id` (nullable FK Expediente — derivado del proforma)
   - `commission_pct_expected` (nullable — de ART-02.payload.comision_pactada)
   - `match_status` (enum: matched, discrepancy, unmatched, no_match_needed)
   - `observation`

**Commands Fase A (ejecutable sin muestra Excel):**

| Command | Endpoint | Nota |
|---------|----------|------|
| C25 UploadLiquidation | `POST /api/liquidations/upload/` | Acepta file + period. Crea Liquidation status=pending. Intenta parsear → si falla, lines vacías + error_log. El archivo siempre se guarda. |

**Parser stub (parsers.py):**
```python
def parse_marluvas_excel(file) -> list[dict]:
    """
    Contrato: recibe archivo Excel, retorna lista de dicts.
    STUB: retorna [] + loguea "Parser not configured - awaiting sample file"
    Fase B reemplaza con mapeo real de columnas.
    """
    return []
```

**Read endpoints:**
- `GET /api/liquidations/` — lista paginada [CEO-ONLY]
- `GET /api/liquidations/{id}/` — detalle con líneas
- `GET /api/liquidations/{id}/lines/` — líneas con match expandido

**Migraciones.** `python manage.py migrate` sin errores.

---

## PASO 4 — ART-12 Compensación (Item 2)

**Qué hacer:** Un command simple. Usa ArtifactInstance existente.

**Command:**
- C29 RegisterCompensation: `POST /api/expedientes/{id}/register-compensation/`
- Input: `items[]` (description, quantity, estimated_value), `notes`
- Precondiciones: expediente exists, status ≠ CERRADO ni CANCELADO, CEO only
- Mutación: INSERT ArtifactInstance (type=ART-12, status=completed, payload con items + total_estimated_value)
- Evento: compensation.noted
- Voidable con C20 existente

**Frontend:**
- Card en detalle expediente, solo si usuario es CEO y ART-12 existe
- Si no existe → no mostrar card vacía
- [CEO-ONLY] completo — nunca en vista client ni PDF espejo

---

## PASO 5 — Handoff expediente→transfer (Item 4)

**Qué hacer:** Cuando expediente cierra (C14) y tiene `nodo_destino`, sugerir crear Transfer.

**Lógica:**
1. C14 CloseExpediente ejecuta side effect: si `expediente.nodo_destino` no es null → generar sugerencia
2. Sugerencia = card en vista del expediente cerrado: *"Producto entregado a [nodo]. ¿Crear transfer?"*
3. CEO confirma → ejecuta C30 CreateTransfer con `source_expediente=expediente_id`, `from_node=nodo_destino`, items del expediente
4. CEO ignora → nada pasa

**Reglas:**
- No es automático. CEO siempre confirma.
- Sin `nodo_destino` → sin sugerencia
- `nodo_destino` se asigna durante el expediente (campo agregado en PASO 1)

---

## PASO 6 — ART-10 Fase B: Parser real (Item 1 continuación)

**⚠️ BLOQUEADO hasta que Alvaro entregue muestra del Excel de Marluvas.**

**Qué hacer cuando llegue la muestra:**
1. Mapear columnas reales del Excel → campos de LiquidationLine
2. Implementar parser real en `parsers.py` reemplazando el stub
3. Test: parsear muestra → líneas extraídas correctamente

**Commands restantes:**

| Command | Endpoint | Detalle |
|---------|----------|---------|
| C26 ManualMatchLine | `POST /api/liquidations/{id}/match-line/` | Input: line_id + proforma_id. Actualiza matched_proforma_id, matched_expediente_id (derivado), commission_pct_expected (de ART-02.payload.comision_pactada), recalcula match_status |
| C27 ReconcileLiquidation | `POST /api/liquidations/{id}/reconcile/` | Precondición: todas las líneas concept=comision tienen match_status ∈ {matched, no_match_needed}. Premiaciones no necesitan match. → status=reconciled |
| C28 DisputeLiquidation | `POST /api/liquidations/{id}/dispute/` | Input: observations. → status=disputed |

**Match automático (al upload exitoso):**
- Para cada línea concept=comision: buscar ART-02 donde payload.consecutive ILIKE marluvas_reference
- Match único → auto-asignar
- Match múltiple o ninguno → unmatched (CEO resuelve con C26)
- Premiaciones → no_match_needed automático

**Tolerancias (configurables en settings):**
- Monto: ±1% o ±$5 USD (lo que sea mayor)
- Porcentaje comisión: ±0.5 puntos porcentuales
- Dentro → matched. Fuera → discrepancy.

**Tracking acumulado:**
- Vista por proforma: total liquidado históricamente (SUM commission_amount en todas las liquidaciones donde matched_proforma_id = X)

---

## PASO 7 — Extensiones (paralelo posible)

Estos tres items son independientes entre sí. Pueden ejecutarse en cualquier orden o en paralelo.

### Item 5: ART-19 auto-suggest

- `GET /api/expedientes/{id}/logistics-suggestions/` [CEO-ONLY]
- Busca expedientes cerrados con ART-19 completed, misma ruta, misma marca, volumen ±30%
- Retorna top 3-5 opciones históricas (carrier, modo, costo promedio, días, frecuencia)
- Si < 5 expedientes históricos → lista vacía con "Insufficient historical data"
- Frontend: sección "Sugerencias basadas en histórico" arriba de opciones manuales. Botón "Agregar como opción" → pre-llena C23
- Sin data → sección no aparece

### Item 6: Tracking links + updates

- Extender ART-05 payload con: `tracking_url`, `sub_legs[]`, `updates[]`
- C36 AddShipmentUpdate: `POST /api/expedientes/{id}/add-shipment-update/`
  - Input: description, source (manual | carrier_api)
  - Precondición: ART-05 exists, status ∈ {DESPACHO, TRANSITO, EN_DESTINO}
  - Mutación: APPEND a ART-05.payload.updates[]
  - Evento: shipment.updated
- Frontend: timeline de updates en vista TRANSITO, botón tracking link abre URL
- Sprint 5 = updates manuales. APIs de carriers = Post-MVP.

### Item 7: Paperless-ngx integración

- Crear `apps/integrations/paperless.py` — client HTTP para API de Paperless
- Hook: cuando ArtifactInstance de expediente se completa con archivo adjunto → auto-upload a Paperless con tags [expediente_id, artifact_type, brand, period]
- Solo artefactos con FK expediente. ART-10 (CROSS) se excluye del hook.
- Si Paperless no responde → log error, NO bloquear operación
- Si Paperless no está corriendo → silently skip
- Unidireccional: Django → Paperless. Sin retorno.

---

## PASO 8 — C21 modo B refinado (Item 8)

**Dependencia:** Item 1 (Fase B idealmente, pero Fase A es suficiente para la estructura).

**Qué cambiar:**

1. **reference_total en modo COMISION** cambia de ART-01.total_po a comisión esperada: `comision_pactada × total_po / 100` (de ART-02)

2. **Pagos parciales:** C21 COMISION soporta múltiples registros (un expediente puede aparecer en varias liquidaciones mensuales)

3. **payment_status=paid** cuando SUM(PaymentLines.amount) >= comisión_esperada

4. **Sugerencia desde liquidación:** Cuando ART-10 se reconcilia y tiene línea matched a una proforma de este expediente → card: *"Liquidación LIQ-2026-01 reconciliada. Comisión $X confirmada. ¿Registrar pago?"* CEO confirma → C21 con amount=commission_amount, method="liquidacion_marluvas", reference=liquidation_id

5. **Frontend:** Badge "Comisión — referencia liquidación Marluvas". Barra de progreso: amount_paid_total / comisión_esperada. Pago manual sin liquidación sigue funcionando (backward compatible).

---

## PASO 9 — Tests (Item 9)

**Archivos:** `apps/liquidations/tests/`, `apps/transfers/tests/`, `apps/expedientes/tests/`

**Cobertura mínima obligatoria:**

**ART-10:**
- Upload → líneas parseadas (con muestra si disponible)
- Upload con columnas no mapeables → source_file guardado, lines vacías, error_log poblado
- Match automático por consecutivo → matched
- Match manual C26 → actualiza línea
- Reconcile C27 → reconciled + evento
- Dispute C28 → disputed con observations
- Upload a período ya reconciliado → rechazado
- Discrepancia en % → discrepancy
- Premiación → no_match_needed automático

**ART-12:**
- C29 → ArtifactInstance creada, CEO-ONLY
- Void C20 → funcional
- No visible en vista client / PDF espejo

**Transfer:**
- C30 → planned
- C31→C34 happy path completo
- C35 cancel solo desde planned/approved
- Discrepancia en recepción → no reconcilable sin excepción
- C34 con discrepancias + CEO + exception_reason → reconciled + event_log
- CostLine en Transfer no afecta CostLines expediente

**Handoff:**
- Con nodo_destino cierra → sugerencia aparece
- Sin nodo_destino → sin sugerencia
- Confirmar → Transfer creada con source_expediente

**ART-19 extensiones:**
- Auto-suggest con 5+ históricos → sugerencias
- Auto-suggest < 5 → vacío
- C36 → update agregado a ART-05.payload

**C21 refinado:**
- Modo B: reference_total = comisión esperada
- Liquidación reconciliada → sugerencia pago
- Backward compatible: pago manual sin liquidación OK

**Regresión:**
- 23 POST endpoints Sprint 1-4 funcionales
- Frontend Sprint 3-4 sin regresión
- ART-09, ART-19 básico, dashboard financiero intactos

---

## Resumen de endpoints nuevos

| # | Command | Endpoint | Módulo |
|---|---------|----------|--------|
| C25 | UploadLiquidation | `POST /api/liquidations/upload/` | liquidations |
| C26 | ManualMatchLine | `POST /api/liquidations/{id}/match-line/` | liquidations |
| C27 | ReconcileLiquidation | `POST /api/liquidations/{id}/reconcile/` | liquidations |
| C28 | DisputeLiquidation | `POST /api/liquidations/{id}/dispute/` | liquidations |
| C29 | RegisterCompensation | `POST /api/expedientes/{id}/register-compensation/` | expedientes |
| C30 | CreateTransfer | `POST /api/transfers/` | transfers |
| C31 | ApproveTransfer | `POST /api/transfers/{id}/approve/` | transfers |
| C32 | DispatchTransfer | `POST /api/transfers/{id}/dispatch/` | transfers |
| C33 | ReceiveTransfer | `POST /api/transfers/{id}/receive/` | transfers |
| C34 | ReconcileTransfer | `POST /api/transfers/{id}/reconcile/` | transfers |
| C35 | CancelTransfer | `POST /api/transfers/{id}/cancel/` | transfers |
| C36 | AddShipmentUpdate | `POST /api/expedientes/{id}/add-shipment-update/` | expedientes |

**Total post-Sprint 5: 35 POST endpoints.**

---

## Notas importantes

1. **ART-10 es CROSS** — no tiene FK a expediente. Vive en módulo propio `apps/liquidations/`. La relación con expedientes es indirecta vía proforma matched.

2. **Transfer NO tiene frontend en Sprint 5** — solo modelo, commands, y admin. Frontend Transfer es Sprint 6.

3. **Reglas puente en Transfer** — C32 y C33 usan confirmación manual del CEO porque ART-15 y ART-13 no existen aún. Sprint 6 reemplaza por artefactos.

4. **Muestra Excel = bloqueante para Fase B** — arrancá todo lo demás y dejá el parser stub. Cuando llegue la muestra, completás el mapeo.

5. **Paperless no es bloqueante** — si algo falla, loguear y seguir. Drive sigue siendo válido.

6. **Visibilidad** — Todo ART-10, Transfer, ART-12, y comparativas financieras son [CEO-ONLY]. Nunca en vista client.
