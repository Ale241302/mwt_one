# LOTE_SM_SPRINT18 — Motor de Tallas Genérico + Endpoints Backend
id: LOTE_SM_SPRINT18
version: 3.4
visibility: [INTERNAL]
domain: Plataforma (IDX_PLATAFORMA)
status: DRAFT — Pendiente aprobación CEO
stamp: DRAFT v3.4 — 2026-03-26
tipo: Lote ruteado (ref → PLB_ORCHESTRATOR §E)
sprint: 18
priority: P0
depends_on: LOTE_SM_SPRINT17 (DONE v2.0)
refs: ENT_OPS_STATE_MACHINE (FROZEN v1.2.2), ROADMAP_SPRINTS_17_27,
      ROADMAP_CONVERGENCIA_MWTONE (Sprint 18 expandido),
      ENT_OPS_TALLAS (SSOT tallas RW), ENT_MERCADO_TALLAS (equivalencias),
      COM07_COM08_nomenclatura_marluvas_v1 (tallas Marluvas),
      AGENT_A_BRECHA_FUNCIONAL (hallazgos H2/H5/H6/H7),
      ENT_COMERCIAL_PRICING (SSOT pricing), ENT_PLAT_SEGURIDAD,
      ENT_GOB_DECISIONES (DEC-EXP-01 a DEC-EXP-05)

changelog:
  - v1.0 (2026-03-26): Compilación inicial desde ROADMAP_CONVERGENCIA Sprint 18 (S18-01 a S18-19). BrandSizeChart como modelo flat.
  - v1.1 (2026-03-26): Incorporación fixes Agent-A Fase 0 (brand_sku FK, valid_to bug, campos nullable, hook dispatcher).
  - v2.0 (2026-03-26): REDISEÑO — Motor de tallas como subsistema genérico del catálogo. BrandSizeChart flat → BrandSizeSystem + BrandSize + SizeEquivalence (3 modelos). Insight CEO: Rana Walk (S1-S6) y Marluvas (33-47) siguen la misma lógica de creación. El subsistema es reutilizable por cualquier marca futura. S18-01 rediseñado como item de arquitectura, no como fix aislado.
  - v2.1 (2026-03-26): Corrección CEO — 3 cambios: (1) Múltiples sistemas activos por brand (is_default es hint UI, no restricción). (2) Creación on-demand vinculada a producto, queda a nivel brand. (3) Equivalencias 1:N — una BrandSize puede mapear a múltiples valores en el mismo standard_system (ej: BR42→US8.5 + BR42→US9). unique_together ajustado a (brand_size, standard_system, value). +is_primary +display_order en SizeEquivalence. Tablas seed actualizadas con registros individuales, no rangos string.
  - v3.0 (2026-03-26): REDISEÑO MAYOR — Motor dimensional genérico de plataforma. (1) SizeSystem desacoplado de Brand — es servicio de plataforma, no del brand. FK brand eliminado, reemplazado por BrandSizeSystemAssignment (M:N). (2) Soporte multidimensional: +SizeDimension (N dimensiones por sistema) + SizeEntryValue (valor por dimensión por entry). Calzado=1 dim, camisa=3 dims, pantalón=3 dims. (3) App propia `sizing/` (no dentro de catalog/). (4) standard_system es CharField libre (no choices) para extensibilidad sin migraciones. (5) 6 modelos: SizeSystem, SizeDimension, SizeEntry, SizeEntryValue, SizeEquivalence, BrandSizeSystemAssignment. Ejemplo completo calzado + camisa documentado.
  - v3.1 (2026-03-26): Fixes auditoría R1 (ChatGPT 8.1/10 — 8 hallazgos). H1: seed idempotente con get_or_create + Brand.DoesNotExist controlado. H2: migración "una tanda coordinada por app" (no un solo archivo). H3: +clean() cross-system en SizeEntryValue + validate_entry_completeness() servicio. H4: resolve_client_price cerrada ambigüedad DateRangeField vs campos separados. H5: PATCH alineados con state machine FROZEN (CONFIRMADO no COTIZACION, +justificación estados sin PATCH). H6: factory_order_number declarado read-only derivado de FactoryOrder principal. H7: separación payment_status (PENDING/CONFIRMED/REJECTED) vs credit_released (flag Expediente). H8: nomenclatura legacy barrida (BrandSizeChart/BrandSizeSystem→taxonomía v3).
  - v3.2 (2026-03-26): Fixes auditoría R2 (ChatGPT 8.8/10 — 7 hallazgos). H1: Ruta crédito cerrada — POST crea PENDING, PATCH `/confirmar/` → CONFIRMED + recálculo + auto-release. H2: Bundle credit_status→credit_released + credit_exposure (campos reales del modelo). H3: Merge alineado FROZEN (REGISTRO/PI_SOLICITADA/CONFIRMADO, followers vía c_cancel). H4: FactoryOrder principal = menor ID activa (regla determinista, sin bifurcación). H5: Seed +pseudocódigo concreto get_or_create para Entry/EntryValue/Equivalence. H6: Pricing una sola verdad (campos separados) + grep previo obligatorio. H7: DONE S18-04 corregido a 6 campos (5 nullable + 1 default). +validate_entry_completeness amarrado a admin save_model.
  - v3.3 (2026-03-26): Fixes auditoría R3 (ChatGPT 9.1/10 — 3 hallazgos). H1: recalculate_expediente_credit() ahora es fuente única de verdad bidireccional para credit_released (activa Y revierte). S18-16 simplificado a sync CreditExposure + EventLog. +test regresión: merge post-release revierte flag. H2: S18-06 BundleSerializer alineado exactamente con S18-14 (credit_released + credit_exposure, no credit_status a nivel expediente). DONE S18-06 especifica campos exactos. H3: S18-08 +sync_factory_order_number() explícita invocada en POST/PATCH/DELETE del viewset. +4 tests sync (crear primera, crear segunda, delete principal, delete última).
  - v3.4 (2026-03-26): Fix auditoría R4 (ChatGPT 9.4/10 — 1 hallazgo). S18-04 viñeta contradictoria corregida: credit_released lo setea SOLO recalculate (S18-15), S18-16 solo sincroniza CreditExposure + EventLog. +barrido residuos "auto credit_release" en S18-09 DONE, tests, checklist → renombrados a scope real S18-16.

---

## Contexto

Sprint 18 es el segundo del ROADMAP_SPRINTS_17_27. Su objetivo es doble:

1. **Fixes bloqueantes (Agent-A):** brand_sku FK en ExpedienteProductLine, bug pricing valid_to=null, campos nullable, hook dispatcher.
2. **Endpoints backend:** Toda la funcionalidad de S17 (modelos) expuesta vía API REST.

**Cambio arquitectónico v2.0→v3.0:** El motor de tallas evolucionó de un modelo flat (v1.1) a un subsistema de 3 modelos por marca (v2.0) a un **motor dimensional genérico de plataforma** (v3.0): app `sizing/` con 6 modelos (SizeSystem, SizeDimension, SizeEntry, SizeEntryValue, SizeEquivalence, BrandSizeSystemAssignment). Desacoplado de Brand, soporta N dimensiones (calzado=1, ropa=3+), equivalencias 1:N, compartible entre brands vía M:N.

**Estado post-Sprint 17 (DONE v2.0):**
- State machine 8 estados, 28+ commands con lógica real
- ExpedienteProductLine con FK a ProductMaster (pero sin talla ni BrandSKU)
- FactoryOrder, ExpedientePago funcionales
- ~30 campos operativos por estado
- Portal 3 endpoints con tenant isolation
- DESPACHO funcional (C11 corregido, C11B creado)
- REOPEN verificado, C22 integrado en dispatcher
- CreditPolicy + CreditExposure + CreditOverride funcionales
- ProductMaster 565 SKUs cargados

**Lo que falta (scope de este sprint):**
- EPL sin FK a BrandSKU → no se puede pedir al fabricante con talla
- BrandSKU.size es CharField libre → no hay catálogo de tallas por marca
- Bug valid_to=null en resolve_client_price() → pricelists vigentes no se encuentran
- No hay hook post-command en dispatcher → bloquea emails S20
- 0 endpoints PATCH por estado
- 0 endpoints merge/split
- 0 CRUD FactoryOrder vía API
- Bundle detalle incompleto (sin product_lines, factory_orders, pagos)

---

## Decisiones ya resueltas (NO preguntar de nuevo)

