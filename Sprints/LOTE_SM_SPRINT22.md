# LOTE_SM_SPRINT22 — Capa Comercial: Pricing Engine + Pricelists + Asignaciones
id: LOTE_SM_SPRINT22
version: 1.6
visibility: [INTERNAL]
domain: Plataforma (IDX_PLATAFORMA)
status: DRAFT — Aprobado auditoría R5 9.6/10
stamp: DRAFT v1.6 — 2026-04-01
tipo: Lote ruteado (ref → PLB_ORCHESTRATOR §E)
sprint: 22
priority: P0 (camino crítico → bloquea S23, S24)
depends_on: LOTE_SM_SPRINT21 (DRAFT — monitor actividad),
            LOTE_SM_SPRINT18 (DONE — motor dimensional)
refs: ENT_OPS_STATE_MACHINE (FROZEN v1.2.2),
      ENT_COMERCIAL_PRICING (DRAFT — price ladder actual),
      ENT_COMERCIAL_COSTOS (DRAFT — estructura costos),
      LOTE_SM_SPRINT14 (DONE — agreements layer, resolve_client_price v1),
      LOTE_SM_SPRINT20 (DONE — proformas + ArtifactPolicy),
      ROADMAP_EXTENDIDO_POST_DIRECTRIZ (VIGENTE — numeración definitiva)

changelog:
  - v1.0 (2026-04-01): Compilación inicial. 18 items en 4 fases. CEO-25 resuelto en sesión de diseño 2026-04-01: 6 decisiones cerradas (D1-permanente CPA, D2-N pricelists activas con extinción, D3-pronto pago como policy por cliente, D3b-rebate anual/trimestral, D4-MOQ como grade con multiplicadores por talla, D5-alerta margen delegada a arquitecto configurable). Fuente: ROADMAP_EXTENDIDO S22 + datos reales de tablas Marluvas (pricelists COMEX con grades y multiplicadores).
  - v1.1 (2026-04-01): Integración con consolas existentes. Brand Console: Tab 5 Pricing refactored (no tab nuevo), Tab 4 Catalog enriched con precio+MOQ+Grade. Client Console: Tab Catalog enriquecido con precio post-descuento. Items renumerados: S22-13 a S22-20 (antes S22-13 a S22-18). Total: 20 items en 4 fases. +2 tests backend (portal security), +4 checks FE manuales. 9 notas de auditoría (antes 7).
  - v1.2 (2026-04-01): Fixes auditoría R1 (ChatGPT 8.8/10 — 4 bloqueantes + 3 mayores). B1: skip_cache param en resolve_client_price(), recálculo Celery SIEMPRE pasa skip_cache=True. B2: C5 reescrita con dos serializers separados (Internal vs Portal), contrato de response explícito por tier. B3: lógica de extinción reescrita — regla única por versión completa, eliminada toda referencia a "desactivar por SKU". B4: pseudocódigo waterfall con Paso 2A (GradeItem) + Paso 2B (PriceListItem S14 fallback explícito), source distingue 'pricelist_grade' vs 'pricelist_legacy'. M1: MOQ siempre del winning_item (misma versión que precio). M2: EarlyPaymentPolicy declarada como excepción explícita a S14-C5 con audit trail via ConfigChangeLog. M3: file_url→storage_key, signed URLs generadas al leer. Tests: 36→41. Notas auditoría: 9→11.
  - v1.3 (2026-04-01): Fixes auditoría R2 (ChatGPT 9.4/10 — 0 bloqueantes, 2 mayores, 2 menores). R2-M1: resolve_client_price() ahora retorna size_multipliers del winning_item en el dict; validate_moq() usa ese campo directamente sin reconsultar DB. R2-M2: fallback legacy Paso 2B corregido — eliminado is_active (no existe en S14 PriceListItem), vigencia solo por valid_from/valid_to. R2-m1: DEC-S22-02 reescrito con regla real de extinción por versión completa. R2-m2: copy modal activación corregido para describir regla real de evaluación.
  - v1.4 (2026-04-01): Fixes auditoría R3 (ChatGPT 9.4/10 — 1 mayor, 2 menores). R3-M1: grade constraints desacoplados de fuente de precio — nuevo helper _resolve_grade_constraints() se invoca siempre que size_multipliers=None (CPA, BCPA, legacy). MOQ funciona independientemente del camino de precio. R3-m1: C5 actualizado para incluir size_multipliers en contrato interno. R3-m2: S22-05 actualizado con size_multipliers en dict enriquecido. Tests: 41→44 (+3 para CPA+Grade, BCPA+Grade, legacy sin Grade).
  - v1.5 (2026-04-01): Fixes auditoría R4 (ChatGPT 9.4/10 — 1 mayor, 1 menor). R4-M1: S22-07 reescrito con regla MOQ desacoplada real — eliminado "precio y MOQ siempre de la misma versión". Nota 3 reescrita: explica desacople, distingue pricelist_version (precio) de grade_pricelist_version (MOQ). R4-m1: nuevo campo grade_pricelist_version en return dict, helper, y Paso 2A. C5 contrato interno actualizado con ambos campos y semántica explícita.
  - v1.6 (2026-04-01): Fixes menores R5 (ChatGPT 9.6/10 — APROBADO). m1: test 42 extendido para verificar que grade_pricelist_version no se filtra al portal. m2: S22-05 punto 4 actualizado con grade_pricelist_version en dict enriquecido. Lote listo para ejecución.

---

## Contexto

Sprint 22 implementa la capa comercial que transforma la plataforma de "precios manuales" a "pricing engine con pricelists versionadas, descuentos por pronto pago, y assignments por cliente". Es el corazón de H8 ("el expediente ES la venta, no un tracker logístico").

**Cambio de paradigma en 3 frases:**
1. El precio de una línea de producto ya no se ingresa manualmente — se resuelve automáticamente desde pricelists versionadas + políticas de pronto pago + assignments por cliente.
2. Múltiples pricelists pueden coexistir activas para el mismo brand (período de gracia en subidas de precio); el sistema toma MIN(precio) para proteger al cliente.
3. Los multiplicadores por talla (MOQ Grade) de la pricelist de fábrica se modelan nativamente — no como un número plano sino como la estructura real que usa Marluvas.

**Estado post-Sprint 21 (asumido DONE):**
- EventLog extendido con user, proforma, action_source, previous/new status
- UserNotificationState con high-water mark
- Activity feed endpoints (GET feed + POST mark-seen + GET count)
- Role-based sidebar activada
- Badge en header con count

**Estado post-Sprint 14 (base de pricing existente):**
- `resolve_client_price()` en `backend/apps/pricing/services.py` con cascada: PriceList base → excepciones SKU → BCPA override
- `PriceListItem` con brand FK, product FK, price, valid_from/to
- `BrandClientPriceAgreement` (BCPA) para overrides por cliente
- 565 SKUs seedeados en ProductMaster
- Pricelist COMEX seedeada

**Lo que falta (scope de este sprint):**
- 0 ClientProductAssignment (paso 0 del waterfall — precio cached por cliente)
- 0 soporte para N pricelists activas simultáneamente con lógica de extinción
- 0 upload de pricelist CSV/Excel en Brand Console
- 0 descuento por pronto pago (EarlyPaymentPolicy)
- 0 MOQ como Grade con multiplicadores por talla (solo min_order_qty plano)
- 0 alerta automática de margen
- 0 bulk assignment por product_key
- 0 recálculo Celery al activar nueva pricelist
- Frontend pre-fill de precio en expediente/proforma = manual

---

## Decisiones ya resueltas (NO preguntar de nuevo)

| Decisión | Ref | Detalle |
|----------|-----|---------|
| Proforma como unidad operativa | DIRECTRIZ / S20 | mode B o C a nivel proforma, no expediente. |
| ArtifactPolicy como constante Python | SG-01 / S20 | Migra a DB en S23. |
| EPL FK a ProductMaster (no texto libre) | DEC-EXP-04 / S17 | unit_price editable con price_source. |
| BCPA es SSOT de overrides | S14-C4 | No duplicar en Brand.pricing ni en otro sitio. |
| Versionado de config inmutable | S14-C5 | Nuevo cambio = nueva versión. |

## Decisiones nuevas Sprint 22 (CEO-25 — sesión 2026-04-01)

