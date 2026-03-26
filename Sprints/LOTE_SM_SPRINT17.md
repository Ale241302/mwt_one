# LOTE_SM_SPRINT17 — Estabilización + Modelo de Datos Expedientes Extended
id: LOTE_SM_SPRINT17
version: 1.3
visibility: [INTERNAL]
domain: Plataforma (IDX_PLATAFORMA)
status: DRAFT — Pendiente aprobación CEO
stamp: DRAFT v1.3 — 2026-03-25
tipo: Lote ruteado (ref → PLB_ORCHESTRATOR §E)
sprint: 17
priority: P0
depends_on: LOTE_SM_SPRINT16 (DONE)
refs: ENT_OPS_STATE_MACHINE (FROZEN v1.2.2), PROMPT_ANTIGRAVITY_EXPEDIENTES_EXTENDED (Fases 0+1),
      ROADMAP_SPRINTS_17_27, MANIFIESTO_APPEND_20260325_EXPEDIENTES_EXTENDED,
      ENT_GOB_DECISIONES (DEC-EXP-01 a DEC-EXP-05), ENT_PLAT_SEGURIDAD,
      ENT_COMERCIAL_PRICING (SSOT pricing), ENT_PLAT_LEGAL_ENTITY

changelog:
  - v1.0 (2026-03-25): Compilación inicial desde ROADMAP Sprint 17 + PROMPT_ANTIGRAVITY_EXPEDIENTES_EXTENDED Fases 0-1.
  - v1.1 (2026-03-25): Fixes auditoría R1 (ChatGPT 8.3/10). H1: nota aclaratoria numeración commands. H2: S17-04 auditar+completar. H3: determinismo FactoryOrder→save(), ExpedientePago→view+atomic. H4: stamp en header. H5: +3 tests portal. H6: DONE items 9-11 obligatorios. H7: docstring→help_text.
  - v1.2 (2026-03-25): Fixes auditoría R2 (ChatGPT 9.1/10). S17-01/02 nombres funcionales, Caso A/B en S17-02, regla tests unificada, S17-12 help_text.
  - v1.3 (2026-03-25): Fixes auditoría R3 (ChatGPT 9.6/10 — APROBADO). F1: regla genérica prefijos internal_/ceo_ en serializer portal. F2: npm lint+typecheck subido a DONE obligatorio. F3: S17-10 dependencia corregida a factory_order_number.

---

## Contexto

Sprint 17 es el primero del ROADMAP_SPRINTS_17_27. Su objetivo es estabilizar bugs críticos heredados de Sprints 13-16 y extender el modelo de datos del expediente con campos operativos, líneas de producto, órdenes de fábrica y pagos estructurados.

**Estado post-Sprint 16 (DONE):**
- State machine 8 estados, 28+ commands con lógica real
- CreditPolicy + CreditExposure + CreditOverride funcionales
- c_cancel + c_reopen implementados con credit release
- Suppliers app completa (models + API + UI 4 tabs)
- Brand Console (6 tabs) + Client Console (7 tabs) + Supplier Console (4 tabs)
- ProductMaster 565 SKUs cargados
- Knowledge fix: /ask/ retorna 200 en vacío

**Lo que falta (scope de este sprint):**
- DESPACHO inalcanzable (C11 salta a TRANSITO)
- REOPEN posiblemente desconectado del dispatcher
- Portal sin endpoints backend
- Firma C1 inconsistente
- Páginas frontend duplicadas
- C22 aislado fuera del dispatcher
- Campos operativos por estado (~30 campos)
- ExpedienteProductLine, FactoryOrder, ExpedientePago (modelos nuevos)
- payment_grace_days en ClientSubsidiary

---

## Decisiones CEO ya resueltas (NO preguntar de nuevo)

| Decisión | Ref ADR | Detalle |
|----------|---------|---------|
| `factory_order_number` genérico (no `sap_number`) + modelo `FactoryOrder` relacional | DEC-EXP-01 | Campo flat para acceso rápido + modelo relacional para detalle. Multi-fabricante. |
| Merge: CEO elige master manualmente | DEC-EXP-02 | Endpoint recibe `{ target_expediente_id, master_id }`. Modal UI con selector. |
| Crédito = snapshot inicial + recálculo con pagos del expediente | DEC-EXP-03 | Al crear (C1): captura límite de CreditPolicy. Pagos recalculan localmente. Sin sincronización posterior. |
| ExpedienteProductLine con FK a ProductMaster (no texto libre) | DEC-EXP-04 | `unit_price` editable + `price_source` (pricelist/manual/override). SKU incluye talla. |
| PATCH por estado son ADICIONALES a commands (no reemplazo) | DEC-EXP-05 | Commands = transiciones. PATCH = edición de campos operativos sin transicionar. |
| Gracia cobranza: 15 días configurable por cliente | — | `payment_grace_days` en ClientSubsidiary (default 15). |
| REOPEN: ya existe c_reopen.py (Sprint 16) | — | Solo verificar conexión al dispatcher, no reimplementar. |
| Permisos granulares: diferido a Sprint 26 | — | Dispatcher mantiene lógica actual (superuser vs normal). |