| Decisión | Ref | Detalle |
|----------|-----|---------|
| `factory_order_number` genérico + modelo `FactoryOrder` relacional | DEC-EXP-01 | Multi-fabricante. Ya implementado en S17. |
| Merge master/follower elegido por CEO | DEC-EXP-02 | No automático. |
| Crédito = snapshot + recálculo local | DEC-EXP-03 | No crédito vivo. |
| EPL FK a ProductMaster (no texto libre) | DEC-EXP-04 | Ya implementado en S17. |
| PATCH por estado son ADICIONALES a commands | DEC-EXP-05 | No reemplazan commands. |

## Decisión nueva Sprint 18

| Decisión | Ref | Detalle |
|----------|-----|---------|
| Motor dimensional genérico de plataforma | DEC-SIZE-01 | App `sizing/` independiente — servicio de plataforma, no del brand. SizeSystem + SizeDimension + SizeEntry + SizeEntryValue + SizeEquivalence + BrandSizeSystemAssignment (6 modelos). Soporta N dimensiones (calzado=1, camisa=3, pantalón=3). Equivalencias 1:N. Sistemas compartibles entre brands (M:N). Creación on-demand. Siempre editable. |

---

## FASE 0 — Motor Dimensional de Plataforma (ARQUITECTURA)

### S18-01: Subsistema de tallas/dimensiones — 5 modelos + tabla puente + data migration

**Ubicación:** `apps/sizing/` (app nueva — servicio de plataforma, no dentro de catalog/ ni brands/)

**Insight arquitectónico:** El motor de tallas NO pertenece a ningún brand. Es un **servicio de plataforma** que cualquier brand consume. Si mañana entra Tecmater y usa el mismo sistema numérico BR 33-48 que Marluvas, no crea uno nuevo — usa el existente.

Además, "talla" es un concepto que varía radicalmente por categoría de producto:
- **Calzado:** 1 dimensión (largo del pie) → S1, S2... o 33, 34...
- **Camisa:** 3 dimensiones (cuello, pecho, cintura) → "16 / 42 / 38"
- **Pantalón:** 3 dimensiones (largo, cintura, cadera) → "32 / 30 / 36"
- **Guantes:** 1 dimensión (circunferencia mano) → S, M, L, XL

El motor tiene que soportar **N dimensiones** por sistema. Una "talla" (SizeEntry) es una combinación de valores en esas dimensiones.

#### Modelo 1: SizeSystem (servicio de plataforma)

```python
class SizeSystem(models.Model):
    """
    Un sistema de tallas disponible en la plataforma.
    NO pertenece a un brand — es un recurso compartido.
    Cualquier brand puede usarlo vía BrandSizeSystemAssignment.

    Ej: 'BR_CALZADO_33_48', 'RW_S1_S6', 'CAMISA_FORMAL', 'PANTALON_JEANS'.
    Si Tecmater usa el mismo sistema BR 33-48 que Marluvas, ambos apuntan
    al mismo SizeSystem.
    """
    CATEGORY_CHOICES = [
        ('FOOTWEAR', 'Calzado'),
        ('SHIRT', 'Camisa'),
        ('PANTS', 'Pantalón'),
        ('GLOVES', 'Guantes'),
        ('GENERIC', 'Genérico'),
    ]

    code = models.CharField(max_length=50, unique=True,
        help_text="Código único global. Ej: 'BR_CALZADO_33_48', 'RW_S1_S6', 'CAMISA_FORMAL'")
    display_name = models.CharField(max_length=100,
        help_text="Nombre legible. Ej: 'Brasil Calzado 33-48', 'Rana Walk S1-S6'")
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='FOOTWEAR',
        help_text="Categoría de producto. Determina qué dimensiones son típicas, pero no restringe.")
    description = models.TextField(blank=True, default='',
        help_text="Descripción libre. Ej: 'Sistema numérico brasileño para calzado de seguridad industrial'")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['category', 'code']

    def __str__(self):
        return f"{self.display_name} ({self.category})"
```

**Reglas:**
- **Sin FK a Brand.** El sistema vive a nivel plataforma. Los brands se conectan vía `BrandSizeSystemAssignment`.
- `code` es `unique` global — no puede haber dos sistemas con el mismo código en toda la plataforma.
- `category` es informativo/sugerencia para UI (agrupar sistemas por tipo de producto). No restringe qué dimensiones se pueden definir.
- **Creación on-demand:** Si al configurar un producto no existe un sistema adecuado, el CEO crea uno nuevo. Queda disponible para cualquier brand.
- **Siempre editable.**

#### Modelo 2: SizeDimension (las N dimensiones de un sistema)

```python
class SizeDimension(models.Model):
    """
    Una dimensión medible dentro de un SizeSystem.

    Calzado tiene 1 dimensión: 'foot_length' (o simplemente 'size').
    Camisa tiene 3: 'neck', 'chest', 'waist'.
    Pantalón tiene 3: 'inseam', 'waist', 'hip'.

    El orden (display_order) define cómo se presenta: "16 / 42 / 38"
    es cuello / pecho / cintura en ese orden.
    """
    system = models.ForeignKey(SizeSystem, on_delete=models.CASCADE,
                               related_name='dimensions')
    code = models.CharField(max_length=30,
        help_text="Código de la dimensión. Ej: 'foot_length', 'neck', 'chest', 'waist', 'inseam'")
    display_name = models.CharField(max_length=50,
        help_text="Nombre visible. Ej: 'Largo pie', 'Cuello', 'Pecho', 'Cintura'")
    unit = models.CharField(max_length=10, blank=True, default='',
        help_text="Unidad de medida. Ej: 'cm', 'in', '' (vacío si es código abstracto como S1)")
    display_order = models.PositiveSmallIntegerField(default=1,
        help_text="Orden de visualización. 1=primera dimensión mostrada.")
    is_primary = models.BooleanField(default=True,
        help_text="Si True, es la dimensión principal del sistema. "
                  "Calzado: la única dimensión es primary. "
                  "Camisa: 'cuello' podría ser primary, 'pecho' y 'cintura' secondary.")

    class Meta:
        unique_together = [('system', 'code')]
        ordering = ['system', 'display_order']

    def __str__(self):
        unit_str = f" ({self.unit})" if self.unit else ""
        return f"{self.system.code}.{self.code}{unit_str}"
```

**Reglas:**
- Calzado: 1 SizeDimension (`code='size'`, `unit=''` porque son códigos abstractos).
- Camisa formal: 3 SizeDimensions (`neck`/`chest`/`waist`, `unit='in'` o `'cm'`).
- **display_order** define la presentación. "16 / 42 / 38" = neck(1) / chest(2) / waist(3).
- **is_primary** — la dimensión principal para mostrar en UIs compactas (solo 1 valor). Calzado: siempre la única. Ropa: depende del tipo.

#### Modelo 3: SizeEntry (una "talla" = combinación de valores dimensionales)

```python
class SizeEntry(models.Model):
    """
    Una talla individual dentro de un SizeSystem.
    Para calzado: es simple — S1, S2, 33, 34.
    Para ropa: es una combinación de dimensiones — "16/42/38" (cuello/pecho/cintura).

    El label es el identificador legible de la talla completa.
    Los valores dimensionales concretos viven en SizeEntryValue.
    """
    system = models.ForeignKey(SizeSystem, on_delete=models.CASCADE,
                               related_name='entries')
    label = models.CharField(max_length=30,
        help_text="Identificador legible de la talla. "
                  "Calzado: 'S1', '33', 'XL'. "
                  "Ropa: '16/42/38' o 'M' o lo que tenga sentido para el sistema.")
    display_order = models.PositiveSmallIntegerField(
        help_text="Orden de visualización. S1=1, S2=2... o 33=1, 34=2...")
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = [('system', 'label')]
        ordering = ['system', 'display_order']

    def __str__(self):
        return f"{self.system.code}:{self.label}"
```

**Regla:** `label` es el identificador visible. Para calzado es sencillo ("S3", "42"). Para ropa multidimensional el CEO decide el formato del label ("16/42/38" o "M" o "Slim-32" — es libre).

#### Modelo 4: SizeEntryValue (valor de cada dimensión por entry)

```python
class SizeEntryValue(models.Model):
    """
    El valor concreto de UNA dimensión para UNA talla.

    Para calzado (1 dimensión):
        SizeEntry 'S3' → SizeEntryValue(dimension='size', value='S3')

    Para camisa (3 dimensiones):
        SizeEntry '16/42/38' → 3 SizeEntryValues:
            (dimension='neck', value='16')
            (dimension='chest', value='42')
            (dimension='waist', value='38')
    """
    entry = models.ForeignKey(SizeEntry, on_delete=models.CASCADE,
                              related_name='dimension_values')
    dimension = models.ForeignKey(SizeDimension, on_delete=models.CASCADE,
                                  related_name='entry_values')
    value = models.CharField(max_length=20,
        help_text="Valor de esta dimensión para esta talla. Ej: '42', '16', 'S3'")

    class Meta:
        unique_together = [('entry', 'dimension')]
        ordering = ['dimension__display_order']

    def clean(self):
        """Validaciones de integridad que Django DB constraints no cubren."""
        from django.core.exceptions import ValidationError
        # V1: La dimensión debe pertenecer al mismo sistema que el entry
        if self.dimension.system_id != self.entry.system_id:
            raise ValidationError(
                f"Dimension '{self.dimension.code}' pertenece al sistema "
                f"'{self.dimension.system.code}', pero el entry '{self.entry.label}' "
                f"pertenece a '{self.entry.system.code}'. Cross-system no permitido."
            )

    def __str__(self):
        return f"{self.entry.label}.{self.dimension.code}={self.value}"
```

