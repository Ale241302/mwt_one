# Sprint 17 — Guía de implementación para Alejandro

## Qué es esto

Sprint 17 estabiliza bugs heredados de Sprints 13-16 y extiende el modelo de datos del expediente. Tiene 2 fases estrictas: primero arreglamos lo roto, después construimos encima. Sin atajos.

## Estructura del sprint

| Fase | Items | Prioridad | Qué hace |
|------|-------|-----------|----------|
| 0 | S17-01 a S17-07: Bugs críticos | P0 obligatorio | State machine rota, portal sin backend, C22 aislado |
| 1 | S17-08 a S17-14: Modelo de datos | P0 | ~30 campos operativos + 3 modelos nuevos + migración |

**REGLA DURA:** No arrancar Fase 1 hasta que Fase 0 esté DONE con todos los tests verdes. Si te saltás esto, lo que construyas encima se rompe.

---

## Contexto (para que entiendas el "por qué")

Post-Sprint 16 la state machine tiene 8 estados, 28+ commands, crédito funcional, 3 consolas (Brand, Client, Supplier), y 565 SKUs cargados. Pero hay problemas que bloquean el uso real:

1. **DESPACHO es inalcanzable** — el command que transiciona desde PREPARACION salta directo a TRANSITO. El estado existe en el enum pero nadie puede llegar ahí.

2. **REOPEN puede estar desconectado** — Sprint 16 implementó `c_reopen.py` pero quizás no lo conectó al dispatcher. No hay que reimplementarlo, solo verificar la conexión.

3. **El portal B2B no responde** — los endpoints se diseñaron pero el backend real puede no tenerlos o tenerlos incompletos.

4. **La firma de C1 es inconsistente** — `create.py` espera `(user, payload)` pero el dispatcher llama con `(payload, user)`.

5. **Hay páginas duplicadas** — dos listados y dos detalles de expedientes coexisten en el frontend.

6. **C22 vive fuera del dispatcher** — aislado en un módulo aparte, no integrado.

7. **El expediente no tiene campos operativos** — faltan ~30 campos por estado (números de factura, datos de envío, tracking, etc.) y 3 modelos nuevos (líneas de producto, órdenes de fábrica, pagos).

---

## Prerequisito

Sprint 16 DONE. Antes de tocar una línea de código, corré estos checks:

```bash
# 1. ¿Qué campos tiene Expediente hoy?
grep -n "Field\|CharField\|IntegerField\|DecimalField\|DateField\|URLField\|ForeignKey" backend/apps/expedientes/models.py | head -80

# 2. ¿Existe reopen_count?
grep -rn "reopen_count" backend/apps/expedientes/

# 3. ¿c_reopen está en el dispatcher?
grep -rn "reopen\|REOPEN" backend/apps/expedientes/services/

# 4. ¿Qué commands están registrados?
cat backend/apps/expedientes/services/constants.py | head -100

# 5. ¿ProductMaster existe?
grep -rn "class ProductMaster" backend/apps/productos/models.py

# 6. ¿ClientSubsidiary tiene payment_grace_days?
grep -rn "payment_grace_days" backend/apps/clientes/models.py

# 7. ¿Qué modelos existen en expedientes?
grep "^class " backend/apps/expedientes/models.py

# 8. Tests pasan?
pytest backend/ -v --tb=short 2>&1 | tail -20
```

**Si un campo o modelo que este sprint dice crear ya existe → NO lo creés de nuevo.** Sprint 13-16 pueden haberlo anticipado. Solo extendé si falta algo.

---

## Decisiones CEO ya resueltas (NO preguntar de nuevo)

Estas decisiones ya están tomadas. No las cuestiones, no propongas alternativas:

| Decisión | Qué significa para vos |
|----------|----------------------|
| `factory_order_number` genérico + modelo `FactoryOrder` | Campo flat en Expediente para queries rápidas + modelo relacional para detalle. No uses nombres SAP-specific. |
| Merge: CEO elige master manualmente | El merge es un endpoint con `{ target_expediente_id, master_id }`. Eso va en Sprint 18, no ahora. |
| Crédito = snapshot inicial + recálculo con pagos | Al crear (C1): capturás límite de CreditPolicy. Pagos recalculan localmente. Sin sincronización posterior. |
| ExpedienteProductLine con FK a ProductMaster | No texto libre. `unit_price` editable + `price_source`. SKU incluye talla. |
| PATCH por estado son ADICIONALES a commands | Commands = transiciones. PATCH = editar campos sin transicionar. PATCH va en Sprint 18. |
| Permisos granulares diferidos a Sprint 26 | El dispatcher mantiene lógica actual (superuser vs normal). No te metás con permisos. |