---

## Convenciones

### CV1. Migraciones additive only
Solo agregar campos (nullable o con default). Nunca ALTER destructivo, rename, ni DROP. Una sola migración consolidada. Reversible con `RemoveField`.

### CV2. No romper commands existentes
Commands C1-C16, C22, c_cancel, c_reopen, ceo-override: mismos inputs → mismos outputs. Si un test existente falla, es bug del sprint.

### CV3. ENT_OPS_STATE_MACHINE es FROZEN
Los 8 estados canónicos no se modifican. Los cambios se implementan alineando el CÓDIGO con la spec, no editando la spec.

### CV4. Verificación antes de implementar
Sprint 13-16 agregaron bastante. Antes de crear cualquier campo o modelo, verificar si ya existe en el codebase (grep). Si existe, NO crearlo de nuevo — solo extender si falta algo.

### CV5. Conventional Commits
`feat:`, `fix:`, `refactor:`, `test:`. Nunca commits genéricos.

---

## Fases y orden de ejecución

```
FASE 0 — Bugs críticos (S17-01 a S17-07)
    ⛔ NO avanzar a Fase 1 hasta que Fase 0 DONE + tests verdes
FASE 1 — Modelo de datos (S17-08 a S17-14)
    Una sola migración consolidada al final
```

---

## FASE 0 — BUGS CRÍTICOS

Estabilizar lo existente antes de agregar funcionalidad. Sin esto, lo que se construya encima se rompe.

---

### S17-01 — Fix command_preparacion_despacho: debe transicionar a DESPACHO

**Agente:** AG-02 Backend
**Dependencia:** Ninguna
**Prioridad:** P0

**Problema:** El estado DESPACHO existe en el enum pero es inalcanzable — el command que transiciona desde PREPARACION salta directamente a TRANSITO.

**Nota de compatibilidad (leer una vez, luego ignorar):** La state machine FROZEN numera C10=ApproveDispatch→DESPACHO y C11=ConfirmShipmentDeparted→TRANSITO. Sprint 16 renumeró internamente. El código real puede usar cualquier número. Este LOTE usa nombres funcionales (`command_preparacion_despacho`, `command_despacho_transito`) para evitar ambigüedad. Code determina el número real con `grep` antes de actuar.

**Verificación previa obligatoria:**
```bash
grep -A5 "PREPARACION\|DESPACHO\|TRANSITO" backend/apps/expedientes/services/constants.py
```

**Solución:** Encontrar el command cuyo `requires_status` incluye PREPARACION y cambiar su `transitions_to` a `DESPACHO`.

**Archivos a tocar:**
- `backend/apps/expedientes/services/constants.py` — entry del command que transiciona desde PREPARACION

**Archivos prohibidos:** ENT_OPS_STATE_MACHINE (FROZEN), docker-compose.yml, nginx/, config/settings/

**Criterio de done:**
- [ ] command_preparacion_despacho transiciona a DESPACHO (no a TRANSITO)
- [ ] Tests existentes no se modifican, salvo los que codificaron la transición incorrecta heredada; cualquier cambio se limita a esa corrección

---

### S17-02 — Asegurar command_despacho_transito: DESPACHO → TRANSITO

**Agente:** AG-02 Backend
**Dependencia:** S17-01 (command_preparacion_despacho corregido)
**Prioridad:** P0

**Problema:** Con DESPACHO alcanzable, debe existir un command para DESPACHO→TRANSITO.

**Verificación previa obligatoria:**
```bash
grep -n "DESPACHO\|TRANSITO" backend/apps/expedientes/services/constants.py
```

**Caso A — ya existe command DESPACHO→TRANSITO:**
No crear nada. Solo verificar que funciona, que está en HANDLERS y URLs, y que el frontend muestra DESPACHO en acordeón y gate. Testear flujo completo.

**Caso B — no existe command DESPACHO→TRANSITO:**
Crear command nuevo "Confirmar Salida":
- Agregar en `COMMAND_SPEC`: `requires_status: DESPACHO`, `transitions_to: TRANSITO`
- Crear handler en `backend/apps/expedientes/services/commands_despacho.py`
- Registrar en HANDLERS dict y URLs
- Actualizar frontend: `ExpedienteAccordion.tsx` (DESPACHO en mapping) + `GateMessage.tsx` (gate DESPACHO)