**Reglas de integridad:**
- `unique_together = [('entry', 'dimension')]` — cada entry tiene exactamente 1 valor por dimensión.
- **`clean()` valida cross-system:** una SizeEntryValue no puede asignar una dimensión de un sistema a un entry de otro sistema. Esto lo previene el unique_together parcialmente (mismo entry = mismo system), pero la validación explícita en `clean()` da error legible si se intenta vía admin o API.
- **Completitud dimensional:** No se fuerza a nivel de modelo (un entry puede estar "incompleto" temporalmente mientras se edita). Se valida vía **servicio transaccional** al marcar un SizeEntry como `is_active=True`:

```python
# En apps/sizing/services.py
def validate_entry_completeness(entry):
    """
    Verifica que un SizeEntry activo tenga exactamente un valor
    por cada dimensión de su sistema.
    """
    system_dims = set(entry.system.dimensions.values_list('id', flat=True))
    entry_dims = set(entry.dimension_values.values_list('dimension_id', flat=True))
    missing = system_dims - entry_dims
    extra = entry_dims - system_dims
    if missing:
        dim_codes = SizeDimension.objects.filter(id__in=missing).values_list('code', flat=True)
        raise ValidationError(f"Entry '{entry.label}' le faltan dimensiones: {list(dim_codes)}")
    if extra:
        raise ValidationError(f"Entry '{entry.label}' tiene dimensiones de otro sistema")
    return True
```

**Tests obligatorios:** "missing dimension" (entry con 2 de 3 dims → error al validar), "cross-system dimension" (dim de sistema A en entry de sistema B → error en clean()).

**Punto de invocación concreto:** `validate_entry_completeness()` se invoca en:
1. **Admin:** Override de `SizeEntryAdmin.save_model()` — si `is_active=True` al guardar, invocar validación. Si falla → el admin no guarda y muestra error.
2. **Serializer (futuro Sprint 19):** En el serializer de SizeEntry para la API, validar antes de setear `is_active=True`.
3. **Seed migration:** El seed crea entries con `is_active=True` solo después de crear todos los EntryValues — así la validación es redundante pero sirve como sanity check al final del seed.

#### Modelo 5: SizeEquivalence (mapeo a sistemas estándar — 1:N)

```python
class SizeEquivalence(models.Model):
    """
    Mapeo de un SizeEntry a un valor en un sistema de tallas estándar.

    RELACIÓN 1:N — Un SizeEntry puede tener MÚLTIPLES equivalencias en el
    MISMO sistema estándar. Ej: BR 42 puede equivaler a US Men 8.5 Y US Men 9.

    Para ropa, los standard_systems pueden ser diferentes: 'US_SHIRT', 'EU_SHIRT'.
    El campo standard_system es CharField libre (no choices hardcodeados) para
    permitir extensibilidad sin migraciones.
    """
    entry = models.ForeignKey(SizeEntry, on_delete=models.CASCADE,
                              related_name='equivalences')
    standard_system = models.CharField(max_length=30,
        help_text="Sistema estándar de destino. "
                  "Calzado: 'EU', 'US_MEN', 'US_WOMEN', 'UK_MEN', 'BR', 'CM'. "
                  "Ropa: 'US_SHIRT', 'EU_SHIRT', 'ALPHA' (S/M/L/XL). "
                  "Libre — no restringido por choices para permitir extensibilidad.")
    value = models.CharField(max_length=20,
        help_text="Valor individual. Ej: '42', '9', '27.0', 'M'. "
                  "Para mapeos 1:N crear múltiples registros.")
    display_order = models.PositiveSmallIntegerField(default=0,
        help_text="Orden dentro del mismo (entry, standard_system).")
    is_primary = models.BooleanField(default=True,
        help_text="Equivalencia principal para UIs compactas.")

    class Meta:
        unique_together = [('entry', 'standard_system', 'value')]
        ordering = ['entry__display_order', 'standard_system', 'display_order']

    def __str__(self):
        primary = ' ★' if self.is_primary else ''
        return f"{self.entry} → {self.standard_system}={self.value}{primary}"
```

**Reglas:**
- **1:N por diseño.** BR 42 → US Men 8.5 + US Men 9 como registros separados.
- **standard_system es CharField libre** (no choices). Calzado usa EU/US_MEN/BR/CM. Ropa puede usar US_SHIRT/EU_SHIRT/ALPHA. No requiere migración para agregar un sistema estándar nuevo.
- **unique_together = [('entry', 'standard_system', 'value')]** — evita duplicados exactos.
- **is_primary** — para UIs compactas que solo muestran 1 equivalencia por sistema.

#### Tabla puente: BrandSizeSystemAssignment (brand ↔ sistema)

```python
class BrandSizeSystemAssignment(models.Model):
    """
    Asigna un SizeSystem a un Brand.
    Un brand puede usar MÚLTIPLES sistemas (ej: Marluvas usa
    'BR_CALZADO_33_48' para industrial y 'BR_CALZADO_35_44' para cleanroom).
    Un sistema puede ser usado por MÚLTIPLES brands (ej: Tecmater y Marluvas
    ambos usan 'BR_CALZADO_33_48').

    Relación M:N con metadata.
    """
    brand = models.ForeignKey('brands.Brand', on_delete=models.CASCADE,
                              related_name='size_system_assignments')
    size_system = models.ForeignKey(SizeSystem, on_delete=models.CASCADE,
                                    related_name='brand_assignments')
    is_default = models.BooleanField(default=False,
        help_text="Hint de UI: cuál sistema pre-seleccionar al crear producto para este brand. "
                  "Puede haber 0 o 1 default por brand — no se valida, es solo sugerencia.")
    assigned_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True, default='')

    class Meta:
        unique_together = [('brand', 'size_system')]
        ordering = ['brand', 'size_system']

    def __str__(self):
        default = ' [default]' if self.is_default else ''
        return f"{self.brand.name} → {self.size_system.display_name}{default}"
```

**Reglas:**
- **M:N.** Un brand usa N sistemas. Un sistema sirve a N brands.
- `is_default` es hint de UI — no restricción. Puede haber 0 defaults (el usuario siempre elige manualmente).
- **Creación on-demand del assignment:** Cuando un brand necesita un sistema nuevo, primero se crea el SizeSystem (si no existe), luego se crea el assignment.

#### Ejemplo: Cómo se ve en la práctica

**Calzado Rana Walk (1 dimensión):**
```
SizeSystem: code='RW_S1_S6', category='FOOTWEAR'
  └─ SizeDimension: code='size', display_name='Talla', unit='', is_primary=True
  └─ SizeEntry: label='S1', display_order=1
       └─ SizeEntryValue: dimension=size, value='S1'
       └─ SizeEquivalence: standard_system='EU', value='35', is_primary=True
       └─ SizeEquivalence: standard_system='EU', value='36', is_primary=False
       └─ SizeEquivalence: standard_system='US_MEN', value='3.5', is_primary=True
       └─ SizeEquivalence: standard_system='US_MEN', value='4', is_primary=False
       └─ ...
  └─ SizeEntry: label='S2', display_order=2
       └─ ...

BrandSizeSystemAssignment: brand=rana_walk → size_system=RW_S1_S6, is_default=True
```

**Calzado Marluvas (1 dimensión, compartible con Tecmater):**
```
SizeSystem: code='BR_CALZADO_33_48', category='FOOTWEAR'
  └─ SizeDimension: code='size', display_name='Talla BR', unit='', is_primary=True
  └─ SizeEntry: label='33', display_order=1
       └─ SizeEntryValue: dimension=size, value='33'
       └─ SizeEquivalence: standard_system='EU', value='35', is_primary=True
       └─ SizeEquivalence: standard_system='US_MEN', value='3.5', is_primary=True
       └─ ...
  └─ SizeEntry: label='42', display_order=10
       └─ SizeEntryValue: dimension=size, value='42'
       └─ SizeEquivalence: standard_system='US_MEN', value='8.5', is_primary=True
       └─ SizeEquivalence: standard_system='US_MEN', value='9', is_primary=False
       └─ ...

BrandSizeSystemAssignment: brand=marluvas → size_system=BR_CALZADO_33_48, is_default=True
BrandSizeSystemAssignment: brand=tecmater → size_system=BR_CALZADO_33_48, is_default=True
```

