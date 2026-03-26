# PROMPT_ANTIGRAVITY_SPRINT17 — Estabilización + Modelo de Datos
## Para: Claude Code (Antigravity) — AG-02 Backend
## Sprint: 17 · Lote: v1.3 (auditoría R3 9.6/10) · Fecha: 2026-03-26

---

## TU ROL

Eres AG-02 Backend Builder para el proyecto MWT.ONE.
Implementas los items de Sprint 17 en código Python/Django.
El CEO (Alejandro) te da contexto y aprueba. Vos escribís código, no tomás decisiones de negocio.

Sprint 17 tiene 2 fases: Fase 0 (bugs) y Fase 1 (modelo de datos). NO avanzar a Fase 1 hasta que Fase 0 esté DONE con tests verdes.

---

## CONTEXTO DEL PROYECTO

- **Stack:** Django 5.x + DRF + PostgreSQL 16 + Celery + Redis + MinIO + Docker Compose + Next.js 14 (App Router)
- **Repo:** `Ale241302/mwt_one`, branch `main`
- **Objetivo:** Estabilizar bugs de state machine + extender modelo Expediente con campos operativos, product lines, órdenes de fábrica y pagos
- **Prerequisito:** Sprints 0-16 DONE. Verificar que tests pasan antes de empezar.

### Estado real del código post-Sprint 16 (verificar antes de empezar):
- `CreditPolicy` + `CreditExposure` → `apps/agreements/models.py` (SSOT crédito)
- `CreditOverride` → `apps/agreements/models.py` (override CEO)
- Commands C1-C16 con lógica real → `apps/expedientes/services/commands/`
- `c_cancel.py` + `c_reopen.py` → ya implementados con credit release
- `ClientSubsidiary` → `apps/clientes/models.py` con legal_name, tax_id
- ProductMaster → `apps/productos/models.py` con 565 SKUs
- Knowledge fix → `/ask/` retorna 200 en vacío

---

## HARD RULES — NUNCA VIOLAR

1. **ENT_OPS_STATE_MACHINE es FROZEN.** Los 8 estados canónicos son: REGISTRO, PRODUCCION, PREPARACION, DESPACHO, TRANSITO, EN_DESTINO, CERRADO, CANCELADO. No inventar estados. No modificar transiciones en la spec. Los cambios se implementan alineando el CÓDIGO con la spec.

2. **No inventar datos.** Si necesitas un valor de negocio (crédito, pricing, tasas), preguntá al CEO. Nunca hardcodear un número inventado. Marcar como `# TODO: CEO_INPUT_REQUIRED` y seguir.

3. **No romper commands existentes.** Los commands implementados (C1-C16, C22, c_cancel, c_reopen, ceo-override) deben seguir funcionando exactamente igual. Mismos inputs → mismos outputs. Si un test existente falla, tu código tiene un bug.

4. **Migraciones additive only.** Solo agregar campos (nullable o con default). Nunca ALTER destructivo, rename, ni DROP. Una sola migración consolidada al final de Fase 1.

5. **No eliminar ni renombrar campos existentes** del modelo Expediente ni de ningún otro modelo.

6. **No tocar infra.** `docker-compose.yml`, `nginx/`, settings de infra = prohibido.

7. **Tests antes y después.** Correr test suite completa antes de empezar. Después de cada fase, los mismos tests deben pasar. Tests nuevos en archivos separados.

8. **Conventional Commits.** `feat:`, `fix:`, `refactor:`, `test:`. Nunca commits genéricos.

---

## ANTES DE ESCRIBIR UNA SOLA LÍNEA — VERIFICACIÓN OBLIGATORIA

Sprint 13-16 agregaron bastante. Correr estos checks:

```bash
# 1. Campos actuales del modelo Expediente
grep -n "Field\|CharField\|IntegerField\|DecimalField\|DateField\|URLField\|ForeignKey\|ManyToMany" backend/apps/expedientes/models.py | head -80

# 2. ¿Existe reopen_count?
grep -rn "reopen_count" backend/apps/expedientes/

# 3. ¿Existe c_reopen en el dispatcher?
grep -rn "reopen\|REOPEN" backend/apps/expedientes/services/

# 4. ¿Qué commands están registrados?
cat backend/apps/expedientes/services/constants.py | head -100

# 5. ¿Existe CreditPolicy?
grep -rn "CreditPolicy" backend/apps/agreements/models.py

# 6. ¿Existe CreditExposure?
grep -rn "CreditExposure\|credit_exposure\|check_and_reserve" backend/apps/

# 7. ¿Qué modelos existen en expedientes?
grep "^class " backend/apps/expedientes/models.py

# 8. ¿ProductMaster existe?
grep -rn "class ProductMaster" backend/apps/productos/models.py

# 9. ¿ClientSubsidiary tiene payment_grace_days?
grep -rn "payment_grace_days" backend/apps/clientes/models.py

# 10. Tests actuales pasan?
pytest backend/ -v --tb=short 2>&1 | tail -20
```

**Si un campo o modelo que este prompt dice crear ya existe → NO crearlo de nuevo. Solo extender si falta algo.**

---

## FASE 0 — BUGS CRÍTICOS (hacer primero)

### Item 0.1 — Fix command_preparacion_despacho: debe transicionar a DESPACHO

**Problema:** DESPACHO es inalcanzable — el command que transiciona desde PREPARACION salta a TRANSITO.

**Nota de compatibilidad numérica:** La state machine FROZEN numera C10=ApproveDispatch→DESPACHO y C11=ConfirmShipmentDeparted→TRANSITO. Sprint 16 renumeró. El código real puede usar cualquier número. Este prompt usa nombres funcionales. Determiná el número real con grep antes de actuar.

```bash
grep -A5 "PREPARACION\|DESPACHO\|TRANSITO" backend/apps/expedientes/services/constants.py
```

**Solución:** Encontrar el command cuyo `requires_status` incluye PREPARACION y cambiar su `transitions_to` a `DESPACHO`.

**Regla de tests:** Tests existentes no se modifican, salvo los que codificaron la transición incorrecta heredada; cualquier cambio se limita a esa corrección.

**Test:** Crear expediente → avanzar hasta PREPARACION → ejecutar el command → verificar status=DESPACHO (no TRANSITO).

### Item 0.2 — Asegurar command_despacho_transito: DESPACHO → TRANSITO

**Verificar primero:**
```bash
grep -B2 -A5 "TRANSITO" backend/apps/expedientes/services/constants.py
```

**Caso A — ya existe command DESPACHO→TRANSITO:**
No crear nada. Verificar que funciona, que está en HANDLERS y URLs, y que el frontend muestra DESPACHO en acordeón y gate. Testear flujo completo.

**Caso B — no existe command DESPACHO→TRANSITO:**
Crear uno nuevo "Confirmar Salida":

```python
# En constants.py, agregar al COMMAND_SPEC:
"CONFIRM_DEPARTURE": {  # o el número que corresponda en la secuencia
    "name": "Confirmar Salida",
    "requires_status": ["DESPACHO"],
    "transitions_to": "TRANSITO",
    "creates_artifact": None,
    "requires_ceo": False,
}
```

Crear handler en `backend/apps/expedientes/services/commands_despacho.py`.
Registrar en `__init__.py` HANDLERS dict y en `urls.py`.

Actualizar frontend (ambos casos):
- `ExpedienteAccordion.tsx` — agregar DESPACHO al mapping de estados
- `GateMessage.tsx` — agregar gate para DESPACHO

**Test:** flujo completo PREPARACION→DESPACHO→TRANSITO.

### Item 0.3 — Verificar REOPEN en dispatcher

**NO reimplementar.** `c_reopen.py` ya existe (Sprint 16).