---

## Fase 0 — Bugs críticos (hacer primero, en orden)

### S17-01: Fix PREPARACION → DESPACHO

**El problema:** DESPACHO es inalcanzable — el command salta directo a TRANSITO.

**Qué hacer:**
```bash
grep -A5 "PREPARACION\|DESPACHO\|TRANSITO" backend/apps/expedientes/services/constants.py
```
Encontrá el command cuyo `requires_status` incluye PREPARACION y cambiá `transitions_to` a `DESPACHO`.

**Nota:** La state machine FROZEN numera C10/C11, pero Sprint 16 renumeró. Usá grep para encontrar el número real. No asumas.

**Done cuando:** El command transiciona a DESPACHO, no a TRANSITO. Tests existentes verdes (solo ajustar los que codificaron la transición incorrecta).

---

### S17-02: Asegurar DESPACHO → TRANSITO

**Depende de:** S17-01

**Qué hacer:**
```bash
grep -n "DESPACHO\|TRANSITO" backend/apps/expedientes/services/constants.py
```

**Si ya existe** un command DESPACHO→TRANSITO: verificar que funciona, que está en HANDLERS y URLs, que el frontend lo muestra. No crear nada.

**Si no existe:** Crear command "Confirmar Salida" con `requires_status: DESPACHO`, `transitions_to: TRANSITO`. Handler en `commands_despacho.py`. Registrar en HANDLERS, URLs. Actualizar `ExpedienteAccordion.tsx` (DESPACHO en mapping) y `GateMessage.tsx` (gate DESPACHO).

**Done cuando:** Flujo completo PREPARACION → DESPACHO → TRANSITO funciona.

---

### S17-03: Verificar REOPEN en dispatcher

**NO reimplementar.** `c_reopen.py` ya existe con restricción max 1 reapertura, solo CEO, re-evaluación de crédito.

**Solo verificar (en este orden):**
1. ¿REOPEN en COMMAND_SPEC? Si no → agregar
2. ¿URL registrada? Si no → agregar
3. ¿En HANDLERS dict? Si no → agregar apuntando a `c_reopen.handle_reopen`

**Done cuando:** Dispatcher puede llamar a REOPEN y funciona.

---

### S17-04: Portal — 3 endpoints con tenant isolation

**⚠️ Este es el item más delicado de seguridad.** Verificá primero qué hay:

```bash
grep -rn "portal" backend/apps/expedientes/urls*.py
grep -rn "Portal\|portal" backend/apps/expedientes/views*.py
```

**3 endpoints requeridos:**
- `GET /api/portal/expedientes/` — listado del cliente autenticado
- `GET /api/portal/expedientes/<pk>/` — detalle sin datos CEO-ONLY
- `GET /api/portal/expedientes/<pk>/artifacts/` — solo PUBLIC y PARTNER_B2B

**Seguridad obligatoria:**
- Toda query con `.for_user(request.user)`, nunca `.all()`
- Inexistente y ajeno = el MISMO 404 (no distinguir)
- Excluir del response: `fob_unit`, `margin_pct`, `commission_pct`, `landed_cost`, `dai_amount`, y cualquier campo con prefijo `internal_` o `ceo_`
- Artifacts filtrados por `visibility__in=['PUBLIC', 'PARTNER_B2B']`

**Done cuando:** 3 endpoints funcionales + 6 tests de seguridad verdes (cross-tenant, 404 uniforme, CEO-ONLY excluido, listado scoped, artifacts filtrados, same 404 body).

---

### S17-05: Fix firma handle_c1

**Sencillo:** `create.py` tiene `handle_c1(user, payload)` pero el dispatcher llama `handle_c1(payload, user)`. Unificar a `handle_c1(payload, user)`.

---

### S17-06: Eliminar páginas duplicadas

```bash
rm -rf frontend/src/app/[lang]/dashboard/expedientes/
```

Dejar solo `frontend/src/app/[lang]/(mwt)/(dashboard)/expedientes/`. Verificar navegación sin rutas rotas.

---

### S17-07: C22 al dispatcher

Mover lógica de `backend/expedientes/domain/c22_issue_commission_invoice.py` a `backend/apps/expedientes/services/commands_destino.py`. Registrar en COMMAND_SPEC + HANDLERS + URLs. Eliminar módulo aislado.