**Camisa formal (3 dimensiones — ejemplo futuro):**
```
SizeSystem: code='CAMISA_FORMAL_IN', category='SHIRT'
  └─ SizeDimension: code='neck', display_name='Cuello', unit='in', display_order=1, is_primary=True
  └─ SizeDimension: code='chest', display_name='Pecho', unit='in', display_order=2
  └─ SizeDimension: code='waist', display_name='Cintura', unit='in', display_order=3
  └─ SizeEntry: label='16/42/38', display_order=5
       └─ SizeEntryValue: dimension=neck, value='16'
       └─ SizeEntryValue: dimension=chest, value='42'
       └─ SizeEntryValue: dimension=waist, value='38'
       └─ SizeEquivalence: standard_system='ALPHA', value='L', is_primary=True
       └─ SizeEquivalence: standard_system='EU_SHIRT', value='41', is_primary=True
```

#### Data migration: Seed RW + Marluvas (calzado)

**En la misma migración**, crear los sistemas de calzado:

**Sistema 1: Rana Walk S1-S6**
- 1 SizeSystem (`RW_S1_S6`, category=FOOTWEAR)
- 1 SizeDimension (`size`)
- 6 SizeEntry (S1 a S6)
- 6 SizeEntryValue (1 por entry, dimensión única)
- ~72 SizeEquivalence (6 entries × ~6 standard_systems × ~2 valores promedio por 1:N)
- 1 BrandSizeSystemAssignment (rana_walk → RW_S1_S6, is_default=True)

**Sistema 2: Brasil Calzado 33-48 (Marluvas + futuro Tecmater)**
- 1 SizeSystem (`BR_CALZADO_33_48`, category=FOOTWEAR)
- 1 SizeDimension (`size`)
- 16 SizeEntry (33 a 48)
- 16 SizeEntryValue (1 por entry)
- ~88 SizeEquivalence (16 entries × ~5 standard_systems × ~1.1 promedio)
- 1 BrandSizeSystemAssignment (marluvas → BR_CALZADO_33_48, is_default=True)

**Nota:** Los valores de equivalencia provienen de ENT_MERCADO_TALLAS. El seed los hardcodea. Todo es editable post-migración vía admin.

**Regla de migración:**
```python
def seed_size_systems(apps, schema_editor):
    SizeSystem = apps.get_model('sizing', 'SizeSystem')
    SizeDimension = apps.get_model('sizing', 'SizeDimension')
    SizeEntry = apps.get_model('sizing', 'SizeEntry')
    SizeEntryValue = apps.get_model('sizing', 'SizeEntryValue')
    SizeEquivalence = apps.get_model('sizing', 'SizeEquivalence')
    BrandSizeSystemAssignment = apps.get_model('sizing', 'BrandSizeSystemAssignment')
    Brand = apps.get_model('brands', 'Brand')

    # 1. Crear sistemas de plataforma (idempotente via get_or_create por code)
    rw_sys, _ = SizeSystem.objects.get_or_create(
        code='RW_S1_S6',
        defaults={'display_name': 'Rana Walk S1-S6', 'category': 'FOOTWEAR'})
    br_sys, _ = SizeSystem.objects.get_or_create(
        code='BR_CALZADO_33_48',
        defaults={'display_name': 'Brasil Calzado 33-48', 'category': 'FOOTWEAR'})

    # 2. Dimensiones (idempotente via get_or_create por system+code)
    rw_dim, _ = SizeDimension.objects.get_or_create(
        system=rw_sys, code='size',
        defaults={'display_name': 'Talla', 'unit': '', 'display_order': 1, 'is_primary': True})
    br_dim, _ = SizeDimension.objects.get_or_create(
        system=br_sys, code='size',
        defaults={'display_name': 'Talla BR', 'unit': '', 'display_order': 1, 'is_primary': True})

    # 3. Entries + EntryValues + Equivalences (idempotente via get_or_create)
    # Patrón concreto — ejemplo con RW S1:
    RW_SIZES = [
        {'label': 'S1', 'order': 1, 'equivs': [
            ('EU', '35', True), ('EU', '36', False),
            ('US_MEN', '3.5', True), ('US_MEN', '4', False),
            ('US_WOMEN', '5', True), ('US_WOMEN', '5.5', False),
            ('UK_MEN', '2.5', True), ('UK_MEN', '3', False),
            ('BR', '33', True), ('BR', '34', False),
            ('CM', '218', True), ('CM', '225', False),
        ]},
        # ... S2 a S6 con el mismo patrón
    ]
    for sz in RW_SIZES:
        entry, _ = SizeEntry.objects.get_or_create(
            system=rw_sys, label=sz['label'],
            defaults={'display_order': sz['order']})
        SizeEntryValue.objects.get_or_create(
            entry=entry, dimension=rw_dim,
            defaults={'value': sz['label']})
        for std_sys, val, primary in sz['equivs']:
            SizeEquivalence.objects.get_or_create(
                entry=entry, standard_system=std_sys, value=val,
                defaults={'is_primary': primary, 'display_order': 0})

    # Marluvas: mismo patrón con BR_SIZES = [{'label': '33', ...}, ...]
    # (datos completos según ENT_MERCADO_TALLAS)

    # 4. Asignar a brands (con error controlado si brand no existe)
    try:
        rw_brand = Brand.objects.get(code='rana_walk')
        BrandSizeSystemAssignment.objects.get_or_create(
            brand=rw_brand, size_system=rw_sys,
            defaults={'is_default': True})
    except Brand.DoesNotExist:
        pass  # Brand no existe aún — assignment se crea cuando se registre

    try:
        mar_brand = Brand.objects.get(code='marluvas')
        BrandSizeSystemAssignment.objects.get_or_create(
            brand=mar_brand, size_system=br_sys,
            defaults={'is_default': True})
    except Brand.DoesNotExist:
        pass  # Brand no existe aún — assignment se crea cuando se registre

def reverse_seed(apps, schema_editor):
    SizeSystem = apps.get_model('sizing', 'SizeSystem')
    SizeSystem.objects.filter(code__in=['RW_S1_S6', 'BR_CALZADO_33_48']).delete()
    # CASCADE elimina dimensions, entries, values, equivalences, assignments
```

**Regla idempotencia:** Todo el seed usa `get_or_create()` con clave natural por entidad. Re-ejecutar la migración en una base parcialmente sembrada no rompe. Los brands se asignan con `try/except Brand.DoesNotExist` — si el brand no se ha creado aún, el assignment se hace manualmente vía admin.

**Verificación post-migración:**
- `SizeSystem.objects.count() == 2`
- RW: 6 SizeEntry, 6 SizeEntryValue, ~72 SizeEquivalence
- BR: 16 SizeEntry, 16 SizeEntryValue, ~88 SizeEquivalence
- `BrandSizeSystemAssignment.objects.count() == 2`
- Cada SizeEntry tiene al menos 1 SizeEquivalence con `is_primary=True` por standard_system

**Criterio DONE S18-01:**
- [ ] App `sizing/` creada con 6 modelos (SizeSystem, SizeDimension, SizeEntry, SizeEntryValue, SizeEquivalence, BrandSizeSystemAssignment)
- [ ] Registrados en admin con inlines (Dimension inline en System, Entry inline en System, EntryValue inline en Entry, Equivalence inline en Entry)
- [ ] Data migration idempotente con seed RW + Marluvas
- [ ] `SizeSystem.objects.count() == 2` post-migración
- [ ] Equivalencias 1:N funcionales (BR42→US8.5 + BR42→US9 ambos válidos)
- [ ] standard_system es CharField libre (no choices hardcodeados)
- [ ] Multidimensional funcional: crear sistema con 3 dimensiones y entries con 3 valores → funciona
- [ ] Brand assignment M:N funcional (asignar mismo sistema a 2 brands → funciona)
- [ ] Todo editable vía admin en cualquier momento
- [ ] Tests: unique_together por modelo, cascade delete, 1:N equivalences, multidimensional entries, M:N brand assignment, crear sistema on-demand

---

### S18-02: FK nullable `brand_sku` en ExpedienteProductLine

**Ubicación:** `apps/expedientes/models.py` → class ExpedienteProductLine

**Cambio:** Agregar campo FK nullable a BrandSKU:
```python
brand_sku = models.ForeignKey(
    'brands.BrandSKU', on_delete=models.SET_NULL,
    null=True, blank=True, related_name='expediente_lines',
    help_text="SKU específico con talla. Nullable para backward compat con líneas creadas pre-S18."
)
```