Verificar:
1. ¿REOPEN en COMMAND_SPEC? Si no → agregar con `requires_status: ["CANCELADO"]`, `transitions_to: "REGISTRO"`, `requires_ceo: True`
2. ¿URL registrada? Si no → agregar
3. ¿En HANDLERS dict? Si no → agregar apuntando a `c_reopen.handle_reopen`

**NO tocar `c_reopen.py` — ya tiene: constraint max 1, solo CEO, re-evaluación crédito.**

### Item 0.4 — Auditar, endurecer y completar endpoints Portal

Sprints 14-16 diseñaron endpoints de portal B2B. **Verificar primero qué existe:**

```bash
grep -rn "portal" backend/apps/expedientes/urls*.py
grep -rn "portal" backend/apps/*/urls*.py
grep -rn "Portal\|portal" backend/apps/expedientes/views*.py
```

**Si existen**: endurecer (verificar tenant isolation, 404 uniforme, CEO-ONLY excluido).
**Si no existen**: crear. 3 GETs con tenant isolation:

```python
# views_portal.py (crear archivo nuevo)

class PortalExpedienteListView(ListAPIView):
    """Listado de expedientes del cliente autenticado."""
    serializer_class = PortalExpedienteListSerializer
    
    def get_queryset(self):
        # ClientScopedManager: NUNCA .all()
        return Expediente.objects.for_user(self.request.user)


class PortalExpedienteDetailView(RetrieveAPIView):
    """Detalle simplificado — sin datos CEO-ONLY."""
    serializer_class = PortalExpedienteBundleSerializer
    
    def get_queryset(self):
        return Expediente.objects.for_user(self.request.user)
    # Si no encuentra: 404 automático de DRF. Mismo 404 para inexistente y ajeno.


class PortalExpedienteArtifactsView(ListAPIView):
    """Artifacts visibles para el cliente."""
    serializer_class = PortalArtifactSerializer
    
    def get_queryset(self):
        expediente = get_object_or_404(
            Expediente.objects.for_user(self.request.user),
            pk=self.kwargs['pk']
        )
        return expediente.artifacts.filter(visibility__in=['PUBLIC', 'PARTNER_B2B'])
```

**Serializer portal:** Crear `serializers_portal.py`. Excluir campos CEO-ONLY: `fob_unit`, `margin_pct`, `commission_pct`, `landed_cost`, `dai_amount`. **Regla genérica adicional:** excluir cualquier campo cuyo nombre empiece con `internal_` o `ceo_` del serializer portal.

```python
# serializers_portal.py
CEO_ONLY_FIELDS = {'fob_unit', 'margin_pct', 'commission_pct', 'landed_cost', 'dai_amount'}
CEO_ONLY_PREFIXES = ('internal_', 'ceo_')

class PortalExpedienteBundleSerializer(ModelSerializer):
    class Meta:
        model = Expediente
        exclude = [...]  # Construir dinámicamente o listar explícitamente
    
    def get_fields(self):
        fields = super().get_fields()
        return {
            k: v for k, v in fields.items()
            if k not in CEO_ONLY_FIELDS
            and not any(k.startswith(p) for p in CEO_ONLY_PREFIXES)
        }
```

URLs:
```python
# urls.py (agregar)
path('api/portal/expedientes/', PortalExpedienteListView.as_view()),
path('api/portal/expedientes/<uuid:pk>/', PortalExpedienteDetailView.as_view()),
path('api/portal/expedientes/<uuid:pk>/artifacts/', PortalExpedienteArtifactsView.as_view()),
```

### Item 0.5 — Fix firma handle_c1

En `create.py`, cambiar `handle_c1(user, payload)` a `handle_c1(payload, user)` — consistente con el dispatcher.

### Item 0.6 — Eliminar páginas duplicadas

```bash
rm -rf frontend/src/app/[lang]/dashboard/expedientes/
```

Dejar solo `frontend/src/app/[lang]/(mwt)/(dashboard)/expedientes/`.

### Item 0.7 — Integrar C22 al dispatcher

Mover lógica de `backend/expedientes/domain/c22_issue_commission_invoice.py` a `backend/apps/expedientes/services/commands_destino.py`.