| ID | Decisión | Detalle |
|----|----------|---------|
| DEC-S22-01 | ClientProductAssignment permanente | `is_active` toggle. Sin `valid_from/valid_to` en MVP. Vigencia temporal en v2. |
| DEC-S22-02 | N pricelists activas simultáneamente | Resolución: `MIN(precio)` de todas las activas para ese SKU. Extinción por versión completa: una versión previa se extingue solo si, para TODOS los SKUs solapados, la nueva versión tiene precio ≤. Si al menos 1 SKU solapado donde la anterior es más barata → la anterior permanece activa (MIN protege al cliente en runtime). CEO puede forzar extinción manual. |
| DEC-S22-03 | Pronto pago = policy por cliente | No es descuento global por brand. Modelo `EarlyPaymentPolicy`: cliente × plazo → % descuento sobre precio de lista. Base = 90d + 10% comisión. Escala real Marluvas: 60d→-1%, 30d→-1.75%, 8d→-2.75%. Es un artefacto ligado al cliente, complementario al pricing. |
| DEC-S22-04 | Rebate = plan anual, cumplimiento trimestral | Otro artefacto separado. Diseño en S23. Solo se modela la referencia en S22. |
| DEC-S22-05 | MOQ = Grade con multiplicadores por talla | La pricelist define por referencia: Grade (rango tallas, ej "35 ao 45"), y multiplicadores por talla (ej: 37=5, 38=5, 39=10, 40=10...). Tallas fuera del Grade = no disponible. MOQ = sum(multiplicadores). No es un número plano. |
| DEC-S22-06 | Alerta de margen configurable por brand | Sin threshold fijo. Campo `min_margin_alert_pct` en Brand. Default [PENDIENTE — NO INVENTAR]. CEO define cuando esté listo. Mecanismo activo solo si el campo tiene valor. |

---

## Convenciones Sprint 22

### C1. State machine FROZEN
No se modifican estados, transiciones ni commands. El pricing engine se conecta al flujo existente vía `resolve_client_price()` que ya se llama desde ExpedienteProductLine.

### C2. Backwards compat con pricing S14
`resolve_client_price()` ya existe en `backend/apps/pricing/services.py`. S22 lo extiende — no lo reescribe. El waterfall actual (PriceList → BCPA) se mantiene; se agregan pasos nuevos al inicio y al final.

### C3. BCPA sigue como SSOT de overrides
`BrandClientPriceAgreement` sigue siendo el ÚNICO lugar para overrides negociados de precio. CPA es un cache de resolución, no un override.

### C4. Inmutabilidad de snapshots
Precio en proforma ya creada NUNCA se recalcula. Si cambia la pricelist, solo afecta futuras resoluciones. `ExpedienteProductLine.unit_price` es snapshot al momento de creación.

### C5. Pricing response contracts por tier de visibilidad (fix B2)

resolve_client_price() retorna siempre el dict completo internamente. La visibilidad del response depende del caller:

**Endpoint interno (CEO/AGENT_*):** Serializer completo. Retorna:
- `price`, `source`, `pricelist_version`, `discount_applied`, `base_price`, `grade_moq`, `size_multipliers`, `grade_pricelist_version`
- `pricelist_version` = fuente del precio. `grade_pricelist_version` = fuente del MOQ/size_multipliers. Pueden coincidir o diferir (fix R4-m1).
- `size_multipliers` es service-level data — solo se expone en el endpoint interno para tooltips y validación MOQ del frontend CEO. No sale por portal.
- Tooltip del frontend CEO muestra fuente + desglose completo (S22-13)
- NUNCA retorna margen — eso se calcula solo en S22-10 (alerta Celery, no en response)

**Endpoint portal (CLIENT_*):** Serializer restringido. Retorna SOLO:
- `price` (final, con descuento pronto pago ya aplicado)
- `moq` (grade_moq si existe)
- NUNCA retorna: `source`, `base_price`, `discount_applied`, `pricelist_version`

**Implementación:** Dos serializers separados (`PricingInternalSerializer` y `PricingPortalSerializer`). El view detecta el rol del user y selecciona serializer. No es un campo excluido — son clases distintas.

---

## Modelos de datos

### M1. ClientProductAssignment (nuevo)

```python
# backend/apps/pricing/models.py

class ClientProductAssignment(models.Model):
    """
    Asignación permanente de un producto a un cliente con precio cached.
    Paso 0 del waterfall de resolve_client_price().
    
    Permanente para MVP (DEC-S22-01): solo is_active toggle.
    Vigencia temporal (valid_from/valid_to) se agrega en v2 si se necesita.
    """
    client_subsidiary = models.ForeignKey(
        'clientes.ClientSubsidiary',
        on_delete=models.CASCADE,
        related_name='product_assignments'
    )
    brand_sku = models.ForeignKey(
        'productos.BrandSKU',
        on_delete=models.PROTECT,
        related_name='client_assignments'
    )
    
    # Precio cached — se recalcula cuando cambia la pricelist (Celery task S22-12)
    cached_client_price = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True,
        help_text="Precio resuelto para este cliente. NULL = no resuelto aún."
    )
    cached_base_price = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True,
        help_text="Precio base de pricelist usado para el cálculo."
    )
    cached_pricelist_version = models.ForeignKey(
        'pricing.PriceListVersion',
        on_delete=models.SET_NULL, null=True, blank=True,
        help_text="Versión de pricelist usada en el último cálculo."
    )
    cached_at = models.DateTimeField(null=True, blank=True)
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['client_subsidiary', 'brand_sku']
        indexes = [
            models.Index(fields=['client_subsidiary', 'is_active']),
            models.Index(fields=['brand_sku', 'is_active']),
        ]
```

### M2. PriceListVersion (refactor de PriceList existente)

```python
class PriceListVersion(models.Model):
    """
    Versión de pricelist por brand. N pueden estar activas simultáneamente (DEC-S22-02).
    
    Lógica de extinción (implementada en activate_pricelist service):
    - Precio baja en nueva versión → extinción inmediata de versiones anteriores para esos SKUs.
    - Precio sube → período de gracia (coexisten). MIN(precio) protege al cliente.
    - CEO puede forzar extinción manual de cualquier versión.
    """
    brand = models.ForeignKey(
        'brands.Brand',
        on_delete=models.CASCADE,
        related_name='pricelist_versions'
    )
    version_label = models.CharField(
        max_length=50,
        help_text="Ej: 'Light 2026v6', 'COMEX 2026v3'"
    )
    storage_key = models.CharField(
        max_length=500, null=True, blank=True,
        help_text="Object key en storage (ej: 'pricelists/marluvas/2026v6.xlsx'). "
                  "Signed URL se genera al leer (TTL 30min). NUNCA persistir URL firmada (fix M3)."
    )
    
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL, null=True,
        related_name='uploaded_pricelists'
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    is_active = models.BooleanField(default=False)
    activated_at = models.DateTimeField(null=True, blank=True)
    deactivated_at = models.DateTimeField(null=True, blank=True)
    deactivation_reason = models.CharField(
        max_length=50, null=True, blank=True,
        choices=[
            ('manual', 'Extinción manual CEO'),
            ('price_decrease', 'Nueva versión con precio menor'),
            ('superseded', 'Reemplazada por nueva versión'),
        ]
    )
    
    notes = models.TextField(blank=True, default='')
    
    class Meta:
        ordering = ['-uploaded_at']
        indexes = [
            models.Index(fields=['brand', 'is_active']),
        ]
```

### M3. PriceListGradeItem (nuevo — reemplaza PriceListItem para items con grade)