**Justificación Agent-A:** EPL tiene FK a ProductMaster pero sin talla. Sin BrandSKU no se puede: pedir al fabricante con talla, validar MOQ, generar packing list, ni mostrar selector de tallas en frontend.

**Backward compatible:** Las líneas existentes (pre-S18) quedan con `brand_sku=null`. Nuevas líneas creadas desde S18 en adelante deberían incluir brand_sku. La validación de "brand_sku requerido" se activa en S19 (frontend) — no en este sprint para no romper C1.

**Propiedad derivada (helper, no campo):**
```python
@property
def size_display(self):
    """Retorna la talla legible. Ej: 'S3' o '42'."""
    if self.brand_sku and self.brand_sku.size:
        return self.brand_sku.size
    return '—'
```

**Criterio DONE S18-02:**
- [ ] FK nullable agregada
- [ ] Migración aditiva (solo AddField)
- [ ] Líneas existentes no afectadas (brand_sku=null)
- [ ] `size_display` property funciona con y sin brand_sku
- [ ] Test: crear EPL sin brand_sku → OK. Crear con brand_sku → OK. Acceder size_display en ambos casos.

---

### S18-03: Fix bug `valid_to=null` en `resolve_client_price()`

**Ubicación:** `apps/pricing/services.py` → función `resolve_client_price()`

**Estructura del modelo PriceList:** Campos separados `valid_from` (DateField) y `valid_to` (DateField, nullable). `valid_to=null` = vigente indefinidamente.

**Bug:** El query actual excluye pricelists con `valid_to=null`.

**Grep previo obligatorio (antes de tocar código):**
```bash
grep -n "valid_" apps/pricing/models.py | head -10
# Verificar: ¿son campos separados (valid_from, valid_to) o DateRangeField?
# Este LOTE asume campos separados. Si grep muestra DateRangeField → escalar al arquitecto.
```

**Fix (asumiendo campos separados — verificado con grep):**
```python
from django.db.models import Q

pricelists = PriceList.objects.filter(
    Q(valid_from__lte=today),
    Q(valid_to__isnull=True) | Q(valid_to__gte=today),
    ...
)
```

**Criterio DONE S18-03:**
- [ ] Grep previo ejecutado — confirma campos separados
- [ ] Query corregida
- [ ] Test: PriceList con valid_to=null → se encuentra
- [ ] Test: PriceList con valid_to=mañana → se encuentra
- [ ] Test: PriceList con valid_to=ayer → NO se encuentra
- [ ] Tests existentes de pricing siguen verdes

---

### S18-04: Campos nullable adelantados en EPL + ExpedientePago

**Ubicación:** `apps/expedientes/models.py`, `apps/pricing/models.py`

| Campo | Modelo | Tipo | Justificación |
|-------|--------|------|---------------|
| `pricelist_used` | ExpedienteProductLine | FK nullable → PriceList | Trazabilidad: qué pricelist resolvió este precio (Agent-A H7) |
| `base_price` | ExpedienteProductLine | Decimal(10,2) nullable | Precio base antes de ajustes — snapshot al crear línea |
| `moq_per_size` | PriceListItem | PositiveIntegerField nullable | MOQ por talla individual (Agent-A H4) |
| `credit_status` | ExpedientePago | CharField(20) nullable, choices | Estado del pago: PENDING/CONFIRMED/REJECTED. Separado de liberación de crédito. |
| `credit_released` | Expediente | BooleanField default=False | Flag independiente: True cuando el crédito fue liberado (pago completo confirmado). NO es un valor de payment_status — es estado del expediente. |
| `incoterms` | Expediente | CharField(3) nullable, choices=['EXW','FOB','CIF','DDP'] | Condiciones de entrega por expediente |

**Separación payment_status vs credit_released (Fix auditoría R1+R4):**
- `credit_status` en ExpedientePago = estado del pago individual: `PENDING` (registrado), `CONFIRMED` (verificado por CEO), `REJECTED` (rechazado).
- `credit_released` en Expediente = flag booleano calculado exclusivamente por `recalculate_expediente_credit()` (S18-15). Nadie más lo setea. Es consecuencia del recálculo, no causa.
- `recalculate_expediente_credit()` (S18-15) suma pagos con `credit_status='CONFIRMED'`, calcula exposure, y setea `credit_released` bidireccionalmente (`<=0 → True`, `>0 → False`).
- S18-16 **no setea `credit_released`** — solo sincroniza `CreditExposure` del cliente y registra `EventLog` cuando el flag cambia de valor post-recálculo.

```python
PAYMENT_STATUS_CHOICES = [
    ('PENDING', 'Pendiente'),
    ('CONFIRMED', 'Confirmado'),
    ('REJECTED', 'Rechazado'),
]
```

**Criterio DONE S18-04:**
- [ ] 6 campos agregados: 5 nullable (pricelist_used, base_price, moq_per_size, credit_status, incoterms) + 1 con default (credit_released BooleanField default=False) — migración aditiva
- [ ] Tests: campos nullable aceptan null y valor válido, choices rechazan valor inválido, credit_released default=False

---

### S18-05: Hook `post_command_hooks` en dispatcher

**Ubicación:** `apps/expedientes/services/dispatcher.py` (o equivalente)

**Cambio (5 líneas):**
```python
# En el dispatcher, después de ejecutar un command exitosamente:
post_command_hooks = []  # Módulo-level list

def dispatch_command(expediente, command_code, user, **kwargs):
    # ... lógica existente de dispatch ...
    result = handler(expediente, user, **kwargs)

    # NUEVO: invocar hooks post-éxito
    for hook in post_command_hooks:
        hook(expediente=expediente, command_code=command_code,
             user=user, result=result)

    return result
```

**Uso futuro (Sprint 20):** `post_command_hooks.append(send_notification_on_state_change)` — sin tocar el dispatcher nunca más.

**Criterio DONE S18-05:**
- [ ] Lista `post_command_hooks` declarada
- [ ] Hooks invocados después de éxito del command
- [ ] Hooks NO invocados si el command falla (excepción)
- [ ] Test: registrar hook mock → ejecutar command → hook invocado con args correctos
- [ ] Test: command falla → hook NO invocado

---

## FASE 1 — Endpoints Backend

### S18-06: Serializers actualizados

**Ubicación:** `apps/expedientes/serializers.py`

**Serializers nuevos/actualizados:**

1. **ProductLineSerializer** — Incluye `brand_sku` (ID + nested read), `size_display`, `pricelist_used`, `base_price`
2. **FactoryOrderSerializer** — CRUD completo. Read: nested con product_lines count.
3. **PagoSerializer** — POST create + read. Incluye `credit_status` (PENDING/CONFIRMED/REJECTED por pago individual).
4. **BundleSerializer (actualizado)** — Detalle expediente. Campos exactos (ref S18-14): `product_lines[]` (con brand_sku, size_display, base_price, pricelist_used), `factory_orders[]` (con status, factory_order_number, product_lines count), `pagos[]` (con amount, payment_date, credit_status), `credit_released` (BooleanField), `credit_exposure` (Decimal), `merged_with`, `split_from`, `incoterms`.
5. **SizeSystemSerializer** — Read-only para selector de tallas en frontend (nested: dimensions → entries → equivalences). Filtrado por brand vía BrandSizeSystemAssignment.

**Regla serializer portal (S17 lección):** Campos con prefijo `internal_` o `ceo_` se excluyen automáticamente del serializer portal. No hardcodear lista de exclusión.

**Criterio DONE S18-06:**
- [ ] 5 serializers nuevos/actualizados
- [ ] BundleSerializer expone exactamente: `credit_released`, `credit_exposure`, `merged_with`, `split_from`, `incoterms` (NO `credit_status` a nivel expediente — eso es por pago)
- [ ] Portal serializer excluye campos internal_/ceo_ automáticamente
- [ ] Tests: serialización correcta con y sin brand_sku, bundle incluye credit_released y credit_exposure

---

### S18-07: 5 endpoints PATCH por estado

**Ubicación:** `apps/expedientes/views.py`

**Alineación con state machine FROZEN (ENT_OPS_STATE_MACHINE v1.2.2):**
Los 8 estados de la máquina congelada son: REGISTRO → PI_SOLICITADA → CONFIRMADO → PRODUCCION → PREPARACION → DESPACHO → TRANSITO → EN_DESTINO. Los PATCH cubren los 5 estados donde hay campos operativos editables post-transición:

| Endpoint | Estado FROZEN | Campos editables | Validación |
|----------|--------------|-----------------|------------|
| PATCH `/expedientes/{id}/confirmado/` | CONFIRMADO | product_lines, currency, incoterms, notes | operado_por required |
| PATCH `/expedientes/{id}/preparacion/` | PREPARACION | product_lines (modified), estimated_production_date | solo si estado==PREPARACION |
| PATCH `/expedientes/{id}/produccion/` | PRODUCCION | factory_orders (nested), production_status, quality_notes | solo si estado==PRODUCCION |
| PATCH `/expedientes/{id}/despacho/` | DESPACHO | shipping_date, tracking_url, dispatch_notes, weight_kg, packages_count | solo si estado==DESPACHO |
| PATCH `/expedientes/{id}/transito/` | TRANSITO | estimated_arrival, customs_status, transit_notes | solo si estado==TRANSITO |

**Estados sin PATCH (y por qué):**
- REGISTRO: se crea vía C1 (CreateExpediente), no se edita inline.
- PI_SOLICITADA: la proforma se gestiona como artefacto (ART-02), no como PATCH de campos.
- EN_DESTINO: estado terminal de llegada — campos se capturan en el command de transición, no post-hoc.

**Canon `factory_order_number` (Fix auditoría R1+R2):** El campo flat `factory_order_number` en el modelo Expediente es **read-only derivado**. Su valor se sincroniza automáticamente desde la **FactoryOrder principal**, definida como: la FactoryOrder activa con menor `id` (la primera creada). Regla determinista, sin ambigüedad. No aparece como editable en ningún PATCH. Si se necesita cambiar, se edita la FactoryOrder vía CRUD (S18-08) y el campo flat se actualiza en el viewset (no en save()). Si no hay FactoryOrders → `factory_order_number = null`.

**Regla:** Cada PATCH valida que `expediente.current_status == estado_esperado`. Si no matchea → 409 Conflict. Validación `operado_por` según DEC-EXP-05.

**Regla tenant:** Todos usan `ClientScopedManager.for_user(request.user)` — nunca `.all()`.

**Criterio DONE S18-07:**
- [ ] 5 endpoints funcionales (CONFIRMADO, PREPARACION, PRODUCCION, DESPACHO, TRANSITO)
- [ ] Cada uno valida estado correcto (409 si no)
- [ ] Tenant isolation (404 uniforme si no es del usuario)
- [ ] Tests: PATCH en estado correcto → 200. PATCH en estado incorrecto → 409. PATCH de otro tenant → 404.

---

### S18-08: CRUD FactoryOrder

**Ubicación:** `apps/expedientes/views.py`

| Método | Endpoint | Lógica |
|--------|----------|--------|
| GET | `/expedientes/{id}/factory-orders/` | Lista órdenes del expediente |
| POST | `/expedientes/{id}/factory-orders/` | Crea orden. Valida FK a expediente. auto-genera `factory_order_number` si no viene. |
| PATCH | `/expedientes/{id}/factory-orders/{fk_id}/` | Edita orden. Solo campos no-readonly. |
| DELETE | `/expedientes/{id}/factory-orders/{fk_id}/` | Soft-delete o hard-delete (según política). Solo si no tiene líneas de producción completadas. |

**factory_order_number:** Si no viene en POST, auto-generar con patrón `FO-{expediente.code}-{seq:03d}`. Si viene, respetar el valor del usuario (genérico, multi-fabricante — DEC-EXP-01).

**Regla determinismo FactoryOrder.save()** (lección S17 v1.1 H3): El `save()` no debe tener side-effects ocultos. Si se necesita recalcular algo al guardar, hacerlo explícito en el viewset, no en el model.

**Sincronización del flat field (obligatoria en POST/PATCH/DELETE):**
Después de cada operación exitosa en el viewset, ejecutar:
```python
def sync_factory_order_number(expediente):
    """Sincroniza el campo flat con la FactoryOrder principal (menor ID activa)."""
    principal = expediente.factory_orders.filter(
        is_active=True  # o el campo equivalente
    ).order_by('id').first()
    expediente.factory_order_number = principal.factory_order_number if principal else None
    expediente.save(update_fields=['factory_order_number'])
```
Invocar en: `create()`, `partial_update()`, `destroy()` del viewset. No en model `save()`.

**Criterio DONE S18-08:**
- [ ] 4 métodos funcionales (GET/POST/PATCH/DELETE)
- [ ] auto-gen factory_order_number
- [ ] DELETE validado (no eliminar si hay producción completada)
- [ ] `sync_factory_order_number()` invocado en POST, PATCH y DELETE
- [ ] Tests: CRUD completo + validación delete + **sync tests: POST primera orden → flat = su number; POST segunda orden → flat sigue siendo la primera; DELETE primera → flat cambia a segunda; DELETE última → flat = null**

---

### S18-09: POST pagos + integración C21/PaymentLine

**Ubicación:** `apps/expedientes/views.py`

**Endpoint:** POST `/expedientes/{id}/pagos/`

**Payload:**
```json
{
  "amount": 15000.00,
  "currency": "USD",
  "payment_date": "2026-04-15",
  "payment_method": "wire_transfer",
  "reference": "TRF-2026-0042",
  "notes": "Pago parcial producción"
}
```

**Lógica:**
1. Crear ExpedientePago con `credit_status='PENDING'`
2. Si existe integración con C21/PaymentLine → crear PaymentLine correspondiente
3. Retornar pago creado con status PENDING

**Ruta de confirmación (acción separada):**
El auto-release NO ocurre al registrar el pago. El flujo completo es:
1. POST `/expedientes/{id}/pagos/` → crea pago PENDING (este endpoint)
2. PATCH `/expedientes/{id}/pagos/{pago_id}/confirmar/` → cambia a CONFIRMED + invoca `recalculate_expediente_credit()` (S18-15 calcula exposure + credit_released) + S18-16 sincroniza CreditExposure si flag cambió

Esto es determinista: un pago recién registrado nunca libera crédito. Solo un pago explícitamente confirmado por el CEO puede hacerlo.

**Regla determinismo ExpedientePago.view** (lección S17 v1.1 H3): La vista es atómica — `select_for_update` en el expediente para evitar race conditions en recálculo de crédito.

**Criterio DONE S18-09:**
- [ ] POST `/pagos/` crea pago PENDING (nunca CONFIRMED directo)
- [ ] PATCH `/pagos/{id}/confirmar/` cambia a CONFIRMED + recálculo + sync CreditExposure
- [ ] Tests: POST → pago PENDING, confirmar → CONFIRMED + recálculo, confirmar último pago → credit_released=True si exposure<=0

---

### S18-10: POST merge (unir expedientes)

**Ubicación:** `apps/expedientes/views.py`

**Endpoint:** POST `/expedientes/{id}/merge/`

**Payload:**
```json
{
  "follower_ids": [42, 43],
  "notes": "Consolidar embarque abril"
}
```

**Lógica:**
1. `select_for_update` en master + followers (orden por ID para evitar deadlocks)
2. Validar que todos están en estado **REGISTRO, PI_SOLICITADA o CONFIRMADO** (únicos estados pre-producción donde merge tiene sentido — ref state machine FROZEN). Expedientes en PRODUCCION+ no son mergeables.
3. Mover product_lines de followers al master
4. Marcar followers como `merged_into = master.id`
5. Cancelar followers vía `c_cancel` (command existente de la state machine FROZEN que ya maneja credit release). No inventar estado "CERRADO" — usar el mecanismo de cancelación existente.
6. Recalcular crédito del master
7. EventLog con event_type='merge' en master y cada follower

**Regla CEO:** El master_id es el expediente sobre el que se hace el POST (DEC-EXP-02).

**Criterio DONE S18-10:**
- [ ] Merge funcional con N followers
- [ ] select_for_update sin race conditions
- [ ] Product lines movidas correctamente
- [ ] Crédito recalculado post-merge
- [ ] EventLog en todos los expedientes involucrados
- [ ] Tests: merge 2 expedientes, merge 3, merge con estado incompatible → error

---

### S18-11: POST separate-products (separar líneas)

**Ubicación:** `apps/expedientes/views.py`

**Endpoint:** POST `/expedientes/{id}/separate-products/`

**Payload:**
```json
{
  "product_line_ids": [101, 102],
  "notes": "Separar productos para embarque distinto"
}
```

**Lógica:**
1. Validar que las líneas pertenecen al expediente
2. Crear nuevo expediente heredando metadata del original (client, brand, currency, etc.)
3. Mover líneas seleccionadas al nuevo expediente
4. Recalcular crédito en ambos expedientes
5. Registrar relación `split_from = original.id` en el nuevo
6. EventLog en ambos

**Regla:** Si todas las líneas se separan → error (no dejar expediente vacío).