Registrar C22 en COMMAND_SPEC, HANDLERS dict, y URLs.

Eliminar módulo aislado después de verificar.

### GATE FASE 0

```
[ ] command_preparacion_despacho: PREPARACION → DESPACHO funcional
[ ] command_despacho_transito: DESPACHO → TRANSITO funcional (existente verificado o nuevo creado)
[ ] REOPEN: en COMMAND_SPEC + URL + HANDLERS
[ ] Portal: 3 endpoints, tenant isolation, 404 uniforme, CEO-ONLY excluido (incluye prefijos internal_/ceo_), artifacts filtrados PARTNER_B2B
[ ] handle_c1: firma (payload, user)
[ ] Páginas duplicadas eliminadas
[ ] C22 en dispatcher
[ ] Tests existentes no se modifican, salvo los que codificaron transición incorrecta heredada
[ ] Test nuevo: PREPARACION→DESPACHO→TRANSITO
```

**⛔ NO avanzar a Fase 1 hasta que TODOS pasen.**

---

## FASE 1 — MODELO DE DATOS EXTENDIDO

Una sola migración al final. Todos los campos `null=True, blank=True` salvo que se indique.

### Item 1.1 — Campos operativos en Expediente

Agregar al modelo `Expediente` en `models.py`. **Verificar antes si existe** — Sprint 13-16 pueden haber creado alguno.

```python
# === GENERALES ===
purchase_order_number = CharField(max_length=100, null=True, blank=True,
    help_text="Número de orden de compra del cliente")
operado_por = CharField(max_length=20, null=True, blank=True,
    choices=[('CLIENTE', 'Cliente'), ('MWT', 'Muito Work Limitada')],
    help_text="Quién opera este expediente: el cliente o MWT")
url_orden_compra = URLField(max_length=500, null=True, blank=True)

# === REGISTRO ===
ref_number = CharField(max_length=100, null=True, blank=True,
    help_text="Número de referencia del cliente")
credit_days_client = IntegerField(null=True, blank=True,
    help_text="Días de crédito aprobados para el cliente")
credit_days_mwt = IntegerField(null=True, blank=True,
    help_text="Días de crédito aprobados para MWT")
credit_limit_client = DecimalField(max_digits=12, decimal_places=2, null=True, blank=True,
    help_text="Snapshot de CreditPolicy al crear expediente (DEC-EXP-03). Recalcula con pagos.")
credit_limit_mwt = DecimalField(max_digits=12, decimal_places=2, null=True, blank=True,
    help_text="Snapshot de CreditPolicy al crear expediente (DEC-EXP-03). Recalcula con pagos.")
order_value = DecimalField(max_digits=12, decimal_places=2, null=True, blank=True,
    help_text="Valor total del pedido")

# === PRODUCCION ===
factory_order_number = CharField(max_length=100, null=True, blank=True,
    help_text="Número de orden principal del fabricante. Campo flat para queries rápidas. Detalle en FactoryOrder.")
proforma_client_number = CharField(max_length=100, null=True, blank=True)
proforma_mwt_number = CharField(max_length=100, null=True, blank=True)
fabrication_start_date = DateField(null=True, blank=True)
fabrication_end_date = DateField(null=True, blank=True)
url_proforma_cliente = URLField(max_length=500, null=True, blank=True)
url_proforma_muito_work = URLField(max_length=500, null=True, blank=True)
master_expediente = ForeignKey('self', null=True, blank=True, on_delete=SET_NULL,
    related_name='merged_followers',
    help_text="Si este expediente fue fusionado, apunta al master (DEC-EXP-02)")

# === PREPARACION ===
shipping_method = CharField(max_length=100, null=True, blank=True)
incoterms = CharField(max_length=20, null=True, blank=True)
cargo_manager = CharField(max_length=20, null=True, blank=True,
    choices=[('CLIENTE', 'Cliente'), ('FABRICA', 'Fábrica')])
shipping_value = DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
payment_mode_shipping = CharField(max_length=20, null=True, blank=True,
    choices=[('PREPAGO', 'Prepago'), ('CONTRAENTREGA', 'Contraentrega')])
url_list_empaque = URLField(max_length=500, null=True, blank=True)
url_cotizacion_envio = URLField(max_length=500, null=True, blank=True)

# === DESPACHO ===
airline_or_shipping_company = CharField(max_length=200, null=True, blank=True)
awb_bl_number = CharField(max_length=100, null=True, blank=True,
    help_text="Air Waybill o Bill of Lading number")
origin_location = CharField(max_length=200, null=True, blank=True)
arrival_location = CharField(max_length=200, null=True, blank=True)
shipment_date = DateField(null=True, blank=True)
payment_date_dispatch = DateField(null=True, blank=True)
invoice_client_number = CharField(max_length=100, null=True, blank=True)
invoice_mwt_number = CharField(max_length=100, null=True, blank=True)
dispatch_additional_info = TextField(null=True, blank=True)
url_certificado_origen = URLField(max_length=500, null=True, blank=True)
url_factura_cliente = URLField(max_length=500, null=True, blank=True)
url_factura_muito_work = URLField(max_length=500, null=True, blank=True)
url_awb_bl = URLField(max_length=500, null=True, blank=True)
tracking_url = URLField(max_length=500, null=True, blank=True,
    help_text="URL de rastreo del envío (DHL, FedEx, naviera). Link clicable en frontend.")

# === TRANSITO ===
intermediate_airport_or_port = CharField(max_length=200, null=True, blank=True)
transit_arrival_date = DateField(null=True, blank=True)
url_packing_list_detallado = URLField(max_length=500, null=True, blank=True)

# === REOPEN (verificar si Sprint 16 ya lo creó) ===
# reopen_count = IntegerField(default=0)  # SOLO agregar si NO existe
```