**Archivos a tocar (solo Caso B):**
- `backend/apps/expedientes/services/constants.py`
- `backend/apps/expedientes/services/__init__.py`
- Crear `backend/apps/expedientes/services/commands_despacho.py`
- `frontend/src/components/expediente/ExpedienteAccordion.tsx`
- `frontend/src/components/expediente/GateMessage.tsx`

**Archivos prohibidos:** ENT_OPS_STATE_MACHINE (FROZEN)

**Criterio de done:**
- [ ] Existe command funcional DESPACHO → TRANSITO (existente verificado o nuevo creado)
- [ ] Handler con EventLog
- [ ] Registrado en HANDLERS y URLs
- [ ] Frontend muestra DESPACHO en acordeón y gate
- [ ] Test: flujo completo PREPARACION → DESPACHO → TRANSITO

---

### S17-03 — Verificar REOPEN en COMMAND_SPEC + URL + HANDLERS

**Agente:** AG-02 Backend
**Dependencia:** Ninguna
**Prioridad:** P0

**Contexto:** Sprint 16 implementó `c_reopen.py` con restricción max 1 reapertura y re-evaluación de crédito. **NO reimplementar.** Lo que puede faltar es la conexión al dispatcher.

**Verificar (en este orden):**
1. ¿`REOPEN` está en `COMMAND_SPEC`? Si no → agregar: `requires_status: ["CANCELADO"]`, `transitions_to: "REGISTRO"`, `requires_ceo: True`
2. ¿Hay ruta URL para REOPEN en `urls.py`? Si no → agregar
3. ¿Está en `HANDLERS` dict en `__init__.py`? Si no → agregar apuntando a `c_reopen.handle_reopen`
4. Verificar que handler existente ya tiene: constraint max 1, solo CEO, re-evaluación crédito, EventLog

**Archivos a tocar (solo si falta conexión):**
- `backend/apps/expedientes/services/constants.py`
- `backend/apps/expedientes/services/__init__.py`
- `backend/apps/expedientes/urls.py`

**Archivos prohibidos:** `c_reopen.py` (ya implementado Sprint 16 — NO modificar lógica)

**Criterio de done:**
- [ ] REOPEN en COMMAND_SPEC, HANDLERS, y URLs
- [ ] Dispatcher conectado al handler existente
- [ ] Test: expediente CANCELADO → REOPEN → status=REGISTRO (si reopen_count < 1)

---

### S17-04 — Auditar, endurecer y completar endpoints Portal

**Agente:** AG-02 Backend
**Dependencia:** Ninguna
**Prioridad:** P0

**Contexto:** Sprints 14-16 diseñaron y parcialmente implementaron endpoints de portal B2B. El frontend portal (S15) consume estos endpoints. Sin embargo, el diagnóstico de Code detectó que algunos endpoints no responden o faltan en el backend real. **NO asumir que no existe nada — verificar primero qué hay, completar lo que falta, endurecer lo que existe.**

**Verificación previa obligatoria:**
```bash
# ¿Qué rutas portal existen?
grep -rn "portal" backend/apps/expedientes/urls*.py
grep -rn "portal" backend/apps/*/urls*.py
# ¿Qué views portal existen?
grep -rn "Portal\|portal" backend/apps/expedientes/views*.py
```

**3 endpoints requeridos (crear si no existen, endurecer si existen):**
```
GET /api/portal/expedientes/                  — listado filtrado por cliente del usuario
GET /api/portal/expedientes/<pk>/             — bundle simplificado (sin datos CEO-ONLY)
GET /api/portal/expedientes/<pk>/artifacts/   — artifacts visibles para cliente
```

**Seguridad obligatoria (ref ENT_PLAT_SEGURIDAD):**
- Toda query usa `.for_user(request.user)` (ClientScopedManager), nunca `.all()`
- Expediente inexistente y expediente ajeno retornan el MISMO 404 (no distinguir "no existe" de "no tienes acceso")
- Datos CEO-ONLY nunca en el response: costos internos, márgenes, notas internas, fob_unit, margin_pct, commission_pct, landed_cost, dai_amount. **Regla genérica adicional:** excluir cualquier campo con prefijo `internal_` o `ceo_`.
- `/artifacts/` filtra solo `visibility__in=['PUBLIC', 'PARTNER_B2B']`

**Archivos a tocar:**
- `backend/apps/expedientes/views_portal.py` (crear o extender existente)
- `backend/apps/expedientes/urls.py` — rutas portal (agregar si faltan)
- `backend/apps/expedientes/serializers_portal.py` — serializers sin campos CEO-ONLY (crear o extender)

**Archivos prohibidos:** Ninguno