```python
class PriceListGradeItem(models.Model):
    """
    Item de pricelist con Grade (multiplicadores por talla).
    Refleja la estructura real de Marluvas: cada referencia tiene un rango
    de tallas (Grade) y multiplicadores por talla que definen MOQ.
    
    Ejemplo real:
    - Referencia 10VS48-A, Grade "35 ao 45"
    - Multiplicadores: {37: 5, 38: 5, 39: 10, 40: 10, 41: 10, 42: 10, 43: 10, 44: 10, "45/46": 10, "47/48": 5}
    - Precio: $7.46 (por par, aplica a todas las tallas del Grade)
    - MOQ = sum(multiplicadores) = 85 pares para esta referencia
    """
    pricelist_version = models.ForeignKey(
        PriceListVersion,
        on_delete=models.CASCADE,
        related_name='grade_items'
    )
    
    # Referencia del producto en la pricelist de fábrica
    reference_code = models.CharField(
        max_length=80,
        help_text="Código referencia fábrica. Ej: '10VS48-A', '100AWORK-CM-BR'"
    )
    brand_sku = models.ForeignKey(
        'productos.BrandSKU',
        on_delete=models.PROTECT,
        null=True, blank=True,
        help_text="Match a BrandSKU si existe. NULL si referencia no mapeada aún."
    )
    
    # Datos del producto (parseados del CSV de fábrica)
    description_upper = models.CharField(max_length=200, blank=True, default='')
    tip_type = models.CharField(max_length=50, blank=True, default='',
        help_text="Bico: ACO, PLASTICO, SEM BICO, COMPOSITE")
    insole_type = models.CharField(max_length=100, blank=True, default='',
        help_text="Palmilha de construção")
    ncm = models.CharField(max_length=20, blank=True, default='',
        help_text="NCM / HS Code")
    ca_number = models.CharField(max_length=20, blank=True, default='',
        help_text="Certificado Aprovação (Brasil)")
    factory_code = models.CharField(max_length=20, blank=True, default='',
        help_text="Código interno fábrica (ej: 701407)")
    factory_center = models.CharField(max_length=50, blank=True, default='',
        help_text="Centro de faturamento (ej: '1010 - OLIVEIRA')")
    
    # Precio unitario (por par, todas las tallas del Grade)
    unit_price_usd = models.DecimalField(max_digits=12, decimal_places=2)
    
    # Grade: rango de tallas y multiplicadores
    grade_label = models.CharField(
        max_length=20,
        help_text="Ej: '33 ao 48', '35 ao 45'"
    )
    size_multipliers = models.JSONField(
        help_text="Dict talla→multiplicador. Ej: {'37': 5, '38': 5, '39': 10, ...}. "
                  "Talla ausente = no disponible en esta referencia. "
                  "Valor = mínimo de pares por talla en un pedido."
    )
    
    class Meta:
        unique_together = ['pricelist_version', 'reference_code']
        indexes = [
            models.Index(fields=['pricelist_version', 'brand_sku']),
            models.Index(fields=['reference_code']),
        ]
    
    @property
    def moq_total(self):
        """MOQ total = sum de multiplicadores de todas las tallas."""
        return sum(self.size_multipliers.values())
    
    @property
    def available_sizes(self):
        """Lista de tallas disponibles en esta referencia."""
        return sorted(self.size_multipliers.keys())
```

### M4. EarlyPaymentPolicy (nuevo — DEC-S22-03)

```python
class EarlyPaymentPolicy(models.Model):
    """
    Política de descuento por pronto pago, ligada a un cliente específico (DEC-S22-03).
    
    EXCEPCIÓN EXPLÍCITA A S14-C5 (fix M2): EarlyPaymentPolicy es MUTABLE en MVP.
    Justificación: las condiciones de pronto pago se renegocian con frecuencia y
    no requieren auditoría histórica de cada cambio en MVP. Los precios ya snapshotados
    en proformas existentes NO se recalculan (POL_INMUTABILIDAD). Solo futuras
    resoluciones usan la policy vigente.
    Si se necesita trazabilidad histórica en v2: agregar policy_version + superseded_at.
    Cambios se registran en ConfigChangeLog (S14 audit app) vía signal post_save.
    
    No es un descuento global por brand — es una condición negociada por cliente.
    El precio base es a 90 días con 10% comisión. Los descuentos reducen 
    desde ese base según el plazo de pago.
    
    Ejemplo real Marluvas:
    - Base: 90 días, 10% comisión
    - 60 días: -1% sobre precio de lista
    - 30 días: -1.75%
    - 8 días: -2.75%
    
    El descuento se aplica DESPUÉS de resolver el precio base (waterfall paso 0-2).
    Precio final = base_price × (1 - discount_pct / 100)
    """
    client_subsidiary = models.ForeignKey(
        'clientes.ClientSubsidiary',
        on_delete=models.CASCADE,
        related_name='early_payment_policies'
    )
    brand = models.ForeignKey(
        'brands.Brand',
        on_delete=models.CASCADE,
        related_name='early_payment_policies'
    )
    
    # Condiciones base
    base_payment_days = models.PositiveIntegerField(
        default=90,
        help_text="Plazo base del precio de lista (días)."
    )
    base_commission_pct = models.DecimalField(
        max_digits=5, decimal_places=2, default=10.00,
        help_text="Comisión base incluida en precio de lista (%)."
    )
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['client_subsidiary', 'brand']


class EarlyPaymentTier(models.Model):
    """
    Tier individual de una EarlyPaymentPolicy.
    Cada tier define: si pagas en X días, obtenés Y% de descuento.
    """
    policy = models.ForeignKey(
        EarlyPaymentPolicy,
        on_delete=models.CASCADE,
        related_name='tiers'
    )
    payment_days = models.PositiveIntegerField(
        help_text="Plazo de pago en días (ej: 8, 30, 60)."
    )
    discount_pct = models.DecimalField(
        max_digits=5, decimal_places=2,
        help_text="Porcentaje de descuento sobre precio de lista (ej: 2.75 para -2.75%)."
    )
    
    class Meta:
        unique_together = ['policy', 'payment_days']
        ordering = ['payment_days']
```

### M5. Extensión de Brand (campo alerta margen — DEC-S22-06)

```python
# Agregar a Brand existente (AddField, no AlterField)
# backend/apps/brands/models.py

# Campo nuevo:
min_margin_alert_pct = models.DecimalField(
    max_digits=5, decimal_places=2, null=True, blank=True,
    help_text="Umbral mínimo de margen (%). Si un CPA cae debajo, alerta al CEO. "
              "NULL = alerta desactivada."
)
```

---

## Waterfall resolve_client_price() v2