### Item 1.2 — Modelo ExpedienteProductLine

```python
class ExpedienteProductLine(models.Model):
    """
    Línea de producto en un expediente (= línea de venta).
    Referencia ProductMaster (DEC-EXP-04). Precio editable con trazabilidad.
    """
    id = UUIDField(primary_key=True, default=uuid4, editable=False)
    expediente = ForeignKey('Expediente', on_delete=CASCADE, related_name='product_lines')
    product = ForeignKey(
        'productos.ProductMaster', on_delete=PROTECT,
        related_name='expediente_lines',
        help_text="SKU del catálogo. Incluye talla como variante."
    )
    quantity = PositiveIntegerField()
    unit_price = DecimalField(max_digits=12, decimal_places=2,
        help_text="Precio unitario aplicado. Editable por expediente.")
    price_source = CharField(max_length=30, default='manual', choices=[
        ('pricelist', 'Lista de precios activa'),
        ('manual', 'Ingresado manualmente'),
        ('override', 'Override por expediente'),
    ])
    
    # Modificaciones post-creación
    quantity_modified = PositiveIntegerField(null=True, blank=True)
    unit_price_modified = DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    modification_reason = CharField(max_length=200, null=True, blank=True)
    
    # Separación
    separated_to_expediente = ForeignKey(
        'Expediente', null=True, blank=True,
        on_delete=SET_NULL, related_name='received_lines'
    )
    
    # Vínculo a orden de fábrica
    factory_order = ForeignKey(
        'FactoryOrder', null=True, blank=True,
        on_delete=SET_NULL, related_name='product_lines'
    )
    
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['created_at']
    
    def __str__(self):
        return f"{self.expediente_id} - {self.product} x{self.quantity}"
```

### Item 1.3 — Modelo FactoryOrder