---

### Gate Fase 0

```
[ ] PREPARACION → DESPACHO funcional
[ ] DESPACHO → TRANSITO funcional
[ ] REOPEN conectado al dispatcher
[ ] Portal 3 endpoints + 6 tests seguridad
[ ] handle_c1 firma unificada
[ ] Páginas duplicadas eliminadas
[ ] C22 en dispatcher
[ ] Tests existentes verdes
[ ] Test nuevo: PREPARACION → DESPACHO → TRANSITO
```

**⛔ Si alguno falla, NO avanzar a Fase 1.**

---

## Fase 1 — Modelo de datos extendido

Todo en esta fase se junta en UNA SOLA migración al final. No generés migraciones parciales.

### S17-08: ~30 campos operativos en Expediente

Agregar campos organizados por estado. Todos `null=True, blank=True` excepto `reopen_count` (default=0). Cada campo con `help_text`.

**Campos por estado:**

**GENERALES:** `purchase_order_number`, `operado_por` (choices: CLIENTE/MWT), `url_orden_compra`

**REGISTRO:** `ref_number`, `credit_days_client`, `credit_days_mwt`, `credit_limit_client`, `credit_limit_mwt`, `order_value`

**PRODUCCION:** `factory_order_number`, `proforma_client_number`, `proforma_mwt_number`, `fabrication_start_date`, `fabrication_end_date`, `url_proforma_cliente`, `url_proforma_muito_work`, `master_expediente` (FK self, SET_NULL)

**PREPARACION:** `shipping_method`, `incoterms`, `cargo_manager` (choices: CLIENTE/FABRICA), `shipping_value`, `payment_mode_shipping` (choices: PREPAGO/CONTRAENTREGA), `url_list_empaque`, `url_cotizacion_envio`

**DESPACHO:** `airline_or_shipping_company`, `awb_bl_number`, `origin_location`, `arrival_location`, `shipment_date`, `payment_date_dispatch`, `invoice_client_number`, `invoice_mwt_number`, `dispatch_additional_info`, `url_certificado_origen`, `url_factura_cliente`, `url_factura_muito_work`, `url_awb_bl`, `tracking_url`

**TRANSITO:** `intermediate_airport_or_port`, `transit_arrival_date`, `url_packing_list_detallado`

**REOPEN:** `reopen_count` (IntegerField, default=0) — **solo agregar si NO existe ya**

**⚠️ NO generar migración todavía.** Se genera una sola al final.

---

### S17-09: Modelo ExpedienteProductLine

Crear modelo con FK a ProductMaster (PROTECT). Campos: `expediente` (FK CASCADE), `product` (FK PROTECT), `quantity`, `unit_price`, `price_source` (3 choices: pricelist/manual/override), `quantity_modified`, `unit_price_modified`, `modification_reason`, `separated_to_expediente` (FK self, SET_NULL), `factory_order` (FK FactoryOrder, SET_NULL), timestamps.

---

### S17-10: Modelo FactoryOrder

Crear modelo relacional. Campos: `expediente` (FK CASCADE), `order_number`, `proforma_client_number`, `proforma_mwt_number`, `purchase_number`, URLs proforma, timestamps. Meta: `ordering = ['created_at']`.

**Regla de sincronización:** Al crear el primer FactoryOrder de un expediente, copiar `order_number` al campo flat `expediente.factory_order_number`. Hacerlo en override de `save()`, NO en signals.

```python
def save(self, *args, **kwargs):
    super().save(*args, **kwargs)
    if not self.expediente.factory_order_number:
        self.expediente.factory_order_number = self.order_number
        self.expediente.save(update_fields=['factory_order_number'])
```

---

### S17-11: Modelo ExpedientePago

Registro operativo de pagos MWT. Coexiste con PaymentLine (C21). Campos: `expediente` (FK CASCADE), `tipo_pago` (COMPLETO/PARCIAL), `metodo_pago` (TRANSFERENCIA/NOTA_CREDITO), `payment_date`, `amount_paid`, `additional_info`, `url_comprobante`, `created_at`.

**La integración con PaymentLine se hace en la VIEW, NO en save(), NO en signals.** El modelo es limpio. La orquestación (crear pago + llamar C21 + recalcular crédito) se implementa en Sprint 18 en la view con `transaction.atomic()`.

**Verificar antes:**
```bash
grep -n "def handle_c21\|def register_payment" backend/apps/expedientes/services/
```