```python
# backend/apps/pricing/services.py

def resolve_client_price(
    brand_sku,
    client_subsidiary,
    payment_days=None,  # NUEVO: para aplicar descuento pronto pago
    proforma_mode=None,  # NUEVO: Mode B/C puede resolver a pricelists distintas
    skip_cache=False,  # NUEVO (B1-fix): True cuando se llama desde recálculo Celery
):
    """
    Waterfall de resolución de precio. Retorna dict con:
    {
        'price': Decimal,
        'source': str,  # 'assignment' | 'agreement' | 'pricelist_grade' | 'pricelist_legacy' | 'manual'
        'pricelist_version': str | None,
        'discount_applied': Decimal | None,  # % descuento pronto pago
        'base_price': Decimal | None,  # precio antes de descuento
        'grade_moq': int | None,  # MOQ total del Grade si viene de pricelist grade
        'size_multipliers': dict | None,  # (fix R2-M1) multiplicadores por talla del winning_item
        'grade_pricelist_version': str | None,  # (fix R4-m1) versión del Grade que alimenta MOQ
    }
    
    Cascada:
    Paso 0: CPA — cached_client_price (SOLO si skip_cache=False). Recálculo Celery
            SIEMPRE pasa skip_cache=True para evitar leer su propio cache (fix B1).
    Paso 1: BCPA — BrandClientPriceAgreement override (SSOT de overrides negociados)
    Paso 2A: PriceListGradeItem — MIN(unit_price_usd) de TODAS las activas (S22)
    Paso 2B: PriceListItem S14 — fallback explícito si no hay GradeItem para este SKU.
             Busca en PriceListItem (modelo S14) con misma lógica: activas, MIN price.
             (fix B4: backwards compat es contrato operativo, no comentario).
    Paso 3: Manual — retorna source='manual', price=None
    
    Post-resolución: si payment_days != None y existe EarlyPaymentPolicy activa,
    aplica descuento. El descuento se aplica sobre el precio resuelto en pasos 0-2.
    """
    result = {
        'price': None,
        'source': 'manual',
        'pricelist_version': None,
        'discount_applied': None,
        'base_price': None,
        'grade_moq': None,
        'size_multipliers': None,
        'grade_pricelist_version': None,
    }
    
    # Paso 0: CPA (skip cuando se llama desde recálculo — fix B1)
    if not skip_cache:
        cpa = ClientProductAssignment.objects.filter(
            client_subsidiary=client_subsidiary,
            brand_sku=brand_sku,
            is_active=True,
            cached_client_price__isnull=False,
        ).first()
        
        if cpa:
            result['price'] = cpa.cached_client_price
            result['source'] = 'assignment'
            result['base_price'] = cpa.cached_base_price
            result['pricelist_version'] = (
                cpa.cached_pricelist_version.version_label 
                if cpa.cached_pricelist_version else None
            )
            # Grade constraints son independientes del precio (fix R3-M1)
            _resolve_grade_constraints(result, brand_sku)
            _apply_early_payment(result, client_subsidiary, brand_sku.brand, payment_days)
            return result
    
    # Paso 1: BCPA
    bcpa = BrandClientPriceAgreement.objects.filter(
        client_subsidiary=client_subsidiary,
        brand_sku=brand_sku,
        is_active=True,
    ).first()
    
    if bcpa:
        result['price'] = bcpa.agreed_price
        result['source'] = 'agreement'
    else:
        # Paso 2A: PriceListGradeItem (S22) — MIN de todas las activas
        from django.db.models import Min
        
        grade_result = PriceListGradeItem.objects.filter(
            pricelist_version__brand=brand_sku.brand,
            pricelist_version__is_active=True,
            brand_sku=brand_sku,
        ).aggregate(min_price=Min('unit_price_usd'))
        
        if grade_result['min_price'] is not None:
            result['price'] = grade_result['min_price']
            result['source'] = 'pricelist_grade'
            
            # Obtener el winning_item (versión + grade del precio ganador)
            winning_item = PriceListGradeItem.objects.filter(
                pricelist_version__brand=brand_sku.brand,
                pricelist_version__is_active=True,
                brand_sku=brand_sku,
                unit_price_usd=grade_result['min_price'],
            ).select_related('pricelist_version').first()
            
            if winning_item:
                result['pricelist_version'] = winning_item.pricelist_version.version_label
                result['grade_moq'] = winning_item.moq_total
                result['base_price'] = winning_item.unit_price_usd
                result['size_multipliers'] = winning_item.size_multipliers
                result['grade_pricelist_version'] = winning_item.pricelist_version.version_label
        else:
            # Paso 2B: PriceListItem S14 — fallback explícito (fix B4)
            # PriceListItem es el modelo plano de Sprint 14: brand, product, price, valid_from, valid_to
            # S14 no tiene is_active — vigencia es solo por valid_from/valid_to (fix R2-M2)
            legacy_result = PriceListItem.objects.filter(
                brand=brand_sku.brand,
                product=brand_sku.product,
            ).filter(
                models.Q(valid_from__isnull=True) | models.Q(valid_from__lte=timezone.now())
            ).filter(
                models.Q(valid_to__isnull=True) | models.Q(valid_to__gte=timezone.now())
            ).aggregate(min_price=Min('price'))
            
            if legacy_result['min_price'] is not None:
                result['price'] = legacy_result['min_price']
                result['source'] = 'pricelist_legacy'
                result['base_price'] = legacy_result['min_price']
    
    # Post-resolución: grade constraints independientes del precio (fix R3-M1)
    # Si el precio vino de BCPA o legacy, aún puede haber Grade activo para este SKU.
    # Solo se llama si size_multipliers no fue ya poblado por Paso 2A.
    if result['size_multipliers'] is None:
        _resolve_grade_constraints(result, brand_sku)
    
    # Post-resolución: descuento por pronto pago (DEC-S22-03)
    _apply_early_payment(result, client_subsidiary, brand_sku.brand, payment_days)
    
    return result


def _resolve_grade_constraints(result, brand_sku):
    """
    Helper (fix R3-M1): poblar grade_moq y size_multipliers desde el Grade activo
    del brand_sku, INDEPENDIENTEMENTE de la fuente del precio.
    
    Esto desacopla la validación MOQ de la resolución de precio:
    - El precio puede venir de CPA, BCPA, o pricelist legacy.
    - El MOQ siempre viene del PriceListGradeItem activo con precio mínimo (si existe).
    - Si no hay Grade activo → size_multipliers=None (válido: SKU sin constraints de Grade).
    """
    from django.db.models import Min
    
    grade_item = PriceListGradeItem.objects.filter(
        pricelist_version__brand=brand_sku.brand,
        pricelist_version__is_active=True,
        brand_sku=brand_sku,
    ).order_by('unit_price_usd').first()  # winning = MIN price
    
    if grade_item:
        result['grade_moq'] = grade_item.moq_total
        result['size_multipliers'] = grade_item.size_multipliers
        result['grade_pricelist_version'] = grade_item.pricelist_version.version_label


def _apply_early_payment(result, client_subsidiary, brand, payment_days):
    """Helper: aplica descuento pronto pago si existe policy activa."""
    if result['price'] is None or payment_days is None:
        return
    try:
        policy = EarlyPaymentPolicy.objects.get(
            client_subsidiary=client_subsidiary,
            brand=brand,
            is_active=True,
        )
        tier = policy.tiers.filter(
            payment_days__gte=payment_days
        ).order_by('payment_days').first()
        
        if tier:
            result['base_price'] = result['price']
            discount = result['price'] * (tier.discount_pct / 100)
            result['price'] = result['price'] - discount
            result['discount_applied'] = tier.discount_pct
    except EarlyPaymentPolicy.DoesNotExist:
        pass  # Sin policy = sin descuento
```

---

## Items

### FASE 0 — Modelos y migraciones (estimado 3-4 días)

#### S22-01: PriceListVersion + PriceListGradeItem
- **Agente:** AG-02 Backend
- **Qué hacer:**
  1. Crear `PriceListVersion` (modelo M2 arriba)
  2. Crear `PriceListGradeItem` (modelo M3 arriba)
  3. Migración aditiva — no modificar ni eliminar `PriceListItem` existente (backwards compat S14)
  4. Admin registrado para ambos modelos
- **Criterio de done:**
  - [ ] Migrations aplicadas sin error
  - [ ] Admin funcional: crear versión, agregar items con grade
  - [ ] PriceListItem de S14 sigue funcionando (no se toca)

#### S22-02: ClientProductAssignment
- **Agente:** AG-02 Backend
- **Qué hacer:**
  1. Crear `ClientProductAssignment` (modelo M1 arriba)
  2. Admin con filtros por client_subsidiary, brand, is_active
  3. Unique constraint client_subsidiary + brand_sku
- **Criterio de done:**
  - [ ] Migrations aplicadas
  - [ ] Admin funcional
  - [ ] Constraint unique verificado (intento de duplicado → IntegrityError)

#### S22-03: EarlyPaymentPolicy + EarlyPaymentTier
- **Agente:** AG-02 Backend
- **Qué hacer:**
  1. Crear `EarlyPaymentPolicy` (modelo M4 arriba)
  2. Crear `EarlyPaymentTier` (modelo M4 arriba)
  3. Admin con inline (tiers dentro de policy)
  4. Unique constraints: policy per client×brand, tier per policy×days
- **Criterio de done:**
  - [ ] Migrations aplicadas
  - [ ] Admin con inline funcional
  - [ ] Constraints verificados

#### S22-04: Brand.min_margin_alert_pct
- **Agente:** AG-02 Backend
- **Qué hacer:**
  1. AddField `min_margin_alert_pct` a Brand (modelo M5)
  2. Migración aditiva (nullable, no rompe nada)
- **Criterio de done:**
  - [ ] Campo visible en Admin de Brand
  - [ ] NULL por default (alerta desactivada)

### FASE 1 — Pricing engine + servicios (estimado 3-4 días)

#### S22-05: Extender resolve_client_price() v2
- **Agente:** AG-02 Backend
- **Dependencia:** S22-01, S22-02, S22-03
- **Qué hacer:**
  1. Agregar Paso 0 (CPA) al waterfall existente
  2. Modificar Paso 2 para usar MIN() de N pricelists activas (PriceListGradeItem)
  3. Agregar post-resolución de descuento por pronto pago
  4. Retornar dict enriquecido (source, pricelist_version, discount_applied, base_price, grade_moq, size_multipliers, grade_pricelist_version)
  5. `size_multipliers` se puebla siempre que exista Grade activo para el SKU, independientemente de si el precio vino de CPA, BCPA o pricelist (fix R3-M1)
  6. **Mantener backwards compat:** si no se pasan payment_days ni proforma_mode, comportamiento idéntico a v1
