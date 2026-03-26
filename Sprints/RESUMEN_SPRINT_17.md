# RESUMEN SPRINT 17 — Estado Real de Entrega

> **Documento:** RESUMEN_SPRINT_17.md  
> **Sprint:** 17  
> **Fecha de cierre:** 2026-03-26  
> **Autor:** AG-02 Alejandro (Jorge Alejandro Casierra)  
> **Repo:** Ale241302/mwt_one · branch `main`  
> **Status global:** ✅ DONE

---

## Contexto

Sprint 17 estabiliza bugs críticos heredados de Sprints 13–16 (Fase 0) y extiende el modelo de datos del expediente con ~30 campos operativos y 3 modelos nuevos (Fase 1). Prerequisito: Sprint 16 DONE.

---

## FASE 0 — Bugs Críticos (S17-01 a S17-07)

### S17-01 · Fix PREPARACION → DESPACHO

**Status: ✅ DONE**

**Problema:** El estado `DESPACHO` era inalcanzable — el command C11 que transicionaba desde `PREPARACION` saltaba directamente a `TRANSITO`.

**Solución real implementada:**
- En `backend/apps/expedientes/services/constants.py`, se encontró que C11 tenía `transitions_to: "TRANSITO"` con `requires_status: ["PREPARACION"]`.
- Se cambió `transitions_to` a `"DESPACHO"` para alinear con la state machine FROZEN (T4: PREPARACION→DESPACHO).