**Criterio de done:**
- [ ] 3 endpoints funcionales con JWT auth
- [ ] Cliente A no ve expedientes de Cliente B (404 uniforme)
- [ ] Response sin campos CEO-ONLY ni campos con prefijo `internal_` o `ceo_`
- [ ] Listado retorna solo expedientes del tenant autenticado
- [ ] `/artifacts/` retorna solo artifacts con visibility PUBLIC o PARTNER_B2B
- [ ] Test: cross-tenant → 404, inexistente → 404 (mismo body)

---

### S17-05 — Fix firma handle_c1

**Agente:** AG-02 Backend
**Dependencia:** Ninguna
**Prioridad:** P1

**Problema:** `create.py` tiene `handle_c1(user, payload)` pero `__init__.py` lo llama como `handle_c1(request.data, request.user)`. Orden de argumentos inconsistente.

**Solución:** Unificar. `create.py` debe recibir `(payload, user)` consistente con el dispatcher.

**Archivos a tocar:**
- `backend/apps/expedientes/services/commands/create.py` — firma de handle_c1

**Archivos prohibidos:** Ninguno

**Criterio de done:**
- [ ] Firma unificada: `handle_c1(payload, user)`
- [ ] Dispatcher llama correctamente
- [ ] Test existente de C1 sigue verde

---

### S17-06 — Eliminar páginas frontend duplicadas

**Agente:** AG-02 Backend / AG-03 Frontend
**Dependencia:** Ninguna
**Prioridad:** P1

**Problema:** Dos listados y dos detalles de expedientes coexisten.

**Solución:** Borrar `frontend/src/app/[lang]/dashboard/expedientes/` (versión vieja). Dejar solo `frontend/src/app/[lang]/(mwt)/(dashboard)/expedientes/`.

**Archivos a tocar:**
- Eliminar directorio `frontend/src/app/[lang]/dashboard/expedientes/`

**Archivos prohibidos:** `frontend/src/app/[lang]/(mwt)/(dashboard)/expedientes/` (versión canónica — no tocar)

**Criterio de done:**
- [ ] Solo una versión de listado y detalle de expedientes
- [ ] Navegación funcional sin rutas rotas

---

### S17-07 — Integrar C22 al dispatcher central

**Agente:** AG-02 Backend
**Dependencia:** Ninguna
**Prioridad:** P1

**Problema:** C22 vive en `backend/expedientes/` (fuera de `apps/expedientes/`). Está aislado del dispatcher central.

**Solución:** Mover lógica de `backend/expedientes/domain/c22_issue_commission_invoice.py` a `backend/apps/expedientes/services/commands_destino.py`. Registrar en HANDLERS dict. Eliminar módulo aislado.

**Archivos a tocar:**
- Crear o extender `backend/apps/expedientes/services/commands_destino.py`
- `backend/apps/expedientes/services/__init__.py` — +C22 en HANDLERS
- `backend/apps/expedientes/services/constants.py` — +C22 en COMMAND_SPEC si falta
- Eliminar `backend/expedientes/domain/c22_issue_commission_invoice.py` (post-migración)

**Archivos prohibidos:** Ninguno

**Criterio de done:**
- [ ] C22 en COMMAND_SPEC + HANDLERS + URLs
- [ ] Lógica movida al dispatcher
- [ ] Módulo aislado eliminado
- [ ] Test: C22 funcional desde dispatcher

---

### Gate Fase 0 DONE

```
[ ] Command PREPARACION → DESPACHO funcional (alineado con state machine FROZEN T4)
[ ] Command DESPACHO → TRANSITO funcional (alineado con state machine FROZEN T5)
[ ] REOPEN: verificado en COMMAND_SPEC + URL + HANDLERS
[ ] Portal: 3 endpoints funcionales con tenant isolation + 404 uniforme + CEO-ONLY excluido
[ ] handle_c1: firma unificada (payload, user)
[ ] Páginas duplicadas eliminadas
[ ] C22 integrado en dispatcher
[ ] Tests existentes no se modifican, salvo los que codificaron una transición incorrecta heredada; cualquier cambio se limita a esa corrección
[ ] Test nuevo: PREPARACION→DESPACHO→TRANSITO flujo completo
```

**⛔ NO avanzar a Fase 1 hasta que TODOS los checks pasen.**

---

## FASE 1 — MODELO DE DATOS EXTENDIDO

Una sola migración aditiva al final de la fase. Todos los campos nuevos `null=True, blank=True` salvo que se indique.

---

### S17-08 — Campos operativos en modelo Expediente (~30 campos)

**Agente:** AG-02 Backend
**Dependencia:** Fase 0 DONE
**Prioridad:** P0

**Acción:** Agregar campos operativos al modelo `Expediente` organizados por estado. Verificar ANTES si alguno ya existe (Sprint 13-16 pueden haberlos creado).

