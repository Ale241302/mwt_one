# Resumen Sprint 25 — Payment Status Machine + Precio Diferido + Parent/Child

**Lote de referencia:** `LOTE_SM_SPRINT25 v1.6` (auditado R6 — score 9.6/10)
**Fecha de cierre:** 2026-04-08
**Commits principales:**
- [`14ce585`](https://github.com/Ale241302/mwt_one/commit/14ce585a07d3612e6bac2740d23a3061db2905f8) — Implementación principal (Fase 0, 1, 2, 3)
- [`0fcefa50`](https://github.com/Ale241302/mwt_one/commit/0fcefa50120b57607e0693a8e734389309ddce2c) — Cierre S25-08 (BundleSerializer tiered)

**Tres pilares del sprint:**
1. **(A) Payment Status Machine** — ciclo de vida de pagos: `pending → verified → credit_released / rejected`
2. **(B) Precio Diferido** — campo interno CEO con visibilidad condicional en portal
3. **(C) Parent/Child** — relación genealógica entre expedientes con inversión en split

---

## FASE 0 — Modelos y Migraciones

### S25-01 — Campos `payment_status` en `ExpedientePago`

**Qué se hizo:** Se agregó el ciclo de vida completo al modelo de pagos y se migró la data legacy.

| Tipo | Archivo | Cambio |
|------|---------|--------|
| ✏️ MODIFICADO | `backend/apps/expedientes/models.py` | +6 campos en `ExpedientePago`: `payment_status` (CharField con choices y default `'pending'`), `verified_at` (DateTimeField nullable), `verified_by` (FK a AUTH_USER_MODEL nullable), `credit_released_at` (DateTimeField nullable), `credit_released_by` (FK nullable), `rejection_reason` (TextField blank) |
| 🆕 CREADO | `backend/apps/expedientes/migrations/0023_add_payment_status.py` | Migración estructural `AddField ×6`. Solo `AddField` — verificado con `sqlmigrate`. |
| 🆕 CREADO | `backend/apps/expedientes/migrations/0024_migrate_legacy_payment_status.py` | Data migration forward-only. Usa `apps.get_model()` con strings congelados (ref `ENT_OPS_STATE_MACHINE FROZEN v1.2.2`). Lógica C2: `amount <= 0 / NULL → pending`, expediente en `GATE_PASSED_STATUSES → credit_released`, resto `→ verified`. Reverse = `noop`. |
| ✏️ MODIFICADO | `backend/apps/expedientes/admin.py` | `payment_status` visible y filtrable. `verified_by` y `credit_released_by` read-only en admin. |

**Regla de migración legacy (C2):**
```python
GATE_PASSED_STATUSES = {
    "PRODUCCION", "PREPARACION", "DESPACHO",
    "TRANSITO", "EN_DESTINO", "CERRADO",
}
# amount <= 0 o NULL  → pending
# amount > 0 + estado en GATE_PASSED → credit_released
# amount > 0 + estado pre-gate       → verified
```

---

### S25-02 — Campos `deferred` + `parent/child` en `Expediente`

**Qué se hizo:** Se agregaron 4 campos al modelo `Expediente` para precio diferido y genealogía. Sin data migration (nullable/default).

| Tipo | Archivo | Cambio |
|------|---------|--------|
| ✏️ MODIFICADO | `backend/apps/expedientes/models.py` | +4 campos en `Expediente`: `deferred_total_price` (DecimalField nullable), `deferred_visible` (BooleanField default False), `parent_expediente` (FK self nullable), `is_inverted_child` (BooleanField default False) |
| 🆕 CREADO | `backend/apps/expedientes/migrations/0025_add_deferred_parent_child.py` | Migración estructural `AddField ×4`. Solo campos compatibles con legacy. |
| ✏️ MODIFICADO | `backend/apps/expedientes/admin.py` | `deferred_total_price` + `deferred_visible` editables. `parent_expediente` + `is_inverted_child` read-only. |

---

## FASE 1 — Servicios y Endpoints Backend

### S25-03 — Endpoints verificación y rechazo de pago

**Qué se hizo:** Se crearon los endpoints `verify` y `reject` con locking atómico, EventLog y permisos CEO only.

| Tipo | Archivo | Cambio |
|------|---------|--------|
| 🆕 CREADO | `backend/apps/expedientes/views/payment_status.py` | Funciones `verify_payment()` y `reject_payment()`. Ambas usan `transaction.atomic()` + `select_for_update()` sobre `Expediente` y `ExpedientePago`. `verify`: `pending → verified` (409 si no es pending). `reject`: `pending/verified → rejected` + `reason` obligatorio (400 si falta). Ambas crean `EventLog` con `action_source` correspondiente. |
| 🆕 CREADO | `backend/apps/expedientes/views/__init__.py` | Archivo de inicialización del subpaquete `views/`. |
| ✏️ MODIFICADO | `backend/apps/expedientes/urls.py` | URLs `verify/` y `reject/` registradas bajo `expedientes:payment-verify` y `expedientes:payment-reject`. |

**Transiciones implementadas:**
- `pending → verified` ✅
- `pending → rejected` ✅ (requiere `reason`)
- `verified → rejected` ✅
- Non-pending → verify → `409 Conflict` ✅
- `credit_released` → reject → `409 Conflict` ✅

---

### S25-04 — Endpoints liberación de crédito (individual + bulk)

**Qué se hizo:** Se agregaron los endpoints `release-credit` individual y `release-all-verified` bulk al mismo archivo de vistas.

| Tipo | Archivo | Cambio |
|------|---------|--------|
| ✏️ MODIFICADO | `backend/apps/expedientes/views/payment_status.py` | Funciones `release_credit()` y `release_all_verified()`. Individual: `verified → credit_released` (409 si no es verified). Bulk: opera sobre `verified + credit_released`, ignora `pending/rejected`, recalcula **UNA sola vez** post-bulk, genera 1 `EventLog` por pago con `payload.bulk=True`. |
| ✏️ MODIFICADO | `backend/apps/expedientes/urls.py` | URLs `release-credit/` y `release-all-verified/` registradas. |

**Semántica bulk (`release_all_verified`):**
- `released`: pagos que pasaron de `verified → credit_released` en esta llamada
- `already_released`: pagos que ya estaban en `credit_released` al momento de la llamada
- `recalculate_expediente_credit()` se llama **una vez** al final (no N veces)

---

### S25-05 — Extender `recalculate_expediente_credit()`

**Qué se hizo:** Se creó `compute_coverage()` como SSOT y se extendió `recalculate_expediente_credit()` para filtrar solo pagos `credit_released`.

| Tipo | Archivo | Cambio |
|------|---------|--------|
| ✏️ MODIFICADO | `backend/apps/expedientes/services/credit.py` | Nueva función `compute_coverage(total_paid, expediente_total)` con early return para `expediente_total=None/0`, `ROUND_HALF_UP` explícito en `quantize()`, cap a `100.00`. `recalculate_expediente_credit()` ahora calcula `total_released` (solo `credit_released`), `total_pending` (`pending+verified`), `total_rejected`. El snapshot incluye `payment_coverage`, `coverage_pct`, `total_pending`, `total_rejected`. |

**Función `compute_coverage()`:**
```python
# Edge case: expediente_total=None o <=0 → ('none', 0.00)
# total_paid <= 0          → ('none', 0.00)
# total_paid >= total      → ('complete', min(100.00, pct))
# 0 < total_paid < total   → ('partial', pct)
# Redondeo: ROUND_HALF_UP a 2 decimales
```

---

### S25-06 — Endpoint PATCH `deferred-price`

**Qué se hizo:** Se creó el endpoint para gestión del precio diferido con invariantes estrictas de validación y sentinel `_MISSING`.

| Tipo | Archivo | Cambio |
|------|---------|--------|
| 🆕 CREADO | `backend/apps/expedientes/views/deferred.py` | Función `patch_deferred_price()` con locking. Sentinel `_MISSING = object()` para distinguir campo no enviado vs enviado como `null`. Orden de validación: (1) payload contradictorio `null + visible=True` → 400 duro, (2) auto-corrección `null → visible=False`, (3) validar `visible=True` con precio null → 400. EventLog con `action_source='patch_deferred'`. |
| ✏️ MODIFICADO | `backend/apps/expedientes/urls.py` | URL `deferred-price/` registrada bajo `expedientes:deferred-price`. |

**Precedencia de validación (fix M1 R6):**
1. Payload contradictorio (`null + visible=True` en misma llamada) → `400` inmediato, sin auto-corrección
2. Solo `null` → auto-corregir `visible=False`
3. `visible=True` con precio null existente → `400`

---

### S25-07 — Extender `separate-products` con inversión

**Qué se hizo:** Se extendió el handler de separación de productos para soportar el parámetro `invert_parent` y los EventLogs en ambos expedientes.

| Tipo | Archivo | Cambio |
|------|---------|--------|
| ✏️ MODIFICADO | `backend/apps/expedientes/views_sprint18.py` | Parámetro `invert_parent=False` leído del payload. Restricción: si `expediente.parent_expediente_id is not None` e `invert_parent=True` → `409 Conflict`. Lógica de asignación: `invert=False` → `new_exp.parent = original` (S18 backward compat); `invert=True` → `original.parent = new_exp`, `original.is_inverted_child=True`. `EventLog` creado en **ambos** expedientes (original y nuevo) con `action_source='separate_products'`, `event_type='expediente.split'`, payload con `parent_id`, `child_id`, `inverted`, `role`, `lines_moved`. |

---

### S25-08 — Bundle de detalle extendido (serializers tiered)

**Qué se hizo:** Se implementaron dos serializers separados por tier — CEO/AGENT_* completo y CLIENT_* restringido. Adicionalmente se actualizaron los serializers auxiliares.

| Tipo | Archivo | Cambio |
|------|---------|--------|
| ✏️ MODIFICADO | `backend/apps/expedientes/serializers.py` | `BundleSerializer` (CEO/AGENT_*) extendido con: `payment_coverage`, `coverage_pct`, `total_pending`, `total_rejected` (via helper `_get_coverage_data()` con caché por `obj.pk`), `deferred_total_price`, `deferred_visible`, `parent_expediente {id, number}`, `child_expedientes [{id, number}]`, `is_inverted_child`. Nuevo `BundlePortalSerializer` (CLIENT_*) con campos restringidos: `payment_coverage + coverage_pct` únicamente, `deferred_total_price` solo si `deferred_visible=True` (retorna `null` si no), pagos via `PagoClienteSerializer`. **SIN** `total_pending`, `total_rejected`, `deferred_visible`, `credit_exposure`, `is_inverted_child`. |
| ✏️ MODIFICADO | `backend/apps/expedientes/serializers_portal.py` | Actualizado para usar `BundlePortalSerializer` en el contexto del portal B2B. |
| ✏️ MODIFICADO | `backend/apps/expedientes/serializers_ui.py` | Actualizado para referenciar el nuevo contrato de bundle CEO. |
| 🆕 CREADO | `backend/apps/expedientes/tests/test_sprint25_serializers.py` | 3 tests de tiering: `test_bundle_serializer_ceo_fields` (verifica snapshot completo CEO), `test_bundle_portal_serializer_restricted_fields` (verifica que CLIENT no ve campos sensibles), `test_bundle_portal_serializer_deferred_masked` (verifica que `deferred_total_price=null` cuando `visible=False`). |

**Contratos por tier:**

| Campo | BundleSerializer (CEO) | BundlePortalSerializer (CLIENT) |
|-------|----------------------|--------------------------------|
| `payment_coverage` | ✅ | ✅ |
| `coverage_pct` | ✅ | ✅ |
| `total_pending` | ✅ | ❌ |
| `total_rejected` | ✅ | ❌ |
| `deferred_total_price` | ✅ siempre | ✅ solo si `visible=True` |
| `deferred_visible` | ✅ | ❌ |
| `credit_exposure` | ✅ | ❌ |
| `parent_expediente` | ✅ `{id, number}` | ✅ solo `str` |
| `child_expedientes` | ✅ lista | ❌ |
| `is_inverted_child` | ✅ | ❌ |
| Pagos | `PagoSerializer` (completo) | `PagoClienteSerializer` (restringido) |

---

## FASE 2 — Frontend

### S25-09 — Sección pagos con status y acciones

**Qué se hizo:** Se refactorizó la sección de pagos del expediente para incluir el ciclo de vida de pagos con badges, acciones CEO y summary.

| Tipo | Archivo | Cambio |
|------|---------|--------|
| ✏️ MODIFICADO | `frontend/src/components/expediente/PagosSection.tsx` | +450 líneas / -81. Tabla con columna "Estado" con badges por `payment_status`: amarillo (pending), azul (verified), verde (credit_released), rojo (rejected) + tooltip con `rejection_reason`. Botones inline CEO: `[Verificar] [Rechazar]` para pending; `[Liberar crédito] [Rechazar]` para verified; estados terminales sin acciones. Modal "Rechazar" con textarea `reason` obligatorio. Botón "Liberar todos los verificados" (bulk) en header. Summary row: "Pagado (liberado): $X | Pendiente verificación: $Y | Rechazado: $Z". |

---

### S25-10 — Credit bar actualizada

**Qué se hizo:** Se creó el componente `CreditBar` con tiering por rol.

| Tipo | Archivo | Cambio |
|------|---------|--------|
| 🆕 CREADO | `frontend/src/components/expediente/CreditBar.tsx` | +167 líneas. Barra de progreso con estados: verde (`complete`), amarillo con % (`partial`), rojo (`none`). Tooltip tiered: CEO/AGENT_* → "Liberado: $X de $Y (Z%) | Pendiente: $W"; CLIENT_* → solo "Cobertura: Z%" sin montos. Nota "Hay pagos pendientes de liberar" visible solo para CEO cuando hay pagos en `pending/verified`. |

---

### S25-11 — Toggle y display precio diferido

**Qué se hizo:** Se creó el panel de gestión del precio diferido para CEO y su visualización condicional en portal.

| Tipo | Archivo | Cambio |
|------|---------|--------|
| 🆕 CREADO | `frontend/src/components/expediente/DeferredPricePanel.tsx` | +281 líneas. Input numérico para `deferred_total_price` con semántica null vs 0: input vacío envía `null`, botón "✕ Limpiar" para volver a null. Toggle `deferred_visible` con label condicional: verde "El cliente ve este precio" / gris "Solo visible internamente". Toggle deshabilitado si precio es null (tooltip "Define un precio diferido primero"). PATCH on blur / on toggle change. Portal: muestra "Precio acordado: $X" solo si `deferred_visible=True` — sin toggle ni hint de "diferido". |

---

### S25-12 — Banner parent/child + checkbox inversión en split

**Qué se hizo:** Se creó el banner genealógico y se extendió el modal de split.

| Tipo | Archivo | Cambio |
|------|---------|--------|
| 🆕 CREADO | `frontend/src/components/expediente/FamilyBanner.tsx` | +128 líneas. Banner en header del expediente: "🔗 Separado de Expediente #{parent.number}" (con link) si tiene parent; "🔗 Expedientes derivados: #{child.number}..." si tiene children; "(inversión)" agregado si `is_inverted_child=True`. |
| ✏️ MODIFICADO | `frontend/src/components/expediente/ModalSplit.tsx` | +46 líneas / -2. Checkbox "☐ Invertir relación: el nuevo expediente será el principal" con tooltip explicativo. Payload incluye `invert_parent: true/false`. |

---

### S25-13 — Vista portal pagos (CLIENT_*)

**Qué se hizo:** Se creó la vista de pagos para el portal del cliente con campos restringidos.

| Tipo | Archivo | Cambio |
|------|---------|--------|
| 🆕 CREADO | `frontend/src/components/portal/PortalPagosTab.tsx` | +257 líneas. Lista simplificada: fecha, monto, badge de estado. CLIENT_* nunca ve: `verified_by`, `rejection_reason` detallado, `credit_released_by`. Si `rejected`: solo badge rojo "Rechazado" sin motivo. Si `deferred_visible=True`: muestra "Precio acordado: $X" (sin label "diferido"). Sin acciones — solo lectura. |

---

## FASE 3 — Tests y QA

### S25-14 — Suite de tests backend (56 + 3 = 59 tests)

**Qué se hizo:** Se crearon dos archivos de tests cubriendo todos los flujos del sprint.

| Tipo | Archivo | Cambio |
|------|---------|--------|
| 🆕 CREADO | `backend/apps/expedientes/tests/test_sprint25.py` | 56 tests en 9 bloques: T01-T08 `compute_coverage()` edge cases, T09-T14 `recalculate_expediente_credit()` con payment_status, T15-T20 `verify_payment` endpoint, T21-T27 `reject_payment` endpoint, T28-T32 `release_credit` individual, T33-T38 `release_all_verified` bulk, T39-T48 `patch_deferred_price` invariants, T49-T54 split con `invert_parent`, T55-T56 lógica data migration C2. |
| 🆕 CREADO | `backend/apps/expedientes/tests/test_sprint25_serializers.py` | 3 tests de tiering serializers: CEO campos completos, CLIENT campos restringidos, deferred enmascarado cuando `visible=False`. |

**Cobertura por bloque:**

| Bloque | Tests | Qué cubre |
|--------|-------|-----------|
| T01–T08 | 8 | `compute_coverage()`: None/0 total, zero paid, partial, complete, overpayment, ROUND_HALF_UP |
| T09–T14 | 6 | Solo `credit_released` cuenta en crédito; pending/verified/rejected ignorados |
| T15–T20 | 6 | verify: 403 no-CEO, pending→verified, 409 non-pending, no libera crédito, EventLog |
| T21–T27 | 7 | reject: 403, 400 sin reason, pending→rejected, verified→rejected, 409 credit_released, recalculate, EventLog |
| T28–T32 | 5 | release individual: verified→released, 409 pending, 409 ya released, recalculate, EventLog |
| T33–T38 | 6 | bulk release: all verified, ignora pending/rejected, idempotente, recalculate×1, EventLog×N, 403 |
| T39–T48 | 10 | deferred: 403, set price, visible=True con precio, visible sin precio→400, contradictorio→400, null autocorrige, negativo→400, cero válido, body vacío→400, EventLog |
| T49–T54 | 6 | split: default child, invert parent, 409 ya es child, backward compat, EventLog ambos, 400 all lines |
| T55–T56 | 2 | Lógica migración C2: amount=0→pending, PRODUCCION+amount>0→credit_released |
| Serializers | 3 | BundleSerializer CEO completo, BundlePortalSerializer restringido, deferred enmascarado |

---

## Índice de archivos modificados/creados

| Archivo | Tipo | Ítem(s) |
|---------|------|---------|
| `backend/apps/expedientes/models.py` | ✏️ MODIFICADO | S25-01, S25-02 |
| `backend/apps/expedientes/admin.py` | ✏️ MODIFICADO | S25-01, S25-02 |
| `backend/apps/expedientes/migrations/0023_add_payment_status.py` | 🆕 CREADO | S25-01 |
| `backend/apps/expedientes/migrations/0024_migrate_legacy_payment_status.py` | 🆕 CREADO | S25-01 |
| `backend/apps/expedientes/migrations/0025_add_deferred_parent_child.py` | 🆕 CREADO | S25-02 |
| `backend/apps/expedientes/services/credit.py` | ✏️ MODIFICADO | S25-05 |
| `backend/apps/expedientes/views/__init__.py` | 🆕 CREADO | S25-03 |
| `backend/apps/expedientes/views/payment_status.py` | 🆕 CREADO | S25-03, S25-04 |
| `backend/apps/expedientes/views/deferred.py` | 🆕 CREADO | S25-06 |
| `backend/apps/expedientes/views_sprint18.py` | ✏️ MODIFICADO | S25-07 |
| `backend/apps/expedientes/serializers.py` | ✏️ MODIFICADO | S25-08 |
| `backend/apps/expedientes/serializers_portal.py` | ✏️ MODIFICADO | S25-08 |
| `backend/apps/expedientes/serializers_ui.py` | ✏️ MODIFICADO | S25-08 |
| `backend/apps/expedientes/urls.py` | ✏️ MODIFICADO | S25-03, S25-04, S25-06 |
| `backend/apps/expedientes/tests/test_sprint25.py` | 🆕 CREADO | S25-14 |
| `backend/apps/expedientes/tests/test_sprint25_serializers.py` | 🆕 CREADO | S25-08, S25-14 |
| `frontend/src/components/expediente/PagosSection.tsx` | ✏️ MODIFICADO | S25-09 |
| `frontend/src/components/expediente/CreditBar.tsx` | 🆕 CREADO | S25-10 |
| `frontend/src/components/expediente/DeferredPricePanel.tsx` | 🆕 CREADO | S25-11 |
| `frontend/src/components/expediente/FamilyBanner.tsx` | 🆕 CREADO | S25-12 |
| `frontend/src/components/expediente/ModalSplit.tsx` | ✏️ MODIFICADO | S25-12 |
| `frontend/src/components/portal/PortalPagosTab.tsx` | 🆕 CREADO | S25-13 |

---

## Estado final

| Fase | Ítems | Estado |
|------|-------|--------|
| FASE 0 — Modelos y Migraciones | S25-01, S25-02 | ✅ COMPLETO |
| FASE 1 — Backend Endpoints | S25-03, S25-04, S25-05, S25-06, S25-07, S25-08 | ✅ COMPLETO |
| FASE 2 — Frontend | S25-09, S25-10, S25-11, S25-12, S25-13 | ✅ COMPLETO |
| FASE 3 — Tests | S25-14 (59 tests) | ✅ COMPLETO |

> **Sprint 25 cerrado.** Todos los ítems del `LOTE_SM_SPRINT25 v1.6` implementados y verificados.