**Criterio DONE S18-11:**
- [ ] Separación funcional
- [ ] Nuevo expediente hereda metadata correcta
- [ ] No permite separar TODAS las líneas
- [ ] Crédito recalculado en ambos
- [ ] Tests: separar 2 de 5 líneas, intentar separar todas → error

---

### S18-12: DELETE url-orden-compra

**Ubicación:** `apps/expedientes/views.py`

**Endpoint:** DELETE `/expedientes/{id}/purchase-order-url/`

**Lógica:** Setear `purchase_order_url = null` en el expediente. EventLog.

**Criterio DONE S18-12:**
- [ ] Endpoint funcional
- [ ] EventLog registra la eliminación
- [ ] Test: DELETE → campo en null, EventLog creado

---

### S18-13: Actualizar C1 (CreateExpediente)

**Ubicación:** `apps/expedientes/services/commands/handle_c1.py` (o equivalente)

**Cambios:**
1. Aceptar `product_lines` con `brand_sku` FK (opcional, backward compat)
2. Aceptar `incoterms`, `purchase_order_number` como campos nuevos
3. Si `brand_sku` viene en una línea → auto-resolver `base_price` via `resolve_client_price()` y guardar snapshot en `pricelist_used` + `base_price`
4. `credit_check` de S16 sigue funcionando (no romper)

**Backward compat:** POST sin campos nuevos → funciona igual que antes. Campos nuevos son todos opcionales.

**Criterio DONE S18-13:**
- [ ] C1 acepta product_lines con brand_sku
- [ ] Auto-resolución de precio al crear línea con brand_sku
- [ ] credit_check no se rompe
- [ ] Test: C1 viejo (sin campos nuevos) → OK. C1 nuevo (con brand_sku + incoterms) → OK. C1 con brand_sku + pricing → snapshot correcto.

---

### S18-14: Bundle detalle actualizado

**Ubicación:** `apps/expedientes/views.py` → endpoint GET detalle

**Agregar al response:**
- `product_lines[]` — con brand_sku, size_display, base_price, pricelist_used
- `factory_orders[]` — con status, factory_order_number, product_lines count
- `pagos[]` — con amount, payment_date, credit_status (PENDING/CONFIRMED/REJECTED por pago)
- `credit_released` — BooleanField del expediente (True si pagos CONFIRMED cubren total)
- `credit_exposure` — Decimal: exposición actual del expediente (total líneas - pagos confirmados)
- `merged_with` — IDs de expedientes fusionados (si aplica)
- `split_from` — ID del expediente original (si aplica)
- `incoterms`

**Criterio DONE S18-14:**
- [ ] Todos los campos nuevos en response
- [ ] Product lines con talla visible
- [ ] Tests: detalle con y sin product_lines, con y sin merge

---

### S18-15: recalculate_expediente_credit

**Ubicación:** `apps/expedientes/services/credit.py` (o equivalente)

**Única fuente de verdad para `credit_exposure` y `credit_released`:**
```python
def recalculate_expediente_credit(expediente):
    """
    Snapshot + recálculo local (DEC-EXP-03).
    ÚNICA función que toca credit_exposure y credit_released.
    Maneja ambas ramas: activación Y reversión.
    """
    total_lines = sum(
        line.unit_price * line.quantity
        for line in expediente.product_lines.all()
    )
    total_paid = sum(
        pago.amount
        for pago in expediente.pagos.filter(credit_status='CONFIRMED')
    )
    expediente.credit_exposure = total_lines - total_paid

    # Bidireccional: activar Y revertir
    if expediente.credit_exposure <= 0:
        expediente.credit_released = True
    else:
        expediente.credit_released = False

    expediente.save(update_fields=['credit_exposure', 'credit_released'])
```

**Invocado desde:** S18-09 (post-confirmación pago), S18-10 (post-merge), S18-11 (post-split), S18-13 (post-C1 si tiene líneas).

**Regla:** Nadie más setea `credit_released` directamente. Solo esta función. Si un merge agrega líneas y la exposición vuelve a ser positiva, `credit_released` se revierte a `False` automáticamente.

**Criterio DONE S18-15:**
- [ ] Función idempotente y bidireccional
- [ ] Recálculo correcto con líneas + pagos
- [ ] `credit_released=True` cuando exposure <= 0
- [ ] `credit_released=False` cuando exposure > 0 (reversión)
- [ ] Tests: expediente sin pagos, con pago parcial, con pago completo, **regresión: pagado completo → merge sube exposure → credit_released vuelve a False**

---

### S18-16: Sincronización CreditExposure del cliente + EventLog

**Ubicación:** `apps/expedientes/services/credit.py`

**Contexto:** `recalculate_expediente_credit()` (S18-15) es la única función que setea `credit_released` y `credit_exposure` en el expediente. S18-16 se encarga del **efecto colateral** sobre el modelo CreditExposure del cliente (la exposición acumulada a nivel ClientSubsidiary × Brand):

**Lógica:** Invocado como paso adicional DESPUÉS de `recalculate_expediente_credit()`:
1. Si `expediente.credit_released` cambió de `False` a `True` → liberar reserva en CreditExposure del cliente + EventLog con event_type='credit'
2. Si `expediente.credit_released` cambió de `True` a `False` (reversión por merge/split que subió exposure) → re-reservar en CreditExposure del cliente + EventLog

**No confundir:** `credit_released` es flag del **expediente** (¿está pagado?). `credit_status` es estado del **pago individual** (¿fue confirmado?). CreditExposure es la **exposición acumulada del cliente** (suma de todos sus expedientes no liberados).

**Criterio DONE S18-16:**
- [ ] CreditExposure del cliente se actualiza cuando credit_released cambia en cualquier dirección
- [ ] EventLog registra activación y reversión
- [ ] Test: pago completo confirmado → credit_released=True + CreditExposure reducida
- [ ] Test: merge post-release sube exposure → credit_released=False + CreditExposure re-reservada

---

### S18-17: Refactorear resolve_client_price → chain-of-responsibility

**Ubicación:** `apps/pricing/services.py`

**Estado actual:** Función monolítica con if/elif. Difícil de extender para Sprint 22 (capa comercial).

**Refactor:** Patrón chain-of-responsibility:
```python
PRICE_RESOLVERS = [
    resolve_from_brand_client_pricelist,   # Precio específico cliente-marca
    resolve_from_brand_default_pricelist,   # Precio default de la marca
    resolve_from_product_master_base_price, # Precio base del producto
]

def resolve_client_price(brand, client_subsidiary, product_master, brand_sku=None, date=None):
    date = date or timezone.now().date()
    for resolver in PRICE_RESOLVERS:
        result = resolver(brand, client_subsidiary, product_master, brand_sku, date)
        if result is not None:
            return result  # PriceResult(price, source, pricelist_used)
    return None  # No price found
```

**Beneficio Sprint 22:** Agregar un resolver nuevo = `PRICE_RESOLVERS.insert(1, resolve_from_volume_discount)`. Sin tocar lógica existente.

**Criterio DONE S18-17:**
- [ ] Chain-of-responsibility funcional
- [ ] Cada resolver retorna `PriceResult(price, source, pricelist_used)` o None
- [ ] Tests existentes de pricing siguen verdes (misma lógica, nueva estructura)
- [ ] Test: resolver order matters (primero específico, luego default, luego base)

---

### S18-18: EventLog estandarizado

**Ubicación:** `apps/expedientes/models.py` → EventLog

**Cambios aditivos:**
```python
# Campos nuevos (nullable para backward compat)
event_type = models.CharField(max_length=30, null=True, blank=True,
    choices=[('state_change', 'Cambio de estado'), ('data_edit', 'Edición de datos'),
             ('merge', 'Fusión'), ('split', 'Separación'), ('payment', 'Pago'),
             ('credit', 'Crédito')])
previous_status = models.CharField(max_length=30, null=True, blank=True)
new_status = models.CharField(max_length=30, null=True, blank=True)
```

**Criterio DONE S18-18:**
- [ ] 3 campos aditivos
- [ ] Todos los commands existentes populan event_type='state_change' + previous_status + new_status
- [ ] PATCH endpoints populan event_type='data_edit'
- [ ] Merge/Split populan sus tipos respectivos
- [ ] Tests: verificar event_type correcto por tipo de operación

---

### S18-19: Tests completos Sprint 18

**Regla tests unificada (lección S17 v1.2):** Un solo archivo por fase con naming claro.

**Archivo:** `apps/sizing/tests/test_sizing_engine.py` + `apps/expedientes/tests/test_sprint18.py` + `apps/pricing/tests/test_pricing_fix.py`

**Cobertura obligatoria:**