**Campos GENERALES:**
- `purchase_order_number` — CharField(max_length=100)
- `operado_por` — CharField(max_length=20, choices=[('CLIENTE','Cliente'),('MWT','Muito Work Limitada')])
- `url_orden_compra` — URLField(max_length=500)

**Campos REGISTRO:**
- `ref_number` — CharField(max_length=100)
- `credit_days_client` — IntegerField
- `credit_days_mwt` — IntegerField
- `credit_limit_client` — DecimalField(max_digits=12, decimal_places=2) — snapshot de CreditPolicy (DEC-EXP-03)
- `credit_limit_mwt` — DecimalField(max_digits=12, decimal_places=2) — snapshot de CreditPolicy (DEC-EXP-03)
- `order_value` — DecimalField(max_digits=12, decimal_places=2)

**Campos PRODUCCION:**
- `factory_order_number` — CharField(max_length=100) — número de la orden principal (DEC-EXP-01)
- `proforma_client_number` — CharField(max_length=100)
- `proforma_mwt_number` — CharField(max_length=100)
- `fabrication_start_date` — DateField
- `fabrication_end_date` — DateField
- `url_proforma_cliente` — URLField(max_length=500)
- `url_proforma_muito_work` — URLField(max_length=500)
- `master_expediente` — ForeignKey('self', null=True, on_delete=SET_NULL, related_name='merged_followers')

**Campos PREPARACION:**
- `shipping_method` — CharField(max_length=100)
- `incoterms` — CharField(max_length=20)
- `cargo_manager` — CharField(max_length=20, choices=[('CLIENTE','Cliente'),('FABRICA','Fábrica')])
- `shipping_value` — DecimalField(max_digits=12, decimal_places=2)
- `payment_mode_shipping` — CharField(max_length=20, choices=[('PREPAGO','Prepago'),('CONTRAENTREGA','Contraentrega')])
- `url_list_empaque` — URLField(max_length=500)
- `url_cotizacion_envio` — URLField(max_length=500)

**Campos DESPACHO:**
- `airline_or_shipping_company` — CharField(max_length=200)
- `awb_bl_number` — CharField(max_length=100)
- `origin_location` — CharField(max_length=200)
- `arrival_location` — CharField(max_length=200)
- `shipment_date` — DateField
- `payment_date_dispatch` — DateField
- `invoice_client_number` — CharField(max_length=100)
- `invoice_mwt_number` — CharField(max_length=100)
- `dispatch_additional_info` — TextField
- `url_certificado_origen` — URLField(max_length=500)
- `url_factura_cliente` — URLField(max_length=500)
- `url_factura_muito_work` — URLField(max_length=500)
- `url_awb_bl` — URLField(max_length=500)
- `tracking_url` — URLField(max_length=500)

**Campos TRANSITO:**
- `intermediate_airport_or_port` — CharField(max_length=200)
- `transit_arrival_date` — DateField
- `url_packing_list_detallado` — URLField(max_length=500)

**REOPEN (verificar si Sprint 16 ya lo creó):**
- `reopen_count` — IntegerField(default=0) — solo agregar si NO existe

**Archivos a tocar:**
- `backend/apps/expedientes/models.py` — agregar campos
- NO generar migración todavía (se genera una sola al final de Fase 1)

**Archivos prohibidos:** ENT_OPS_STATE_MACHINE (FROZEN)