---

### S17-12: payment_grace_days en ClientSubsidiary

Agregar a `apps/clientes/models.py`:
```python
payment_grace_days = IntegerField(default=15,
    help_text="Días de gracia post-vencimiento antes de email cobranza")
```

---

### S17-13: Admin + migración única

1. Registrar los 3 modelos nuevos como inlines en ExpedienteAdmin
2. Generar UNA sola migración:

```bash
python manage.py makemigrations expedientes clientes \
  --name add_operational_fields_product_lines_factory_orders_pagos

# Verificar que es additive only (solo AddField, CreateModel — nada de Alter/Remove/Rename)
python manage.py sqlmigrate expedientes XXXX

python manage.py migrate
python manage.py check
```

---

### S17-14: Tests

**Archivos separados, no modificar tests existentes:**

- `test_sprint17_transitions.py` — PREPARACION→DESPACHO, DESPACHO→TRANSITO, flujo completo 8 estados, REOPEN funcional, REOPEN bloqueado si reopen_count >= 1
- `test_sprint17_portal.py` — 6 tests de seguridad (cross-tenant detalle, cross-tenant artifacts, same 404 body, listado scoped, CEO-ONLY excluido, artifacts visibility)
- `test_sprint17_models.py` — ProductLine con FK, FactoryOrder sync al campo flat, ExpedientePago campos requeridos, payment_grace_days default=15

---

## Lo que NO tenés que hacer

- ❌ Editar `ENT_OPS_STATE_MACHINE.md` (FROZEN)
- ❌ Reimplementar `c_reopen.py` (Sprint 16 — solo verificar conexión)
- ❌ Crear endpoints PATCH por estado (Sprint 18)
- ❌ Crear endpoints merge/split (Sprint 18)
- ❌ Crear CRUD de FactoryOrder (Sprint 18)
- ❌ Tocar frontend del expediente extendido (Sprint 19)
- ❌ Tocar docker-compose.yml, nginx/, settings de infra
- ❌ Inventar valores de negocio (crédito, pricing, tasas)
- ❌ Hacer ALTER destructivo, rename, o DROP de campos
- ❌ Múltiples migraciones parciales (UNA sola al final)

---

## Lo que sí tenés que hacer si te trabás

- Si necesitás un dato de negocio → marcar `# TODO: CEO_INPUT_REQUIRED` y seguir
- Si un test existente falla después de tu cambio → tu cambio tiene un bug, no el test
- Si algo del spec no queda claro → preguntale al CEO antes de asumir
- Si un campo que debés crear ya existe → no lo creés, solo verificá que tenga todo

---

## Checklist de entrega

```
ANTES DE EMPEZAR
[ ] Sprint 16 DONE, tests pasan
[ ] Verificación de 10 puntos corrida (grep arriba)

FASE 0
[ ] PREPARACION → DESPACHO funcional
[ ] DESPACHO → TRANSITO funcional
[ ] REOPEN en dispatcher
[ ] Portal 3 endpoints + 6 tests seguridad
[ ] handle_c1 firma (payload, user)
[ ] Páginas duplicadas eliminadas
[ ] C22 en dispatcher
[ ] Tests existentes verdes

FASE 1
[ ] ~30 campos operativos con help_text
[ ] ExpedienteProductLine con FK ProductMaster
[ ] FactoryOrder con sync vía save()
[ ] ExpedientePago (modelo limpio, integración C21 diferida a view Sprint 18)
[ ] payment_grace_days en ClientSubsidiary
[ ] 1 migración consolidada aplicada
[ ] Admin con inlines
[ ] Tests nuevos verdes + existentes verdes

CI/CD
[ ] python manage.py test
[ ] bandit -ll backend/
[ ] npm run lint && npm run typecheck
[ ] Conventional commits
```

---

## Reporte de ejecución (entregá esto al terminar)

```markdown
## Resultado de ejecución
- **Agente:** AG-02 Alejandro
- **Lote:** LOTE_SM_SPRINT17
- **Status:** DONE / PARTIAL / BLOCKED
- **Archivos creados:** [lista]
- **Archivos modificados:** [lista]
- **Archivos NO tocados (fuera de scope):** [confirmar]
- **Decisiones asumidas:** [lista — cualquier cosa que decidiste sin spec explícita]
- **Blockers:** [lista o "ninguno"]
- **Tests ejecutados:** [resumen]
- **TODO CEO_INPUT_REQUIRED:** [si quedó alguno]
```