- **Criterio de done:**
  - [ ] Waterfall 4 pasos funcional
  - [ ] Descuento pronto pago se aplica correctamente
  - [ ] Llamadas existentes (sin nuevos params) no se rompen

#### S22-06: Servicio activate_pricelist con lógica de extinción
- **Agente:** AG-02 Backend
- **Dependencia:** S22-01
- **Qué hacer:**
  1. `activate_pricelist(version_id, force=False)` en `pricing/services.py`
  2. Lógica de extinción por versión completa (DEC-S22-02, fix B3):
     - Evaluar TODAS las versiones activas anteriores del mismo brand.
     - Para cada versión anterior, comparar SKUs solapados con la nueva:
       - Si para TODOS los SKUs solapados el precio de la nueva versión es ≤ precio de la anterior → **extinguir versión anterior** (deactivation_reason='price_decrease'). La nueva versión cubre completamente a la anterior.
       - Si existe AL MENOS 1 SKU solapado donde la versión anterior tiene precio menor → **NO extinguir** (período de gracia). MIN() protege al cliente en runtime.
     - Si `force=True` → desactivar TODAS las versiones anteriores del brand (extinción manual CEO), sin evaluar precios.
  3. **Regla única, sin ambigüedad:** La extinción es siempre por versión completa. No existe mecanismo de desactivación parcial por SKU. El modelo PriceListVersion solo tiene `is_active` a nivel de versión.
  4. EventLog: registrar activación y cada extinción con payload: `{ version_activated, versions_extinct: [...], versions_kept: [...], reason }`
- **Criterio de done:**
  - [ ] Activación normal: nueva versión activa, anteriores evaluadas
  - [ ] Extinción: funciona cuando nueva versión cubre completamente a la anterior
  - [ ] Período de gracia: funciona cuando anterior tiene al menos 1 SKU más barato
  - [ ] Force: extingue todas las anteriores sin evaluar precios
  - [ ] EventLog registra cada acción con detalle

#### S22-07: Validación MOQ con Grade
- **Agente:** AG-02 Backend
- **Dependencia:** S22-01, S22-05
- **Qué hacer:**
  1. `validate_moq(proforma_id)` en `pricing/services.py`
  2. **Regla MOQ (actualizada post R3-M1):** El precio y el MOQ pueden venir de fuentes distintas. El precio se resuelve por el waterfall (CPA→BCPA→pricelist→manual). El MOQ se resuelve desde el PriceListGradeItem activo con precio mínimo para ese SKU, independientemente de la fuente del precio. resolve_client_price() retorna ambos en el mismo response: `price` + `source` para el precio, `size_multipliers` + `grade_moq` para constraints MOQ. validate_moq() usa `size_multipliers` y `grade_moq` del response — no reconsulta la DB.
  3. Para cada línea de la proforma:
     - Llamar resolve_client_price() → obtener `size_multipliers` del response
     - Si `size_multipliers` no es None:
       - Buscar la talla de esta línea en `size_multipliers`
       - WARNING si `quantity < size_multipliers[talla]`
  4. Agrupar líneas por referencia (product_key). Para cada referencia:
     - ERROR si `sum(quantities)` < `grade_moq` del response
  5. Retornar lista de warnings y errors con contexto (referencia, talla, esperado vs actual, grade_pricelist_version)
  6. El ERROR bloquea C5 (gate de proforma). El WARNING es informativo.
- **Criterio de done:**
  - [ ] WARNING por talla: funciona
  - [ ] ERROR por pedido: funciona
  - [ ] MOQ viene de size_multipliers del response (puede ser versión distinta al precio)
  - [ ] CPA + Grade activo → MOQ funciona (test 35)
  - [ ] C5 gate: integrado (si hay ERROR → C5 rechaza)

#### S22-08: Bulk assignment endpoint
- **Agente:** AG-02 Backend
- **Dependencia:** S22-02, S22-05
- **Qué hacer:**
  1. `POST /api/pricing/client-assignments/bulk/`
  2. Payload: `{ client_subsidiary_id, brand_id, product_key, price_override? }`
  3. Lógica: product_key mapea a N BrandSKUs (1 por talla). Crea N ClientProductAssignments.
  4. Si price_override: usa ese precio. Si no: llama resolve_client_price() para cada SKU y cachea.
  5. Response: `{ created: N, skipped: N (ya existían), errors: [...] }`
  6. Idempotente: si el CPA ya existe para un SKU, skip (no error).
- **Criterio de done:**
  - [ ] Bulk crea N CPAs por product_key
  - [ ] Idempotente: skip existentes
  - [ ] Price override funcional
  - [ ] Error report por línea

#### S22-09: Recálculo Celery task
- **Agente:** AG-02 Backend
- **Dependencia:** S22-02, S22-05, S22-06
- **Qué hacer:**
  1. `recalculate_assignments_for_brand(brand_id)` como Celery task
  2. Trigger: activate_pricelist → dispara task
  3. Para cada CPA activo de ese brand: llamar `resolve_client_price(..., skip_cache=True)` y actualizar cached_client_price, cached_base_price, cached_pricelist_version, cached_at. **skip_cache=True es obligatorio** (fix B1): sin esto, el recálculo lee su propio cache y no recalcula nada.
  4. Idempotente (UUID + checksum del resultado)
  5. EventLog al completar: cuántos CPAs recalculados, cuántos cambiaron de precio
- **Criterio de done:**
  - [ ] Task se dispara al activar pricelist
  - [ ] Recálculo correcto (cached_client_price actualizado)
  - [ ] Idempotente
  - [ ] EventLog registra resultado

#### S22-10: Alerta de margen
- **Agente:** AG-02 Backend
- **Dependencia:** S22-04, S22-09
- **Qué hacer:**
  1. Al final del recálculo Celery: comparar cada CPA con costo base (de ENT_COMERCIAL_COSTOS si disponible, o de PriceListGradeItem.unit_price_usd como proxy)
  2. Si `margin < Brand.min_margin_alert_pct` → crear NotificationTemplate (S21) con tipo 'margin_alert'
  3. Solo si Brand.min_margin_alert_pct no es NULL (alerta activa)
  4. Payload de alerta: SKU, client, precio cached, costo estimado, margen calculado
- **Criterio de done:**
  - [ ] Alerta se genera cuando margen < threshold
  - [ ] No se genera si threshold es NULL
  - [ ] Payload tiene toda la info para que el CEO decida

### FASE 2 — Upload y parsing (estimado 2-3 días)

#### S22-11: Upload pricelist CSV/Excel
- **Agente:** AG-02 Backend
- **Qué hacer:**
  1. `POST /api/pricing/pricelists/upload/` — multipart file upload
  2. Parsing con Pandas (CSV y Excel):
     - Detectar columnas: Referência, Preço, Grade, tallas (33/34 a 47/48)
     - Parsear multiplicadores por talla: número = multiplicador, '-' = no disponible
     - Parsear metadata: Cabedal, Bico, Palmilha, NCM, CA, Código, Centro
  3. Validación línea por línea:
     - reference_code no vacío
     - Precio numérico positivo
     - Al menos 1 talla con multiplicador > 0
     - Match a BrandSKU (warning si no matchea — se puede mapear después)
  4. Error report: `{ valid_lines: N, warnings: [...], errors: [...], preview: [...first 5] }`
  5. NO crear PriceListVersion automáticamente — retornar preview. CEO confirma → S22-12.
- **Criterio de done:**
  - [ ] CSV parsing funcional
  - [ ] Excel parsing funcional
  - [ ] Validación por línea con error report
  - [ ] Preview retornado (no se guarda hasta confirmación)

#### S22-12: Confirmar y crear PriceListVersion
- **Agente:** AG-02 Backend
- **Dependencia:** S22-11
- **Qué hacer:**
  1. `POST /api/pricing/pricelists/confirm/` — con session_id del upload
  2. Crear PriceListVersion + N PriceListGradeItems
  3. NO activar automáticamente — CEO activa manualmente (S22-06)
  4. Retornar version_id + summary (items creados, tallas mapeadas, unmapped)
- **Criterio de done:**
  - [ ] Versión creada con is_active=False
  - [ ] Items con grades y multiplicadores correctos
  - [ ] Summary con unmapped SKUs

### FASE 3 — Frontend (estimado 5-6 días)