**Criterio de done:**
- [ ] ~30 campos nuevos declarados en models.py (todos nullable excepto reopen_count)
- [ ] Ningún campo existente modificado ni eliminado
- [ ] Cada campo nuevo con `help_text=` o comentario inline agrupado por estado (## REGISTRO, ## PRODUCCION, etc.)

---

### S17-09 — Modelo ExpedienteProductLine

**Agente:** AG-02 Backend
**Dependencia:** S17-08 (campos en Expediente)
**Prioridad:** P0

**Acción:** Crear modelo `ExpedienteProductLine` con FK a ProductMaster (DEC-EXP-04).

**Campos:**
- `expediente` — FK(Expediente, CASCADE, related_name='product_lines')
- `product` — FK('productos.ProductMaster', PROTECT, related_name='expediente_lines')
- `quantity` — PositiveIntegerField
- `unit_price` — DecimalField(max_digits=12, decimal_places=2) — editable, inicializado desde resolve_client_price() si disponible
- `price_source` — CharField(max_length=30, default='manual', choices=[('pricelist','Lista de precios activa'),('manual','Ingresado manualmente'),('override','Override por expediente')])
- `quantity_modified` — PositiveIntegerField(null=True)
- `unit_price_modified` — DecimalField(max_digits=12, decimal_places=2, null=True)
- `modification_reason` — CharField(max_length=200, null=True)
- `separated_to_expediente` — FK(Expediente, null=True, SET_NULL, related_name='received_lines')
- `factory_order` — FK('FactoryOrder', null=True, SET_NULL, related_name='product_lines')
- `created_at` — DateTimeField(auto_now_add=True)
- `updated_at` — DateTimeField(auto_now=True)

**Archivos a tocar:**
- `backend/apps/expedientes/models.py` — nueva clase

**Archivos prohibidos:** `backend/apps/productos/models.py` (ProductMaster no se toca — solo se referencia)

**Criterio de done:**
- [ ] Modelo creado con FK a ProductMaster (PROTECT)
- [ ] price_source con 3 choices documentados
- [ ] Campos de modificación (quantity_modified, unit_price_modified) separados de originales
- [ ] separated_to_expediente para trazabilidad de separación

---

### S17-10 — Modelo FactoryOrder

**Agente:** AG-02 Backend
**Dependencia:** S17-08 (campo factory_order_number en Expediente)
**Prioridad:** P0

**Acción:** Crear modelo `FactoryOrder` relacional (DEC-EXP-01).

**Campos:**
- `expediente` — FK(Expediente, CASCADE, related_name='factory_orders')
- `order_number` — CharField(max_length=100) — número en sistema del fabricante (SAP para Marluvas, otro para otros)
- `proforma_client_number` — CharField(max_length=100, null=True)
- `proforma_mwt_number` — CharField(max_length=100, null=True)
- `purchase_number` — CharField(max_length=100, null=True)
- `url_proforma_client` — URLField(max_length=500, null=True)
- `url_proforma_mwt` — URLField(max_length=500, null=True)
- `created_at` — DateTimeField(auto_now_add=True)
- `updated_at` — DateTimeField(auto_now=True)
- Meta: `ordering = ['created_at']`

**Regla de sincronización:** Al crear el primer FactoryOrder de un expediente, copiar `order_number` al campo flat `expediente.factory_order_number`. **Punto de orquestación único: override de `save()` en el modelo FactoryOrder.** NO usar signals. NO delegar a la view. El modelo es responsable de esta invariante.

```python
def save(self, *args, **kwargs):
    super().save(*args, **kwargs)
    if not self.expediente.factory_order_number:
        self.expediente.factory_order_number = self.order_number
        self.expediente.save(update_fields=['factory_order_number'])
```

**Archivos a tocar:**
- `backend/apps/expedientes/models.py` — nueva clase

**Criterio de done:**
- [ ] Modelo creado con campos genéricos (no SAP-specific)
- [ ] Relación FK a Expediente (CASCADE)
- [ ] Ordering por created_at

---

### S17-11 — Modelo ExpedientePago

**Agente:** AG-02 Backend
**Dependencia:** S17-08
**Prioridad:** P0

**Acción:** Crear modelo `ExpedientePago` (registro operativo de pagos MWT).

**Campos:**
- `expediente` — FK(Expediente, CASCADE, related_name='pagos')
- `tipo_pago` — CharField(max_length=20, choices=[('COMPLETO','Completo'),('PARCIAL','Pago Parcial')])
- `metodo_pago` — CharField(max_length=30, choices=[('TRANSFERENCIA','Transferencia Bancaria'),('NOTA_CREDITO','Nota de Crédito')])
- `payment_date` — DateField
- `amount_paid` — DecimalField(max_digits=12, decimal_places=2)
- `additional_info` — TextField(null=True)
- `url_comprobante` — URLField(max_length=500, null=True)
- `created_at` — DateTimeField(auto_now_add=True)

**Coexistencia con PaymentLine — contrato de integración fijado:**

`PaymentLine` es el ledger append-only del sistema de commands (C21, Sprint 16). `ExpedientePago` es el registro operativo con campos de dominio MWT. Coexisten.

**Punto de orquestación único: la VIEW que crea ExpedientePago.** NO en save() del modelo, NO en signals. La view hace todo dentro de `transaction.atomic()`:
1. Crear `ExpedientePago`
2. Llamar a `handle_c21` (o crear `PaymentLine` directamente si C21 no acepta los campos nuevos) para mantener el audit trail
3. Recalcular crédito del expediente

**Verificación previa obligatoria:**
```bash
# ¿Qué acepta handle_c21?
grep -n "def handle_c21\|def register_payment" backend/apps/expedientes/services/
cat backend/apps/expedientes/services/financial.py | head -50
```

Si `handle_c21` ya acepta amount + date → `ExpedientePago` es wrapper que lo invoca.
Si `handle_c21` no acepta los campos de dominio → `ExpedientePago` crea `PaymentLine` directamente + EventLog.

**Archivos a tocar:**
- `backend/apps/expedientes/models.py` — nueva clase

**Criterio de done:**
- [ ] Modelo creado con choices para tipo y método de pago
- [ ] Campo url_comprobante para documento de soporte
- [ ] Documentado cómo coexiste con PaymentLine (C21)

---

### S17-12 — Campo payment_grace_days en ClientSubsidiary

**Agente:** AG-02 Backend
**Dependencia:** Ninguna (paralelo con S17-08)
**Prioridad:** P1

**Acción:** Agregar campo de días de gracia de cobranza a ClientSubsidiary (config del cliente, no del expediente).

**Campo:**
- `payment_grace_days` — IntegerField(default=15) — días post-vencimiento antes de enviar email de cobranza. Editable por CEO en sección del cliente.

**Archivos a tocar:**
- `backend/apps/clientes/models.py` — agregar campo a ClientSubsidiary

**Criterio de done:**
- [ ] Campo agregado con default=15 y `help_text` explícito

---

### S17-13 — Registrar en admin + migración única

**Agente:** AG-02 Backend
**Dependencia:** S17-08 a S17-12 (todos los modelos y campos)
**Prioridad:** P0

**Acción:**
1. Registrar ExpedienteProductLine, FactoryOrder, ExpedientePago en Django admin (inline en ExpedienteAdmin cuando aplique)
2. Generar UNA SOLA migración consolidada:
```bash
python manage.py makemigrations expedientes clientes --name add_operational_fields_product_lines_factory_orders_pagos
```

**Archivos a tocar:**
- `backend/apps/expedientes/admin.py` — inlines nuevos
- Migración generada automáticamente

**Criterio de done:**
- [ ] Migración única generada (no múltiples migraciones parciales)
- [ ] Migración reversible con RemoveField
- [ ] Admin registrado con inlines para los 3 modelos nuevos
- [ ] `python manage.py migrate` exitoso
- [ ] `python manage.py check` sin warnings

---

### S17-14 — Tests: transiciones, portal, modelos nuevos

**Agente:** AG-02 Backend
**Dependencia:** S17-13 (migración aplicada)
**Prioridad:** P0

**Tests nuevos (archivos separados, no modificar tests existentes):**

**Tests de transición:**
- [ ] Test PREPARACION → DESPACHO (command corregido)
- [ ] Test DESPACHO → TRANSITO (command existente o nuevo)
- [ ] Test flujo completo: REGISTRO → PRODUCCION → PREPARACION → DESPACHO → TRANSITO → EN_DESTINO → CERRADO
- [ ] Test REOPEN: CANCELADO → REGISTRO (si reopen_count < 1)
- [ ] Test REOPEN bloqueado: reopen_count >= 1 → error

**Tests portal tenant isolation (6 tests obligatorios):**
- [ ] Test cross-tenant detalle: cliente A GET /portal/expedientes/{id_B}/ → 404
- [ ] Test cross-tenant artifacts: cliente A GET /portal/expedientes/{id_B}/artifacts/ → 404
- [ ] Test same 404 semantics: inexistente y ajeno → mismo 404 body
- [ ] Test listado scoped: GET /portal/expedientes/ retorna SOLO expedientes del tenant autenticado
- [ ] Test CEO-ONLY no expuesto: response portal sin fob_unit, margin_pct, commission_pct, landed_cost, dai_amount
- [ ] Test artifacts visibility filter: /artifacts/ retorna solo artifacts con visibility PUBLIC o PARTNER_B2B

**Tests modelos nuevos:**
- [ ] Test crear ExpedienteProductLine con FK a ProductMaster
- [ ] Test crear FactoryOrder — primer order copia number al campo flat del expediente
- [ ] Test crear ExpedientePago con campos requeridos
- [ ] Test payment_grace_days default=15 en ClientSubsidiary nueva

**Archivos a tocar:**
- Crear `backend/apps/expedientes/tests/test_sprint17_transitions.py`
- Crear `backend/apps/expedientes/tests/test_sprint17_portal.py`
- Crear `backend/apps/expedientes/tests/test_sprint17_models.py`

**Criterio de done:**
- [ ] Todos los tests nuevos verdes
- [ ] Tests existentes (pre-Sprint 17) verdes sin modificación
- [ ] Coverage de los 3 modelos nuevos + 2 transiciones corregidas + portal

---

## Migration Plan

Una sola migración consolidada al final de Fase 1:

```bash
# 1. Verificar estado limpio
python manage.py showmigrations expedientes clientes

# 2. Generar migración
python manage.py makemigrations expedientes clientes --name add_operational_fields_product_lines_factory_orders_pagos

# 3. Verificar que es additive only (solo AddField, CreateModel — no AlterField, RemoveField, RenameField)
python manage.py sqlmigrate expedientes XXXX

# 4. Aplicar
python manage.py migrate

# 5. Verificar
python manage.py check
python manage.py test
```

**Rollback:** La migración es reversible. Todos los campos son nullable o tienen default. `RemoveField` + `DeleteModel` para cada adición.

---

## Checklist completa Sprint 17

### Fase 0 — Bugs
- [ ] S17-01: command_preparacion_despacho → DESPACHO funcional
- [ ] S17-02: command_despacho_transito → TRANSITO funcional
- [ ] S17-03: REOPEN conectado al dispatcher
- [ ] S17-04: Portal 3 endpoints con tenant isolation (6 tests seguridad)
- [ ] S17-05: handle_c1 firma unificada
- [ ] S17-06: Páginas duplicadas eliminadas
- [ ] S17-07: C22 integrado en dispatcher

### Fase 1 — Modelos
- [ ] S17-08: ~30 campos operativos en Expediente
- [ ] S17-09: ExpedienteProductLine (FK ProductMaster)
- [ ] S17-10: FactoryOrder (relacional)
- [ ] S17-11: ExpedientePago (coexiste con PaymentLine)
- [ ] S17-12: payment_grace_days en ClientSubsidiary
- [ ] S17-13: Admin + migración única
- [ ] S17-14: Tests nuevos + existentes verdes

### CI/CD
- [ ] `python manage.py test` verde
- [ ] `bandit -ll backend/` sin high/critical
- [ ] `npm run lint && npm run typecheck` verde (cambios frontend mínimos: acordeón + gate DESPACHO)
- [ ] Conventional commits en todos los commits

---

## Dependencias internas

```
S17-01 (command_preparacion_despacho) ──→ S17-02 (command_despacho_transito)
                                              │
S17-03 (REOPEN) ──────────────────────────── │ ─── paralelo
S17-04 (Portal) ──────────────────────────── │ ─── paralelo
S17-05 (Fix C1) ──────────────────────────── │ ─── paralelo
S17-06 (Duplicados) ─────────────────────── │ ─── paralelo
S17-07 (C22) ─────────────────────────────── │ ─── paralelo
                                              │
                              GATE FASE 0 DONE
                  │
     ┌────────────┼────────────┐
     │            │            │
  S17-08      S17-12       (paralelo)
  (Campos)   (grace_days)
     │
     ├── S17-09 (ProductLine)
     ├── S17-10 (FactoryOrder)
     └── S17-11 (Pago)
              │
          S17-13 (Admin + Migración)
              │
          S17-14 (Tests)
```

---

## Excluido explícitamente de Sprint 17

| Feature | Razón | Cuándo |
|---------|-------|--------|
| Endpoints PATCH por estado | Sprint 18 | Después de modelos estables |
| Merge/Split endpoints | Sprint 18 | Endpoints backend |
| CRUD FactoryOrder API | Sprint 18 | Endpoints backend |
| Frontend expediente extendido | Sprint 19 | Después de endpoints |
| Emails/notificaciones | Sprint 20 | CEO-28 pendiente |
| Capa comercial (pricelists, rebates) | Sprint 22-23 | CEO-25 pendiente |
| Autogestión B2B | Sprint 24 | CEO-26 pendiente |
| Permisos granulares | Sprint 26 | Diferido por CEO |

---

## Criterio Sprint 17 DONE

### Obligatorio (bloquea Sprint 18)
1. Flujo completo REGISTRO→...→DESPACHO→TRANSITO→...→CERRADO funcional
2. REOPEN conectado al dispatcher y funcional
3. Portal 3 endpoints con tenant isolation estricta (6 tests de seguridad verdes)
4. 3 modelos nuevos (ExpedienteProductLine, FactoryOrder, ExpedientePago) creados con migración aplicada
5. Campos operativos (~30) en Expediente agregados con help_text por estado
6. payment_grace_days en ClientSubsidiary
7. C22 integrado en dispatcher central (no aislado)
8. handle_c1 firma coherente con dispatcher
9. 0 páginas frontend duplicadas
10. Tests existentes verdes + tests nuevos verdes
11. CI verde: `python manage.py test && bandit -ll backend/ && npm run lint && npm run typecheck`

---

## Impacto en seguridad

| Cambio | Impacto | Mitigación |
|--------|---------|------------|
| Endpoints portal (S17-04) | Amplía superficie — acceso B2B a datos | ClientScopedManager obligatorio, 404 uniforme, CEO-ONLY excluido, 6 tests seguridad |
| Modelos nuevos (S17-09/10/11) | Datos financieros (precios, pagos) | Mismo tier de visibilidad que Expediente padre |
| master_expediente FK (S17-08) | Relación entre expedientes | select_for_update en merge (Sprint 18) |

Ref: ENT_PLAT_SEGURIDAD — sin ampliación de superficie de ataque más allá de los 3 endpoints portal (ya diseñados en Sprint 14).

---

Stamp: DRAFT v1.3 — Arquitecto (Claude Opus 4.6) — 2026-03-25 — Auditoría ChatGPT R3: 9.6/10 APROBADO