```python
class FactoryOrder(models.Model):
    """
    Orden en el sistema del fabricante (DEC-EXP-01).
    Para Marluvas = SAP. Para otro fabricante = su sistema. Genérico.
    """
    id = UUIDField(primary_key=True, default=uuid4, editable=False)
    expediente = ForeignKey('Expediente', on_delete=CASCADE, related_name='factory_orders')
    order_number = CharField(max_length=100,
        help_text="Número en el sistema del fabricante")
    proforma_client_number = CharField(max_length=100, null=True, blank=True)
    proforma_mwt_number = CharField(max_length=100, null=True, blank=True)
    purchase_number = CharField(max_length=100, null=True, blank=True,
        help_text="Referencia de compra asociada")
    url_proforma_client = URLField(max_length=500, null=True, blank=True)
    url_proforma_mwt = URLField(max_length=500, null=True, blank=True)
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['created_at']
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Al crear el primer FactoryOrder, copiar order_number al campo flat
        # Depende de: factory_order_number en Expediente (Item 1.1)
        if not self.expediente.factory_order_number:
            self.expediente.factory_order_number = self.order_number
            self.expediente.save(update_fields=['factory_order_number'])
    
    def __str__(self):
        return f"FO-{self.order_number} ({self.expediente_id})"
```

### Item 1.4 — Modelo ExpedientePago

```python
class ExpedientePago(models.Model):
    """
    Registro operativo de pagos MWT.
    Coexiste con PaymentLine (C21 ledger).
    CONTRATO: la integración con PaymentLine se hace en la VIEW, no en save().
    """
    TIPO_PAGO = [('COMPLETO', 'Completo'), ('PARCIAL', 'Pago Parcial')]
    METODO_PAGO = [
        ('TRANSFERENCIA', 'Transferencia Bancaria'),
        ('NOTA_CREDITO', 'Nota de Crédito'),
    ]
    
    id = UUIDField(primary_key=True, default=uuid4, editable=False)
    expediente = ForeignKey('Expediente', on_delete=CASCADE, related_name='pagos')
    tipo_pago = CharField(max_length=20, choices=TIPO_PAGO)
    metodo_pago = CharField(max_length=30, choices=METODO_PAGO)
    payment_date = DateField()
    amount_paid = DecimalField(max_digits=12, decimal_places=2)
    additional_info = TextField(null=True, blank=True)
    url_comprobante = URLField(max_length=500, null=True, blank=True)
    created_at = DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-payment_date']
    
    def __str__(self):
        return f"Pago {self.tipo_pago} ${self.amount_paid} ({self.expediente_id})"
```

**Integración con PaymentLine (C21) — contrato fijado:**

El modelo `ExpedientePago` NO tiene lógica de integración en `save()`. NO usar signals.
La integración se hace en la **view que crea el pago**, dentro de `transaction.atomic()`:

```python
# En la view POST /api/expedientes/{id}/pagos/ (Sprint 18, pero el modelo se crea ahora):
with transaction.atomic():
    pago = ExpedientePago.objects.create(**validated_data)
    # Verificar si handle_c21 acepta amount + date:
    # Si sí → llamar handle_c21 para crear PaymentLine
    # Si no → crear PaymentLine directamente + EventLog
    recalculate_expediente_credit(expediente)
```

**Verificación previa:**
```bash
grep -n "def handle_c21\|def register_payment" backend/apps/expedientes/services/
```

### Item 1.5 — payment_grace_days en ClientSubsidiary

En `apps/clientes/models.py`:
```python
# Agregar a ClientSubsidiary:
payment_grace_days = IntegerField(
    default=15,
    help_text="Días de gracia post-vencimiento antes de email cobranza. Editable por CEO."
)
```

### Item 1.6 — Admin + migración

```python
# admin.py — agregar inlines
class ExpedienteProductLineInline(admin.TabularInline):
    model = ExpedienteProductLine
    extra = 0
    readonly_fields = ('created_at', 'updated_at')

class FactoryOrderInline(admin.TabularInline):
    model = FactoryOrder
    extra = 0
    readonly_fields = ('created_at', 'updated_at')

class ExpedientePagoInline(admin.TabularInline):
    model = ExpedientePago
    extra = 0
    readonly_fields = ('created_at',)

# Agregar a ExpedienteAdmin.inlines:
# inlines = [...existing..., ExpedienteProductLineInline, FactoryOrderInline, ExpedientePagoInline]
```