**Contexto Brand Console pre-S22:**
Brand Console tiene 7 tabs entregados en sprints anteriores:
```
Tab 1: Overview          (S14)
Tab 2: Agreements        (S14)
Tab 3: Orders            (S14)
Tab 4: Catalog           (S14) ← productos + BrandSKU
Tab 5: Pricing           (S15) ← pricelist items planos, overrides, upload básico
Tab 6: Operations        (S15) ← workflow policy read-only
Tab 7: Tallas            (S19) ← BrandSizeSystem assignments
```

**Qué cambia en S22:**
- Tab 4 (Catalog) se enriquece: cada producto muestra precio resuelto, MOQ Grade, y tallas disponibles del Grade
- Tab 5 (Pricing) se reescribe: deja de ser items planos y pasa a PriceListVersion + GradeItems + extinción + historial. Upload se reemplaza con el nuevo flujo preview→confirm
- Tab 8 (nuevo): Payment Terms — EarlyPaymentPolicy por cliente
- Tab 9 (nuevo): Assignments — CPA por cliente con bulk assign
- Client Console Catalog se enriquece: precios resueltos para ESE cliente (con descuento pronto pago aplicado)

**Regla:** NO crear tabs duplicados. Reutilizar estructura existente. S22 EXTIENDE tabs 4 y 5, y AGREGA tabs 8 y 9.

#### S22-13: Frontend expediente/proforma: pre-fill precio + MOQ
- **Agente:** AG-03 Frontend
- **Dependencia:** S22-05 (API resolve_client_price v2)
- **Qué hacer:**
  1. Al seleccionar BrandSKU en una proforma → llamar `GET /api/pricing/resolve/?brand_sku_id=X&client_subsidiary_id=Y&payment_days=Z`
  2. Pre-llenar unit_price con precio resuelto
  3. Tooltip con desglose: "Base: $X (Yv6) × descuento Zd = $W — fuente: pricelist"
  4. Si source='manual' → campo editable sin pre-fill, label "Precio manual"
  5. Si MOQ warning → mostrar badge warning con texto: "MOQ talla: mín X pares"
  6. Si grade_moq en response → mostrar nota: "Pedido mínimo referencia: X pares"
- **Criterio de done:**
  - [ ] Pre-fill funciona al seleccionar SKU
  - [ ] Tooltip muestra fuente y desglose
  - [ ] MOQ warning por talla visible
  - [ ] MOQ total por referencia visible
  - [ ] Editable (override) con price_source='override'

#### S22-14: Refactor Brand Console Tab Pricing → Pricelists versionadas
- **Agente:** AG-03 Frontend
- **Dependencia:** S22-11, S22-12, S22-06
- **Qué hacer:**
  1. **Reemplazar contenido del Tab 5 (Pricing) existente** — no crear tab nuevo. El tab S15 mostraba PriceListItems planos; ahora muestra PriceListVersions con GradeItems.
  2. Sección "Versiones activas": lista de PriceListVersions con status badge (active/inactive/extinct), fecha, uploaded_by. N pueden estar activas (badge verde en cada activa).
  3. Sección "Detalle versión" (expandible por click): tabla de PriceListGradeItems con columnas:
     - Referencia (mono) | Descripción | Bico | NCM | Precio USD | Grade | MOQ total
     - Expandir fila → multiplicadores por talla (37: 5, 38: 5, 39: 10, 40: 10...)
  4. Upload: botón "Subir nueva versión" → file picker (CSV/Excel) → **preview con tabla parseada** (referencia, precio, grade, multiplicadores) → botón "Confirmar" → crea versión inactiva
  5. Acciones por versión:
     - "Activar" → modal de confirmación: "¿Activar {label}? Se evaluarán las versiones activas anteriores. Una versión previa solo se extinguirá si la nueva no empeora el precio en ningún SKU solapado."
     - "Desactivar" → simple toggle
     - "Extinguir anteriores" → modal: "¿Forzar extinción de todas las versiones anteriores? Solo {label} quedará activa."
  6. Historial: log de activaciones/extinciones al final del tab (timeline)
- **Criterio de done:**
  - [ ] Tab Pricing muestra versiones (no items planos)
  - [ ] Detalle versión con GradeItems expandibles
  - [ ] Multiplicadores por talla visibles al expandir
  - [ ] Upload flow completo (pick → preview → confirm)
  - [ ] Activar con extinción inteligente (confirmación muestra qué pasa)
  - [ ] Force extinct funcional
  - [ ] Historial de cambios visible

#### S22-15: Enriquecer Brand Console Tab Catalog con pricing + Grade
- **Agente:** AG-03 Frontend
- **Dependencia:** S22-05, S22-01
- **Qué hacer:**
  1. **Extender Tab 4 (Catalog) existente** — no crear tab nuevo. Actualmente muestra ProductMaster/BrandSKU plano.
  2. Agregar columnas a tabla de productos:
     - "Precio base" → MIN(precio) de pricelists activas para ese BrandSKU. Si no hay → "Sin precio"
     - "MOQ Grade" → sum(multiplicadores) del PriceListGradeItem. Si no hay → "-"
     - "Tallas disponibles" → badge count de tallas con multiplicador > 0 en el Grade
  3. Expandir fila de producto → sección "Grade detalle":
     - Tabla de tallas con multiplicador por talla
     - Tallas fuera del Grade = "No disponible" (gris)
     - Precio unitario (mismo para todas las tallas del Grade)
  4. Filtro: "Solo con precio" toggle → filtra productos que tienen al menos 1 pricelist activa
  5. Si el producto tiene N pricelists activas con precios distintos → mostrar rango: "$4.71 – $5.76"
- **Criterio de done:**
  - [ ] Columnas precio base + MOQ + tallas visibles en catálogo
  - [ ] Expandir producto muestra Grade detalle con multiplicadores
  - [ ] Filtro "Solo con precio" funcional
  - [ ] Rango de precios cuando hay N pricelists activas

#### S22-16: Brand Console Tab Payment Terms (nuevo tab 8)
- **Agente:** AG-03 Frontend
- **Dependencia:** S22-03
- **Qué hacer:**
  1. **Nuevo Tab 8 "Payment Terms"** en Brand Console (después de Tallas)
  2. Vista por cliente: lista de clientes del brand con indicator de policy activa/inactiva
  3. Expandir cliente → EarlyPaymentPolicy con:
     - Base: {base_payment_days}d, comisión {base_commission_pct}%
     - Tabla tiers: plazo | descuento % | precio ejemplo (calculado: base_price × (1 - discount))
  4. CRUD: crear policy, agregar/editar/eliminar tiers inline
  5. Toggle active/inactive por policy
- **Criterio de done:**
  - [ ] Tab visible en Brand Console (posición 8)
  - [ ] Lista clientes con status policy
  - [ ] CRUD policy + tiers inline funcional
  - [ ] Precio ejemplo calculado dinámicamente
  - [ ] Validación: días únicos por policy

#### S22-17: Brand Console Tab Assignments (nuevo tab 9)
- **Agente:** AG-03 Frontend
- **Dependencia:** S22-08, S22-02
- **Qué hacer:**
  1. **Nuevo Tab 9 "Assignments"** en Brand Console (después de Payment Terms)
  2. Selector de cliente (dropdown) → tabla de assignments para ese cliente:
     - Product key | Tallas asignadas (count) | Cached price | Status (active/inactive) | Cache age
  3. Expandir product_key → tabla de CPAs por talla: talla | cached_price | cached_at | pricelist_version
  4. Bulk assign: botón "Asignar productos" → modal:
     - Selector múltiple de product_keys del catálogo del brand
     - Checkbox "Usar precio de pricelist" (default on) / "Override manual" con input
     - Confirmar → POST bulk → resultado (creados/skipped/errors)
  5. Toggle active/inactive individual por CPA
  6. Indicador "⚠ Cache desactualizado" si cached_at < última activación de pricelist del brand
  7. Botón "Recalcular precios" → trigger manual del recálculo Celery
- **Criterio de done:**
  - [ ] Selector cliente + tabla assignments funcional
  - [ ] Expandir por product_key muestra CPAs por talla
  - [ ] Bulk assign modal funcional
  - [ ] Toggle active/inactive funcional
  - [ ] Stale indicator funcional
  - [ ] Recalcular manual funcional