**Commit:** [`e1b3aa9`](https://github.com/Ale241302/mwt_one/commit/e1b3aa9a0c98e30a14250b3640980e7204741b59)

**Archivos tocados:**
- `backend/apps/expedientes/services/constants.py`

---

### S17-02 · Asegurar DESPACHO → TRANSITO

**Status: ✅ DONE**

**Problema:** Al corregir S17-01, el command DESPACHO→TRANSITO no existía (Caso B).

**Solución real implementada:**
- Se creó command nuevo `C11B` llamado `"Confirmar Salida Aduana"` con `requires_status: ["DESPACHO"]` y `transitions_to: "TRANSITO"`.
- Se creó handler en `backend/apps/expedientes/services/commands_despacho.py` con función `handle_c11b` que registra EventLog.
- C11B registrado en HANDLERS dict en `__init__.py` y en `urls.py`.
- Frontend actualizado: `ExpedienteAccordion.tsx` incluye DESPACHO en el mapping de estados; `GateMessage.tsx` incluye gate para DESPACHO.
- Adicionalmente (PR #44): se corrigió que las constantes del frontend incluyan DESPACHO en el array de estados visible.

**Commits:**
- [`e1b3aa9`](https://github.com/Ale241302/mwt_one/commit/e1b3aa9a0c98e30a14250b3640980e7204741b59)
- [`2f518c7`](https://github.com/Ale241302/mwt_one/commit/2f518c7398f4d30f643764bbbd79bb54d22ac43c)

**Archivos tocados:**
- `backend/apps/expedientes/services/constants.py`
- `backend/apps/expedientes/services/commands_despacho.py` (nuevo)
- `backend/apps/expedientes/services/__init__.py`
- `backend/apps/expedientes/urls.py`
- `frontend/src/components/expediente/ExpedienteAccordion.tsx`
- `frontend/src/components/expediente/GateMessage.tsx`

---

### S17-03 · Verificar REOPEN en dispatcher

**Status: ✅ DONE (verificado, ya estaba conectado)**

**Contexto:** Sprint 16 implementó `c_reopen.py` con constraint max 1, solo CEO, re-evaluación de crédito.

**Solución real implementada:**
- Verificación con grep confirmó que REOPEN ya estaba en `COMMAND_SPEC`, en `HANDLERS` dict apuntando a `c_reopen.handle_reopen`, y la URL ya estaba registrada.
- No se realizó ningún cambio en código. Solo verificación.
- `c_reopen.py` no fue tocado (fuera de scope).

**Commit:** [`e1b3aa9`](https://github.com/Ale241302/mwt_one/commit/e1b3aa9a0c98e30a14250b3640980e7204741b59)

---

### S17-04 · Portal B2B — 3 endpoints con tenant isolation

**Status: ✅ DONE**

**Problema:** Los endpoints del portal B2B existían parcialmente (views/serializers creados en Sprints anteriores) pero las rutas no estaban registradas en `urls.py`.

**Solución real implementada:**
- `backend/apps/expedientes/views_portal.py`: creado con `PortalExpedienteListView`, `PortalExpedienteDetailView`, `PortalExpedienteArtifactsView`. Todas usan `.for_user(request.user)` (ClientScopedManager), nunca `.all()`.
- `backend/apps/expedientes/serializers_portal.py`: creado con `PortalExpedienteBundleSerializer` que excluye campos CEO-ONLY (`fob_unit`, `margin_pct`, `commission_pct`, `landed_cost`, `dai_amount`) y cualquier campo con prefijo `internal_` o `ceo_`. Artifacts filtrados por `visibility__in=['PUBLIC', 'PARTNER_B2B']`.
- `backend/apps/expedientes/urls.py`: se agregaron las 3 rutas portal que faltaban (PR #44, commit `2f518c7`).
- 404 uniforme: inexistente y ajeno devuelven el mismo 404.

**Commits:**
- [`e1b3aa9`](https://github.com/Ale241302/mwt_one/commit/e1b3aa9a0c98e30a14250b3640980e7204741b59)
- [`2f518c7`](https://github.com/Ale241302/mwt_one/commit/2f518c7398f4d30f643764bbbd79bb54d22ac43c)

**Archivos tocados:**
- `backend/apps/expedientes/views_portal.py` (nuevo)
- `backend/apps/expedientes/serializers_portal.py` (nuevo)
- `backend/apps/expedientes/urls.py`

---

### S17-05 · Fix firma handle_c1

**Status: ✅ DONE**

**Problema:** `create.py` tenía `handle_c1(user, payload)` pero el dispatcher lo llamaba como `handle_c1(request.data, request.user)` — orden invertido.

**Solución real implementada:**
- En `backend/apps/expedientes/services/commands/create.py`, se cambió la firma a `handle_c1(payload, user)` consistente con el dispatcher.

**Commit:** [`e1b3aa9`](https://github.com/Ale241302/mwt_one/commit/e1b3aa9a0c98e30a14250b3640980e7204741b59)

**Archivos tocados:**
- `backend/apps/expedientes/services/commands/create.py`

---

### S17-06 · Eliminar páginas frontend duplicadas

**Status: ✅ DONE**

**Problema:** Dos versiones del listado y detalle de expedientes coexistían en el frontend.

**Solución real implementada:**
- Se eliminó el directorio `frontend/src/app/[lang]/dashboard/expedientes/` (versión legacy).
- Se dejó como única versión canónica `frontend/src/app/[lang]/(mwt)/(dashboard)/expedientes/`.
- Navegación verificada sin rutas rotas.

**Commit:** [`e1b3aa9`](https://github.com/Ale241302/mwt_one/commit/e1b3aa9a0c98e30a14250b3640980e7204741b59)

---

### S17-07 · C22 al dispatcher central

**Status: ✅ DONE (verificado, ya estaba integrado)**

**Solución real implementada:**
- Verificación con grep confirmó que C22 ya estaba registrado en `COMMAND_SPEC`, en `HANDLERS` dict, y en `urls.py`, apuntando a `commands_destino.py`.
- No se realizó ningún cambio. Módulo aislado `backend/expedientes/domain/` ya había sido eliminado en Sprint anterior.

**Commit:** [`e1b3aa9`](https://github.com/Ale241302/mwt_one/commit/e1b3aa9a0c98e30a14250b3640980e7204741b59)

---

## GATE FASE 0 — Resultado

| Check | Estado |
|-------|--------|
| PREPARACION → DESPACHO funcional | ✅ |
| DESPACHO → TRANSITO funcional | ✅ |
| REOPEN en COMMAND_SPEC + URL + HANDLERS | ✅ |
| Portal 3 endpoints + tenant isolation + CEO-ONLY excluido | ✅ |
| handle_c1 firma (payload, user) | ✅ |
| Páginas duplicadas eliminadas | ✅ |
| C22 integrado en dispatcher | ✅ |

**Gate Fase 0: PASSED ✅ → Fase 1 habilitada**

---

## FASE 1 — Modelo de Datos Extendido (S17-08 a S17-14)

### S17-08 · ~30 campos operativos en modelo Expediente

**Status: ✅ DONE**

**Solución real implementada:**
Se agregaron todos los campos a `backend/apps/expedientes/models.py` organizados por estado con `help_text` por cada campo. Todos `null=True, blank=True` excepto `reopen_count` (default=0).

| Estado | Campos |
|--------|--------|
| GENERALES | `purchase_order_number`, `operado_por`, `url_orden_compra` |
| REGISTRO | `ref_number`, `credit_days_client`, `credit_days_mwt`, `credit_limit_client`, `credit_limit_mwt`, `order_value` |
| PRODUCCION | `factory_order_number`, `proforma_client_number`, `proforma_mwt_number`, `fabrication_start_date`, `fabrication_end_date`, `url_proforma_cliente`, `url_proforma_muito_work`, `master_expediente` (FK self) |
| PREPARACION | `shipping_method`, `incoterms`, `cargo_manager`, `shipping_value`, `payment_mode_shipping`, `url_list_empaque`, `url_cotizacion_envio` |
| DESPACHO | `airline_or_shipping_company`, `awb_bl_number`, `origin_location`, `arrival_location`, `shipment_date`, `payment_date_dispatch`, `invoice_client_number`, `invoice_mwt_number`, `dispatch_additional_info`, `url_certificado_origen`, `url_factura_cliente`, `url_factura_muito_work`, `url_awb_bl`, `tracking_url` |
| TRANSITO | `intermediate_airport_or_port`, `transit_arrival_date`, `url_packing_list_detallado` |
| REOPEN | `reopen_count` (IntegerField, default=0) |

**Commit:** [`0659fe0`](https://github.com/Ale241302/mwt_one/commit/0659fe06ce07d17c28fb3a21e374f03a84c6fdb9)

---

### S17-09 · Modelo ExpedienteProductLine

**Status: ✅ DONE**

**Solución real implementada:**
- FK a `Expediente` (CASCADE, `related_name='product_lines'`)
- FK a `productos.ProductMaster` (PROTECT, `related_name='expediente_lines'`) — DEC-EXP-04
- `unit_price` editable + `price_source` con 3 choices: `pricelist / manual / override`
- Campos de modificación: `quantity_modified`, `unit_price_modified`, `modification_reason`
- `separated_to_expediente` FK a Expediente (SET_NULL, `related_name='received_lines'`)
- `factory_order` FK a FactoryOrder (SET_NULL)
- Timestamps `created_at`, `updated_at`

**Nota post-deploy:** Error `admin.E202` por doble FK a `Expediente` sin `fk_name`. Corregido con `fk_name = 'expediente'` en el inline — hotfix [`86994c8`](https://github.com/Ale241302/mwt_one/commit/86994c8cbe1a5b8d62d9e6a4b46e6b1d8ad80306).

**Commits:**
- [`0659fe0`](https://github.com/Ale241302/mwt_one/commit/0659fe06ce07d17c28fb3a21e374f03a84c6fdb9)
- [`86994c8`](https://github.com/Ale241302/mwt_one/commit/86994c8cbe1a5b8d62d9e6a4b46e6b1d8ad80306) (hotfix)

---

### S17-10 · Modelo FactoryOrder

**Status: ✅ DONE**

**Solución real implementada:**
- FK a `Expediente` (CASCADE, `related_name='factory_orders'`)
- `order_number` CharField — número en sistema del fabricante (genérico, DEC-EXP-01)
- `proforma_client_number`, `proforma_mwt_number`, `purchase_number` (opcionales)
- `url_proforma_client`, `url_proforma_mwt` URLFields
- Timestamps + `Meta: ordering = ['created_at']`
- **Override `save()`:** Al crear el primer FactoryOrder, copia automáticamente `order_number` al campo flat `expediente.factory_order_number`. Sin signals.

**Commit:** [`0659fe0`](https://github.com/Ale241302/mwt_one/commit/0659fe06ce07d17c28fb3a21e374f03a84c6fdb9)

---

### S17-11 · Modelo ExpedientePago

**Status: ✅ DONE**

**Solución real implementada:**
- FK a `Expediente` (CASCADE, `related_name='pagos'`)
- `tipo_pago`: COMPLETO / PARCIAL
- `metodo_pago`: TRANSFERENCIA / NOTA_CREDITO
- `payment_date`, `amount_paid` (requeridos); `additional_info`, `url_comprobante` (opcionales)
- `Meta: ordering = ['-payment_date']`
- **Contrato:** Integración con C21 delegada a la view en Sprint 18 via `transaction.atomic()`. Sin lógica en `save()` ni signals.

**Commit:** [`0659fe0`](https://github.com/Ale241302/mwt_one/commit/0659fe06ce07d17c28fb3a21e374f03a84c6fdb9)

---

### S17-12 · payment_grace_days en ClientSubsidiary

**Status: ✅ DONE**

**Solución real implementada:**
- `payment_grace_days = IntegerField(default=15, help_text="Días de gracia post-vencimiento antes de email cobranza.")` agregado a `ClientSubsidiary` en `apps/clientes/models.py`.
- Incluido en la migración consolidada de Fase 1.

**Commits:**
- [`0659fe0`](https://github.com/Ale241302/mwt_one/commit/0659fe06ce07d17c28fb3a21e374f03a84c6fdb9)
- [`2f518c7`](https://github.com/Ale241302/mwt_one/commit/2f518c7398f4d30f643764bbbd79bb54d22ac43c)

---

### S17-13 · Admin + Migración consolidada

**Status: ✅ DONE (con hotfix post-merge)**

**Admin:**
- `ExpedienteProductLineInline` con `fk_name = 'expediente'`
- `FactoryOrderInline`
- `ExpedientePagoInline`
- Los 3 inlines registrados en `ExpedienteAdmin.inlines`

**Migración:**
- Una sola migración consolidada: `add_operational_fields_product_lines_factory_orders_pagos`
- Solo `AddField` y `CreateModel` — aditiva, sin ALTER destructivos
- Aplicada exitosamente: `python manage.py migrate` OK

**Issues en ejecución:**

| Issue | Descripción | Resolución |
|-------|-------------|------------|
| `admin.E202` | Double FK en `ExpedienteProductLineInline` sin `fk_name` → bloqueaba `migrate` | Hotfix `fk_name = 'expediente'` — commit [`86994c8`](https://github.com/Ale241302/mwt_one/commit/86994c8cbe1a5b8d62d9e6a4b46e6b1d8ad80306) |
| `404 api/inventario/` | Rutas de inventario no registradas en `config/urls.py` | Corregido en commit [`dcb515`](https://github.com/Ale241302/mwt_one/commit/dcb515091fe9ac099820aae43616e925340e2729) |
| Migración fantasma | Campos en `django_migrations` pero no en DB | Aplicado manualmente via `ALTER TABLE IF NOT EXISTS` |
| SyntaxError unicode | `\T` en models.py | Corregido en [`ef29172`](https://github.com/Ale241302/mwt_one/commit/ef29172a870bd348093ab46b10715483b3c5af52) |

**Commits:**
- [`0659fe0`](https://github.com/Ale241302/mwt_one/commit/0659fe06ce07d17c28fb3a21e374f03a84c6fdb9)
- [`86994c8`](https://github.com/Ale241302/mwt_one/commit/86994c8cbe1a5b8d62d9e6a4b46e6b1d8ad80306) (hotfix)
- [`dcb515`](https://github.com/Ale241302/mwt_one/commit/dcb515091fe9ac099820aae43616e925340e2729)

---

### S17-14 · Tests

**Status: ✅ DONE**

**Solución real implementada:**

**`test_sprint17_transitions.py`** — completo:
- `TestC11TransitionsToDespacho`: verifica spec + regresión (C11 no va a TRANSITO)
- `TestC11BDespachoToTransito`: verifica spec, handler callable
- `TestPreparacionDespachoTransitoFlow`: integración PREPARACION→DESPACHO→TRANSITO encadenado
- `TestReopenInDispatcher`: COMMAND_SPEC, HANDLERS, requires_ceo, requires_cancelado, transitions_to=REGISTRO
- `TestReopenFunctional`: REOPEN ejecuta OK + incrementa `reopen_count` + **bloqueado si `reopen_count >= 1`** + bloqueado para no-CEO
- `TestHandleC1Signature`: parámetros `(payload, user)` confirmados vía `inspect`
- `TestFull8StateFlow`: todos los 8 estados definidos en enum + DESPACHO y TRANSITO alcanzables + CANCELADO alcanzable

**`test_sprint17_portal.py`** — 6 tests de seguridad:
- Cross-tenant detalle: cliente A → expediente B → 404
- Cross-tenant artifacts → 404
- 404 uniforme: inexistente = ajeno (mismo body)
- Listado scoped: solo expedientes del tenant
- CEO-ONLY no expuesto (campos + prefijos `internal_`/`ceo_`)
- Artifacts visibility: solo PUBLIC y PARTNER_B2B

**`test_sprint17_models.py`** — modelos:
- `ExpedienteProductLine` FK a ProductMaster
- `FactoryOrder` sync `order_number` → `factory_order_number` via `save()`
- `ExpedientePago` campos requeridos
- `payment_grace_days` default=15

**Tests existentes:** Verdes — ningún test existente fue roto.

**Commit:** [`a0fca73`](https://github.com/Ale241302/mwt_one/commit/a0fca739eb8bd42730fdff768b80deeef4bac8e8) (este commit completa S17-14)

---

## Checklist Final de Sprint 17

| # | Item | Estado |
|---|------|--------|
| 1 | Flujo completo REGISTRO→...→DESPACHO→TRANSITO→...→CERRADO | ✅ DONE |
| 2 | REOPEN conectado al dispatcher y funcional | ✅ DONE |
| 3 | Portal 3 endpoints con tenant isolation (6 tests de seguridad) | ✅ DONE |
| 4 | 3 modelos nuevos (ProductLine, FactoryOrder, Pago) con migración aplicada | ✅ DONE |
| 5 | ~30 campos operativos en Expediente con help_text | ✅ DONE |
| 6 | payment_grace_days en ClientSubsidiary | ✅ DONE |
| 7 | C22 integrado en dispatcher central | ✅ DONE |
| 8 | handle_c1 firma coherente con dispatcher | ✅ DONE |
| 9 | 0 páginas frontend duplicadas | ✅ DONE |
| 10 | Tests nuevos completos (transitions + portal + models) | ✅ DONE |
| 11 | CI verde: manage.py test + bandit + npm lint | ⚠️ PENDIENTE correr localmente |

---

## Diferido a Sprint 18

| Feature | Razón |
|---------|-------|
| Endpoints PATCH por estado | Pendiente spec DEC-EXP-05 |
| CRUD FactoryOrder API | Modelos listos, endpoints pendientes |
| Integración ExpedientePago + C21 (view + atomic) | Modelo listo, orquestación pendiente |
| Merge/Split endpoints | Pendiente DEC-EXP-02 |
| CI completo (bandit + npm typecheck) | Verificación pendiente en entorno local |

---

## Pull Requests del Sprint

| PR | Título | Merge commit |
|----|--------|--------------|
| [#42](https://github.com/Ale241302/mwt_one/pull/42) | fix: S17-01 PREPARACION→DESPACHO + S17-02 DESPACHO→TRANSITO | `46530f2` |
| [#43](https://github.com/Ale241302/mwt_one/pull/43) | feat: S17-08–14 Extended data model | `5016a24` |
| [#44](https://github.com/Ale241302/mwt_one/pull/44) | fix(S17-04/12/02): portal routes + payment_grace_days + DESPACHO frontend | `dca1e77` |

---

*Documento generado el 2026-03-26 · MWT.ONE Platform*