Generar migración:
```bash
python manage.py makemigrations expedientes clientes --name add_operational_fields_product_lines_factory_orders_pagos
python manage.py migrate
python manage.py check
```

### Item 1.7 — Tests

Crear archivos separados (no modificar tests existentes):

**`test_sprint17_transitions.py`:**
- Test PREPARACION→DESPACHO (command corregido)
- Test DESPACHO→TRANSITO (command existente o nuevo)
- Test flujo completo 8 estados
- Test REOPEN: CANCELADO→REGISTRO
- Test REOPEN bloqueado si reopen_count >= 1

**`test_sprint17_portal.py`:**
- Test cross-tenant detalle: cliente A GET /portal/expedientes/{id_B}/ → 404
- Test cross-tenant artifacts: cliente A GET /portal/expedientes/{id_B}/artifacts/ → 404
- Test 404 uniforme: inexistente = ajeno (mismo body)
- Test listado scoped: GET /portal/expedientes/ retorna SOLO expedientes del tenant
- Test CEO-ONLY no expuesto en response (incluye verificar que campos con prefijo `internal_`/`ceo_` están ausentes)
- Test artifacts visibility: solo PUBLIC y PARTNER_B2B

**`test_sprint17_models.py`:**
- Test crear ExpedienteProductLine con FK ProductMaster
- Test FactoryOrder: primer order copia number al campo flat `factory_order_number` (via save())
- Test ExpedientePago: campos requeridos validados
- Test payment_grace_days default=15

---

## CHECKLIST FINAL

```
FASE 0:
[ ] command_preparacion_despacho → DESPACHO funcional
[ ] command_despacho_transito → TRANSITO funcional (Caso A o B)
[ ] REOPEN: dispatcher conectado
[ ] Portal: 3 endpoints + tenant isolation + 404 uniforme + CEO-ONLY excluido (campos explícitos + prefijos internal_/ceo_) + artifacts filtrados
[ ] handle_c1: firma (payload, user)
[ ] Páginas duplicadas eliminadas
[ ] C22 en dispatcher
[ ] Tests existentes verdes

FASE 1:
[ ] ~30 campos operativos en Expediente (con help_text por estado)
[ ] ExpedienteProductLine con FK ProductMaster
[ ] FactoryOrder relacional (sync vía save() al campo factory_order_number, no signals)
[ ] ExpedientePago (integración C21 vía view+atomic, no save/signals)
[ ] payment_grace_days en ClientSubsidiary
[ ] 1 migración consolidada aplicada
[ ] Admin con inlines
[ ] Tests nuevos verdes
[ ] Tests existentes verdes

CI (DONE obligatorio — bloquea cierre de sprint):
[ ] python manage.py test
[ ] bandit -ll backend/
[ ] npm run lint && npm run typecheck
[ ] Conventional commits
```

---

## PREGUNTAS CEO (solo si algo no está claro después de verificar el código)

1. Si `reopen_count` ya existe con nombre diferente → confirmar cuál es el canónico.
2. Si `handle_c21` ya acepta los campos de ExpedientePago → confirmar si ExpedientePago es wrapper o complemento.
3. Si algún campo de DESPACHO ya existe desde Sprint 13-16 → confirmar si extender o usar el existente.

---

## MIGRATION PLAN

```bash
# 1. Estado limpio
python manage.py showmigrations expedientes clientes

# 2. Generar (UNA sola)
python manage.py makemigrations expedientes clientes \
  --name add_operational_fields_product_lines_factory_orders_pagos

# 3. Verificar additive only (solo AddField, CreateModel)
python manage.py sqlmigrate expedientes XXXX

# 4. Aplicar
python manage.py migrate

# 5. Verificar
python manage.py check
python manage.py test
```

**Rollback:** RemoveField + DeleteModel para revertir. Todos los campos nullable o con default.