#### S22-18: Enriquecer Client Console Catalog con precio resuelto
- **Agente:** AG-03 Frontend
- **Dependencia:** S22-05
- **Qué hacer:**
  1. **Extender Tab Catalog de Client Console** (S14-11) — actualmente usa `/api/portal/catalog/` que filtra por AssortmentPolicy y llama resolve_client_price v1.
  2. Actualizar para usar resolve_client_price v2: pasar payment_days del cliente (si tiene EarlyPaymentPolicy)
  3. Mostrar precio final (con descuento pronto pago aplicado) en la columna de precio
  4. Si hay descuento → badge: "Precio {payment_days}d: -X%"
  5. MOQ Grade visible por producto: "Pedido mínimo: X pares"
  6. **CLIENT_* NUNCA ve:** cascada de resolución, margen, precio base pre-descuento, ni fuente del precio. Solo ve SU precio final.
- **Criterio de done:**
  - [ ] Catálogo cliente muestra precio con descuento aplicado
  - [ ] Badge de descuento visible
  - [ ] MOQ visible
  - [ ] No leakea info CEO-ONLY (cascada, margen, fuente)

### FASE 4 — Tests y QA (estimado 2 días)

#### S22-19: Tests backend (30+)
- **Agente:** AG-02 Backend
- **Dependencia:** Todo lo anterior

```python
# Tests obligatorios (38 mínimo)

# PriceListVersion + Grade
1. Upload CSV → preview correcto ✓
2. Upload Excel → preview correcto ✓
3. Confirm → PriceListVersion creada con is_active=False ✓
4. Activate → is_active=True, activated_at set ✓
5. Grade multiplicadores parseados correctamente ✓
6. Talla con '-' = no disponible ✓
7. MOQ total = sum(multiplicadores) ✓

# Extinción por versión completa (DEC-S22-02, fix B3)
8. Nueva versión cubre completamente (todos SKUs ≤) → extinción inmediata ✓
9. Nueva versión con al menos 1 SKU más caro → coexistencia (gracia) ✓
10. Force extinct → todas las anteriores desactivadas sin evaluar precios ✓
11. MIN(precio) retorna precio de versión más barata ✓
12. EventLog registra activación + extinción con payload detallado ✓

# ClientProductAssignment
13. Bulk assign por product_key → N CPAs creados ✓
14. Bulk assign idempotente → skip existentes ✓
15. CPA con cached_client_price → resuelto en paso 0 ✓
16. CPA sin cache → fallback a paso 1+ ✓
17. Unique constraint client+sku → IntegrityError ✓

# resolve_client_price v2
18. Paso 0 (CPA) → retorna cached_client_price ✓
19. Paso 1 (BCPA) → retorna agreed_price ✓
20. Paso 2A (PriceListGradeItem MIN) → retorna min de activas ✓
21. Paso 2B (PriceListItem S14 fallback) → retorna si no hay GradeItem (fix B4) ✓
22. Paso 3 (manual) → source='manual', price=None ✓
23. Con payment_days → descuento aplicado ✓
24. Sin EarlyPaymentPolicy → sin descuento ✓
25. Backwards compat: llamada sin nuevos params → OK ✓
26. skip_cache=True → salta paso 0, resuelve desde paso 1+ (fix B1) ✓
27. skip_cache=False (default) → usa cache si existe ✓

# EarlyPaymentPolicy
28. Policy con 3 tiers → descuento correcto por plazo ✓
29. Unique constraint client+brand → IntegrityError ✓
30. Cambio de policy → ConfigChangeLog registra (fix M2) ✓

# MOQ validation (fix R3-M1: grade constraints independent of price source)
31. Cantidad < multiplicador talla → WARNING ✓
32. Sum cantidades < MOQ total Grade → ERROR ✓
33. ERROR en MOQ → C5 gate rechaza ✓
34. Precio de pricelist_grade → size_multipliers del winning_item ✓
35. CPA activo + Grade activo → size_multipliers poblado, MOQ WARNING/ERROR funciona (fix R3-M1) ✓
36. BCPA activo + Grade activo → size_multipliers poblado, MOQ WARNING/ERROR funciona (fix R3-M1) ✓
37. Legacy sin Grade → size_multipliers=None, validate_moq() skips gracefully ✓

# Recálculo Celery
38. Activar pricelist más barata → task recalcula CPAs con skip_cache=True → precio cambia (fix B1) ✓
39. CPA con precio que rompe margen → alerta generada ✓
40. Brand sin min_margin_alert_pct → sin alerta ✓

# Portal catalog (S22-18 backend support)
41. Portal catalog endpoint retorna precio con descuento aplicado ✓
42. Portal catalog endpoint NO retorna source/base_price/discount/size_multipliers/grade_pricelist_version para CLIENT_* (fix B2, R4-m1) ✓

# Regresión
43. resolve_client_price v1 calls → no se rompen ✓
44. PriceListItem de S14 → sigue funcionando como fallback paso 2B ✓
```

#### S22-20: Validación manual frontend
- **Agente:** AG-03 Frontend
- **Dependencia:** S22-13 a S22-18

```
Checklist validación manual frontend (20 checks):

# Brand Console — Tab Pricing (refactored S22-14)
□ Tab Pricing muestra PriceListVersions (no items planos)
□ Detalle versión expandible con GradeItems
□ Multiplicadores por talla visibles al expandir referencia
□ Upload CSV → preview con tabla de referencias y multiplicadores
□ Upload Excel → preview correcto
□ Confirmar upload → versión creada (inactive)
□ Activar versión → modal con explicación de extinción → activa
□ Force extinct → modal → anteriores desactivadas
□ Historial de cambios visible en timeline

# Brand Console — Tab Catalog (enriched S22-15)
□ Catálogo muestra columnas precio base + MOQ + tallas disponibles
□ Expandir producto muestra Grade detalle con multiplicadores por talla
□ Filtro "Solo con precio" funcional

# Brand Console — Tab Payment Terms (S22-16)
□ Tab visible, CRUD policy + tiers inline funcional

# Brand Console — Tab Assignments (S22-17)
□ Selector cliente + tabla assignments funcional
□ Bulk assign modal funcional
□ Stale indicator visible

# Client Console — Catalog (S22-18)
□ Catálogo cliente muestra precio con descuento pronto pago
□ MOQ visible por producto
□ NO muestra cascada, margen, ni fuente del precio

# Expediente/Proforma (S22-13)
□ Pre-fill precio + tooltip desglose + MOQ warning al seleccionar SKU
```

---

## Seguridad (ref → ENT_PLAT_SEGURIDAD)

| Aspecto | Evaluación | Acción |
|---------|-----------|--------|
| Superficie de ataque | Upload file endpoint nuevo | Validar extensión (csv/xlsx only), tamaño max (10MB), sanitizar contenido. No ejecutar macros. |
| Pricing data | CEO-ONLY | Endpoints de pricing detrás de `IsAuthenticated + IsCEOOrAgent`. CLIENT_* puede ver SU precio resuelto pero no la cascada ni el margen. |
| Bulk assignment | Operación masiva | Rate limit: max 1 request/min. Auditar en EventLog. |
| File storage | Pricelist uploaded files | Signed URLs con TTL 30min (ref CEO-27). No links permanentes. |
| ClientScopedManager | Aplica | Endpoints de CPA y resolve filtran por client_subsidiary del user cuando el caller es CLIENT_*. |
| Celery task | Background execution | No expone endpoint directo. Solo se dispara desde activate_pricelist (autenticado). |
| Alerta de margen | CEO-ONLY | Solo visible para CEO. Notificación vía activity feed (S21). |

**Sin nuevos canales de acceso externo.** El upload es Brand Console (INTERNAL). El resolve es para uso interno y portal (CLIENT_* ve solo su precio).

---

## Gate Sprint 22