| Área | Tests mínimos |
|------|---------------|
| Motor dimensional | unique_together por modelo, cascade delete, equivalencias 1:N, is_primary filter, multidimensional (crear sistema 3 dims + entries 3 valores), brand assignment M:N (mismo sistema a 2 brands), crear sistema on-demand, standard_system libre (no choices), **clean() cross-system dimension → ValidationError**, **validate_entry_completeness() missing dim → error**, **seed idempotente (re-run no rompe)** |
| brand_sku FK | Crear EPL sin/con brand_sku, size_display property |
| Pricing fix | valid_to=null encontrado, valid_to futuro encontrado, valid_to pasado excluido |
| Campos nullable | Cada campo acepta null y valor válido |
| Hook dispatcher | Hook invocado post-éxito, no invocado post-error |
| PATCH por estado | Estado correcto → 200, estado incorrecto → 409, otro tenant → 404 |
| CRUD FactoryOrder | GET/POST/PATCH/DELETE + validación delete |
| Pagos | Pago parcial, pago completo, confirmación → recálculo bidireccional credit_released |
| Merge | 2 expedientes, 3 expedientes, estado incompatible → error |
| Split | Separar parcial, intentar separar todo → error |
| C1 actualizado | Viejo sin campos → OK, nuevo con brand_sku → OK |
| Bundle detalle | Todos los campos nuevos presentes |
| recalculate_credit | Sin pagos, con pago parcial, con pago completo |
| Chain resolver | Orden de resolvers correcto, fallback funciona |
| EventLog | event_type correcto por tipo de operación |

**Criterio DONE S18-19:**
- [ ] Todos los tests arriba pasan
- [ ] `python manage.py test` verde (incluye tests de sprints anteriores)
- [ ] `bandit -ll backend/` sin high/critical

---

## Tanda de migraciones coordinada

**Django genera una migración por app.** Sprint 18 produce una tanda coordinada de migraciones (una por app afectada), aplicadas en un solo `migrate`:

```bash
# 1. Verificar estado limpio
python manage.py showmigrations

# 2. Generar migraciones (una por app)
python manage.py makemigrations sizing      # CreateModel ×6 + RunPython seed
python manage.py makemigrations expedientes  # AddField brand_sku, incoterms, event_type, previous_status, new_status
python manage.py makemigrations pricing      # AddField moq_per_size
python manage.py makemigrations clientes     # (si hay campos nuevos en ClientSubsidiary)

# 3. Verificar CADA migración generada — additive only
python manage.py sqlmigrate sizing 0001      # Solo CreateModel + RunPython
python manage.py sqlmigrate expedientes XXXX # Solo AddField
python manage.py sqlmigrate pricing XXXX     # Solo AddField
#    Esperado: CreateModel, AddField, RunPython
#    NO esperado: AlterField, RemoveField, RenameField
#    Si aparece algo NO esperado → PARAR y revisar

# 4. Aplicar toda la tanda
python manage.py migrate

# 5. Verificar
python manage.py check
python manage.py test
```

**Regla:** Cada app genera su propio archivo de migración. La tanda se aplica junta con un solo `migrate`. Si alguna migración individual no es additive-only, parar y revisar antes de aplicar.

**Rollback:** Reversible. Todos los campos son nullable o tienen default. `RemoveField` + `DeleteModel` para cada adición. `reverse_seed` para los datos.

---

## Dependencias internas Sprint 18

```
S18-01 (Motor dimensional) ──┐
S18-02 (brand_sku FK)  ──────┤
S18-03 (Fix pricing)  ───────┤
S18-04 (Campos nullable) ────┤──→ MIGRACIÓN ÚNICA ──→ S18-06 (Serializers)
S18-05 (Hook dispatcher) ────┘                              │
                                                   ┌────────┼────────────┐
                                                   │        │            │
                                              S18-07    S18-08       S18-09
                                              (PATCH)   (FactOrder)  (Pagos)
                                                   │        │            │
                                                   │   S18-10 (Merge)    │
                                                   │   S18-11 (Split)    │
                                                   │   S18-12 (DELETE)   │
                                                   │        │            │
                                                   └────────┼────────────┘
                                                            │
                                                   S18-13 (C1 actualizado)
                                                   S18-14 (Bundle detalle)
                                                   S18-15 (Recalc credit)
                                                   S18-16 (Auto release)
                                                   S18-17 (Chain resolver)
                                                   S18-18 (EventLog)
                                                            │
                                                   S18-19 (Tests)
```

---

## Checklist completa Sprint 18

### Fase 0 — Arquitectura + Fixes
- [ ] S18-01: Motor dimensional plataforma (app `sizing/`: SizeSystem + SizeDimension + SizeEntry + SizeEntryValue + SizeEquivalence + BrandSizeSystemAssignment + seed RW/Marluvas)
- [ ] S18-02: FK brand_sku en EPL
- [ ] S18-03: Fix valid_to=null en pricing
- [ ] S18-04: Campos nullable adelantados
- [ ] S18-05: Hook post_command_hooks en dispatcher

### Fase 1 — Endpoints
- [ ] S18-06: Serializers actualizados
- [ ] S18-07: 5 endpoints PATCH por estado
- [ ] S18-08: CRUD FactoryOrder
- [ ] S18-09: POST pagos + credit release
- [ ] S18-10: POST merge
- [ ] S18-11: POST separate-products
- [ ] S18-12: DELETE url-orden-compra
- [ ] S18-13: Actualizar C1
- [ ] S18-14: Bundle detalle
- [ ] S18-15: recalculate_expediente_credit
- [ ] S18-16: Sync CreditExposure + EventLog (post-recálculo S18-15)
- [ ] S18-17: Refactor resolve_client_price → chain
- [ ] S18-18: EventLog estandarizado
- [ ] S18-19: Tests completos

### CI/CD
- [ ] `python manage.py test` verde
- [ ] `bandit -ll backend/` sin high/critical
- [ ] `npm run lint && npm run typecheck` verde (cambios frontend mínimos)
- [ ] Conventional commits en todos los commits

---

## Excluido explícitamente de Sprint 18

| Feature | Razón | Cuándo |
|---------|-------|--------|
| Tab "Tallas" en Brand Console (frontend) | Sprint 19 S19-13 | Después de motor backend estable |
| Selector tallas al agregar línea | Sprint 19 S19-14 | Después de SizeSystem disponible en API |
| Formulario creación extendido frontend | Sprint 19 | Después de endpoints |
| Emails/notificaciones | Sprint 20 | Hook dispatcher listo, pero CEO-28 pendiente |
| Capa comercial (pricelists, rebates) | Sprint 22-23 | CEO-25 pendiente |
| Autogestión B2B | Sprint 24 | CEO-26 pendiente |
| Permisos granulares | Sprint 26 | Diferido por CEO |
| Sidebar role-based | Sprint 21 | Switch, no desarrollo |

---

## Criterio Sprint 18 DONE

### Obligatorio (bloquea Sprint 19)
1. Motor dimensional de plataforma funcional: app `sizing/`, 2+ sistemas seedeados (RW + BR calzado), assignments M:N, equivalencias 1:N, todo editable vía admin
2. EPL acepta brand_sku FK (nullable, backward compat)
3. resolve_client_price() funciona con valid_to=null
4. Hook post_command_hooks invoca hooks registrados
5. 5 endpoints PATCH por estado responden correctamente
6. CRUD FactoryOrder completo
7. Merge y Split funcionales con recálculo de crédito
8. C1 acepta campos nuevos sin romper backward compat
9. Bundle detalle incluye product_lines con talla + factory_orders + pagos
10. `python manage.py test` verde (0 failures, 0 errors)
11. `bandit -ll backend/` sin high/critical
12. `npm run lint && npm run typecheck` verde

### Deseable (no bloquea Sprint 19)
13. Chain-of-responsibility en pricing completamente refactoreado
14. EventLog con event_type en todas las operaciones
15. Admin con inlines para motor dimensional (SizeSystem → SizeDimension, SizeEntry → SizeEntryValue + SizeEquivalence)

---

## Lecciones de Sprint 17 aplicadas

1. **fk_name en inlines:** Si un modelo tiene múltiples FK al mismo modelo → siempre declarar `fk_name` en admin inlines.
2. **config/urls.py:** Verificar rutas después de agregar apps — rutas huérfanas no causan error hasta que se navegan.
3. **help_text:** Usar raw strings `r"..."` o escapar caracteres especiales.
4. **CI primero:** Sprint 18 incluye CI check (`bandit` + `npm typecheck`) como criterio DONE obligatorio, no deseable.
5. **Migración additive-only:** Verificar con `sqlmigrate` que solo hay `CreateModel` y `AddField`. Cualquier `AlterField` o `RemoveField` es señal de alerta.

---

Stamp: DRAFT v3.4 — Arquitecto (Claude Opus 4.6) — 2026-03-26