- [ ] PriceListVersion + PriceListGradeItem creados y funcionales
- [ ] Multiplicadores por talla parseados de CSV/Excel
- [ ] N pricelists activas simultáneamente con lógica de extinción
- [ ] ClientProductAssignment funcional con cached_client_price
- [ ] resolve_client_price() v2 usa waterfall de 4 pasos + descuento pronto pago
- [ ] EarlyPaymentPolicy funcional con tiers por plazo
- [ ] Bulk assignment por product_key funcional
- [ ] MOQ Grade: WARNING por talla, ERROR por pedido (bloquea C5)
- [ ] Recálculo Celery al activar pricelist
- [ ] Alerta de margen configurable por brand
- [ ] Brand Console Tab Pricing refactored: versiones + GradeItems + extinción + historial
- [ ] Brand Console Tab Catalog enriched: precio base + MOQ + Grade detalle por producto
- [ ] Brand Console Tab Payment Terms: CRUD policy + tiers
- [ ] Brand Console Tab Assignments: vista por cliente + bulk assign + stale indicator
- [ ] Client Console Catalog: precio con descuento pronto pago + MOQ (sin leakeo CEO-ONLY)
- [ ] Frontend expediente: pre-fill precio con tooltip de fuente + MOQ warning
- [ ] 44 tests backend verdes
- [ ] 20 checks validación manual FE
- [ ] 0 regresiones en tests existentes (S14 pricing, S20 proformas)
- [ ] Backwards compat: PriceListItem de S14 sigue funcionando

---

## Excluido explícitamente

- **Rebates y metas trimestrales** → S23 (solo referencia en DEC-S22-04).
- **Herencia brand→cliente→subsidiaria** → S23.
- **BrandWorkflowPolicy migración a DB** → S23.
- **Comisiones por producto/cliente** → S23.
- **DSL tipado para fórmulas de pricing** → post-MVP.
- **FXRatePolicy multi-moneda** → post-MVP (Marluvas opera solo USD).
- **Proforma mode routing** → el parámetro `proforma_mode` está en la firma pero no se usa en v1. Se conecta en S23 cuando las pricelists por mode sean distintas.

---

## Dependencias internas

```
S22-01 (PriceListVersion) → S22-05 (waterfall v2)
S22-01 (PriceListVersion) → S22-06 (activate/extinct)
S22-01 (PriceListVersion) → S22-11 (upload)
S22-01 (PriceListVersion) → S22-15 (FE catalog enrichment)
S22-02 (CPA) → S22-05 (paso 0 waterfall)
S22-02 (CPA) → S22-08 (bulk assign)
S22-02 (CPA) → S22-09 (recálculo)
S22-02 (CPA) → S22-17 (FE assignments tab)
S22-03 (EarlyPaymentPolicy) → S22-05 (post-resolución)
S22-03 (EarlyPaymentPolicy) → S22-16 (FE payment terms tab)
S22-04 (Brand margin field) → S22-10 (alerta)
S22-05 (waterfall v2) → S22-07 (MOQ validation)
S22-05 (waterfall v2) → S22-13 (FE pre-fill expediente)
S22-05 (waterfall v2) → S22-15 (FE catalog pricing columns)
S22-05 (waterfall v2) → S22-18 (FE client console catalog)
S22-06 (activate) → S22-09 (trigger recálculo)
S22-08 (bulk assign) → S22-17 (FE assignments tab)
S22-09 (recálculo) → S22-10 (alerta)
S22-11 (upload) → S22-12 (confirm)
S22-12 (confirm) → S22-14 (FE pricelists tab refactor)

Orden sugerido:
  AG-02 Día 1-2: S22-01 + S22-02 + S22-03 + S22-04 (modelos + migraciones)
  AG-02 Día 3-4: S22-05 + S22-06 (waterfall v2 + extinción)
  AG-02 Día 5-6: S22-07 + S22-08 (MOQ + bulk)
  AG-02 Día 7-8: S22-09 + S22-10 (Celery + alerta)
  AG-02 Día 9-10: S22-11 + S22-12 (upload + confirm)
  AG-03 Día 1-3: S22-15 (catalog enrichment — solo necesita S22-01 + API resolve)
  AG-03 Día 3-5: S22-14 (pricelists tab refactor — necesita upload APIs)
  AG-03 Día 5-6: S22-16 + S22-17 (payment terms + assignments tabs)
  AG-03 Día 7-8: S22-13 (pre-fill expediente — necesita waterfall v2 completo)
  AG-03 Día 8-9: S22-18 (client console catalog — necesita resolve v2 + portal endpoint)
  AG-02 Día 11-12: S22-19 (tests)
  AG-03 Día 10: S22-20 (validación manual FE)
```

---

## Notas para auditoría

1. **DEC-S22-02 (N pricelists activas — fix B3):** La extinción es siempre por versión completa. Regla única: se extingue una versión previa solo si, para TODOS los SKUs solapados, la nueva versión tiene precio ≤. Si existe al menos 1 SKU donde la versión previa es más barata, la versión previa permanece activa. No existe desactivación parcial por SKU — el modelo PriceListVersion solo tiene `is_active` a nivel de versión. Force bypass esta evaluación.

2. **DEC-S22-03 (Pronto pago como policy por cliente):** El descuento se aplica DESPUÉS de resolver el precio base (pasos 0-2). El cached_client_price del CPA se calcula SIN descuento pronto pago (el descuento se aplica en runtime al construir la proforma). EarlyPaymentPolicy es mutable en MVP (excepción explícita a S14-C5, fix M2) — cambios se registran en ConfigChangeLog vía signal.

3. **MOQ desacoplado del precio (fix R3-M1, actualizado R4):** Tras el desacople, precio y MOQ pueden venir de fuentes distintas. El precio se resuelve por el waterfall completo (CPA→BCPA→pricelist→manual). El MOQ se resuelve siempre desde el PriceListGradeItem activo con precio mínimo para ese SKU (vía `_resolve_grade_constraints()`). El response distingue ambos orígenes: `pricelist_version` = fuente del precio, `grade_pricelist_version` = fuente del MOQ/size_multipliers. Cuando ambos coinciden (precio vino de Paso 2A), los dos campos tienen el mismo valor. Cuando difieren (precio de CPA/BCPA, MOQ de Grade activo), los campos son distintos. El frontend interno puede mostrar ambos si necesita explicar la fuente.

4. **Backwards compat con S14 es contrato operativo (fix B4):** El pseudocódigo tiene fallback explícito: Paso 2A busca PriceListGradeItem (S22), Paso 2B busca PriceListItem (S14) si no hay grade item. No se eliminan datos de S14. Source distingue: 'pricelist_grade' vs 'pricelist_legacy'. Tests 21, 40 y 41 verifican esto explícitamente.

5. **skip_cache en recálculo (fix B1):** resolve_client_price() acepta `skip_cache=True` que salta Paso 0 (CPA). El recálculo Celery (S22-09) SIEMPRE pasa skip_cache=True. Sin esto, el recálculo leería su propio cache y nunca llegaría a las pricelists actualizadas. Test 35 verifica: "activar pricelist más barata → CPA cambia de precio".

6. **Response contracts por visibilidad (fix B2):** Dos serializers separados (PricingInternalSerializer para CEO/AGENT_*, PricingPortalSerializer para CLIENT_*). El portal nunca ve source, base_price, discount_applied, pricelist_version. Margen nunca sale del backend en ningún serializer. Tests 38-39 verifican.

7. **proforma_mode diferido:** El parámetro está en la firma para evitar breaking change futuro, pero no se usa en S22. En S23, cuando las pricelists se puedan asociar a modes específicos, el filtro se activa en Paso 2A.

8. **EarlyPaymentTier.payment_days semántica:** El tier se selecciona como "el primer tier cuyo payment_days >= payment_days solicitado". Si pagás a 30 días y hay tiers para 8d, 30d, 60d → se aplica el tier de 30d.

9. **storage_key en vez de file_url (fix M3):** PriceListVersion.storage_key guarda el object path en storage. Signed URLs se generan al leer con TTL 30min. Nunca se persiste una URL firmada — expira y deja rastro muerto.

10. **Integración con consolas existentes (no tabs duplicados):** Brand Console pre-S22 tiene 7 tabs. S22 refactora Tab 5 (Pricing), enriquece Tab 4 (Catalog), y agrega Tab 8 (Payment Terms) y Tab 9 (Assignments). Client Console Tab 2 (Catalog) se enriquece con precio post-descuento + MOQ.

11. **Portal catalog security (CLIENT_*):** Endpoint `/api/portal/catalog/` usa PricingPortalSerializer (fix B2). Response al CLIENT_* retorna `price` (final) y `moq`, NUNCA retorna source, base_price, discount_applied, pricelist_version. Cumple R6 y C5.
