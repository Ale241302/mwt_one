# PROMPT_ANTIGRAVITY_SPRINT18 — Motor Dimensional + Endpoints Backend
## Para: Claude Code (Antigravity) — AG-02 Backend
## Sprint: 18 · Fecha: 2026-03-26 · LOTE: v3.5 (auditado 9.6/10, 6 rondas ChatGPT)

---

## TU ROL

Eres AG-02 Backend Builder para el proyecto MWT.ONE.
Implementas los items de Sprint 18 en código Python/Django.
El CEO (Alejandro) te da contexto y aprueba. Vos escribís código, no tomás decisiones de negocio.

Sprint 18 tiene 2 fases: Fase 0 (motor dimensional + fixes) y Fase 1 (endpoints). NO avanzar a Fase 1 hasta que Fase 0 esté DONE con tests verdes y migración aplicada.

---

## CONTEXTO DEL PROYECTO

- **Stack:** Django 5.x + DRF + PostgreSQL 16 + Celery + Redis + MinIO + Docker Compose + Next.js 14 (App Router)
- **Repo:** `Ale241302/mwt_one`, branch `main`
- **Objetivo:** (A) Motor dimensional de plataforma — app `sizing/` con 6 modelos, seed RW + Marluvas. (B) Endpoints backend para toda la funcionalidad de Sprint 17 (product lines, factory orders, pagos, merge, split, pricing, crédito).
- **Prerequisito:** Sprint 17 DONE (14/14 items). Verificar que tests pasan antes de empezar.

### Estado real del código post-Sprint 17 (verificar antes de empezar):
- State machine 8 estados FROZEN: REGISTRO → PI_SOLICITADA → CONFIRMADO → PRODUCCION → PREPARACION → DESPACHO → TRANSITO → EN_DESTINO
- ExpedienteProductLine con FK a ProductMaster (sin talla ni BrandSKU)
- FactoryOrder, ExpedientePago funcionales
- ~30 campos operativos por estado
- Portal 3 endpoints con tenant isolation
- CreditPolicy + CreditExposure + CreditOverride funcionales
- ProductMaster 565 SKUs cargados

---

## HARD RULES — NUNCA VIOLAR

1. **ENT_OPS_STATE_MACHINE es FROZEN.** Los 8 estados canónicos son: REGISTRO, PI_SOLICITADA, CONFIRMADO, PRODUCCION, PREPARACION, DESPACHO, TRANSITO, EN_DESTINO. No inventar estados. No modificar transiciones.

2. **No inventar datos.** Si necesitas un valor de negocio, preguntá al CEO. Marcar como `# TODO: CEO_INPUT_REQUIRED`.

3. **No romper commands existentes.** C1-C16, C22, c_cancel, c_reopen deben seguir funcionando. Mismos inputs → mismos outputs.

4. **Migraciones additive only.** Solo CreateModel y AddField. Nunca ALTER destructivo, rename, ni DROP. Una tanda coordinada de migraciones (una por app), aplicadas con un solo `migrate`.

5. **No eliminar ni renombrar campos existentes.**

6. **No tocar infra.** docker-compose.yml, nginx/, settings de infra = prohibido.

7. **Tests antes y después.** Suite completa antes de empezar. Después de cada fase, mismos tests pasan. Tests nuevos en archivos separados.

8. **Conventional Commits.** `feat:`, `fix:`, `refactor:`, `test:`.

9. **credit_released lo setea SOLO recalculate_expediente_credit().** Nadie más. Ni views, ni commands, ni signals. Solo esa función. Bidireccional: <=0 → True, >0 → False.

10. **factory_order_number es read-only derivado.** Sincronizado por sync_factory_order_number() en el viewset, nunca en model save(). Principal = menor ID activa.

---

## ANTES DE ESCRIBIR UNA SOLA LÍNEA — VERIFICACIÓN OBLIGATORIA

```bash
# 1. Tests pasan
python manage.py test 2>&1 | tail -10

# 2. ¿ExpedienteProductLine existe?
grep "^class " apps/expedientes/models.py

# 3. ¿FactoryOrder y ExpedientePago existen?
grep -n "class FactoryOrder\|class ExpedientePago" apps/expedientes/models.py

# 4. ¿BrandSKU existe?
grep -rn "class BrandSKU" apps/brands/models.py

# 5. ¿Brand rana_walk y marluvas existen?
python manage.py shell -c "from apps.brands.models import Brand; print(Brand.objects.values_list('code', flat=True))"

# 6. ¿resolve_client_price existe?
grep -rn "def resolve_client_price" apps/pricing/

# 7. ¿PriceList usa valid_from/valid_to o DateRangeField?
grep -n "valid_" apps/pricing/models.py | head -10
# Si aparece DateRangeField → PARAR y escalar al arquitecto. Este sprint asume campos separados.

# 8. ¿Dispatcher existe?
grep -rn "def dispatch_command\|HANDLERS" apps/expedientes/services/

# 9. ¿payment_grace_days en ClientSubsidiary?
grep -rn "payment_grace_days" apps/clientes/models.py

# 10. ¿EventLog existe?
grep -rn "class EventLog" apps/expedientes/models.py
```

**Si un campo o modelo que este prompt dice crear ya existe → NO crearlo de nuevo.**

---

## FASE 0 — MOTOR DIMENSIONAL + FIXES (hacer primero)

### Item 0.1 — App `sizing/` con 6 modelos

**Crear app nueva:** `python manage.py startapp sizing` → mover a `apps/sizing/`

**6 modelos en `apps/sizing/models.py`:**

1. **SizeSystem** — Servicio de plataforma (sin FK a Brand). `code` unique global, `category` choices (FOOTWEAR/SHIRT/PANTS/GLOVES/GENERIC), `is_active`, timestamps.

2. **SizeDimension** — N dimensiones por sistema. `system` FK, `code` (ej: 'size', 'neck', 'chest'), `display_name`, `unit`, `display_order`, `is_primary`. unique_together: (system, code).

3. **SizeEntry** — Una talla. `system` FK, `label` (ej: 'S1', '42', '16/42/38'), `display_order`, `is_active`. unique_together: (system, label).

4. **SizeEntryValue** — Valor de una dimensión para una talla. `entry` FK, `dimension` FK, `value`. unique_together: (entry, dimension). **Incluir clean() que valida dimension.system_id == entry.system_id.**

5. **SizeEquivalence** — Mapeo 1:N a sistemas estándar. `entry` FK, `standard_system` CharField(30) LIBRE (no choices), `value`, `display_order`, `is_primary`. unique_together: (entry, standard_system, value).

6. **BrandSizeSystemAssignment** — M:N brand↔sistema. `brand` FK, `size_system` FK, `is_default` bool, `assigned_at`, `notes`. unique_together: (brand, size_system).

**Admin:** Inlines — SizeDimension y SizeEntry inline en SizeSystemAdmin. SizeEntryValue y SizeEquivalence inline en SizeEntryAdmin. Override `SizeEntryAdmin.save_model()` para invocar `validate_entry_completeness()` cuando `is_active=True`.

**Servicio de validación en `apps/sizing/services.py`:**
```python
def validate_entry_completeness(entry):
    """Verifica que entry activo tenga exactamente 1 valor por dimensión del sistema."""
    system_dims = set(entry.system.dimensions.values_list('id', flat=True))
    entry_dims = set(entry.dimension_values.values_list('dimension_id', flat=True))
    missing = system_dims - entry_dims
    if missing:
        from apps.sizing.models import SizeDimension
        codes = SizeDimension.objects.filter(id__in=missing).values_list('code', flat=True)
        raise ValidationError(f"Entry '{entry.label}' le faltan dimensiones: {list(codes)}")
```

**Data migration (idempotente con get_or_create):**

```python
def seed_size_systems(apps, schema_editor):
    SizeSystem = apps.get_model('sizing', 'SizeSystem')
    SizeDimension = apps.get_model('sizing', 'SizeDimension')
    SizeEntry = apps.get_model('sizing', 'SizeEntry')
    SizeEntryValue = apps.get_model('sizing', 'SizeEntryValue')
    SizeEquivalence = apps.get_model('sizing', 'SizeEquivalence')
    BrandSizeSystemAssignment = apps.get_model('sizing', 'BrandSizeSystemAssignment')
    Brand = apps.get_model('brands', 'Brand')

    # Sistemas
    rw_sys, _ = SizeSystem.objects.get_or_create(
        code='RW_S1_S6', defaults={'display_name': 'Rana Walk S1-S6', 'category': 'FOOTWEAR'})
    br_sys, _ = SizeSystem.objects.get_or_create(
        code='BR_CALZADO_33_48', defaults={'display_name': 'Brasil Calzado 33-48', 'category': 'FOOTWEAR'})

    # Dimensiones
    rw_dim, _ = SizeDimension.objects.get_or_create(
        system=rw_sys, code='size', defaults={'display_name': 'Talla', 'unit': '', 'display_order': 1, 'is_primary': True})
    br_dim, _ = SizeDimension.objects.get_or_create(
        system=br_sys, code='size', defaults={'display_name': 'Talla BR', 'unit': '', 'display_order': 1, 'is_primary': True})

    # Entries + Values + Equivalences (patrón idempotente)
    RW_SIZES = [
        {'label': 'S1', 'order': 1, 'equivs': [
            ('EU', '35', True), ('EU', '36', False),
            ('US_MEN', '3.5', True), ('US_MEN', '4', False),
            ('US_WOMEN', '5', True), ('US_WOMEN', '5.5', False),
            ('UK_MEN', '2.5', True), ('UK_MEN', '3', False),
            ('BR', '33', True), ('BR', '34', False),
            ('CM', '218', True), ('CM', '225', False)]},
        {'label': 'S2', 'order': 2, 'equivs': [
            ('EU', '37', True), ('EU', '38', False),
            ('US_MEN', '4.5', True), ('US_MEN', '5.5', False),
            ('US_WOMEN', '6', True), ('US_WOMEN', '7', False),
            ('UK_MEN', '3.5', True), ('UK_MEN', '4.5', False),
            ('BR', '35', True), ('BR', '36', False),
            ('CM', '231', True), ('CM', '238', False)]},
        {'label': 'S3', 'order': 3, 'equivs': [
            ('EU', '39', True), ('EU', '40', False),
            ('US_MEN', '6', True), ('US_MEN', '7', False),
            ('US_WOMEN', '7.5', True), ('US_WOMEN', '8.5', False),
            ('UK_MEN', '5', True), ('UK_MEN', '6', False),
            ('BR', '37', True), ('BR', '38', False),
            ('CM', '245', True), ('CM', '252', False)]},
        {'label': 'S4', 'order': 4, 'equivs': [
            ('EU', '41', True), ('EU', '42', False),
            ('US_MEN', '7.5', True), ('US_MEN', '8.5', False),
            ('US_WOMEN', '9', True), ('US_WOMEN', '10', False),
            ('UK_MEN', '6.5', True), ('UK_MEN', '7.5', False),
            ('BR', '39', True), ('BR', '40', False),
            ('CM', '258', True), ('CM', '265', False)]},
        {'label': 'S5', 'order': 5, 'equivs': [
            ('EU', '43', True), ('EU', '44', False),
            ('US_MEN', '9', True), ('US_MEN', '10', False),
            ('US_WOMEN', '10.5', True), ('US_WOMEN', '11.5', False),
            ('UK_MEN', '8', True), ('UK_MEN', '9', False),
            ('BR', '41', True), ('BR', '42', False),
            ('CM', '272', True), ('CM', '278', False)]},
        {'label': 'S6', 'order': 6, 'equivs': [
            ('EU', '45', True), ('EU', '46', False), ('EU', '47', False),
            ('US_MEN', '10.5', True), ('US_MEN', '11.5', False), ('US_MEN', '12', False),
            ('US_WOMEN', '12', True), ('US_WOMEN', '13', False), ('US_WOMEN', '13.5', False),
            ('UK_MEN', '9.5', True), ('UK_MEN', '10.5', False), ('UK_MEN', '11', False),
            ('BR', '43', True), ('BR', '44', False), ('BR', '45', False),
            ('CM', '285', True), ('CM', '292', False), ('CM', '298', False)]},
    ]

    for sz in RW_SIZES:
        entry, _ = SizeEntry.objects.get_or_create(
            system=rw_sys, label=sz['label'], defaults={'display_order': sz['order']})
        SizeEntryValue.objects.get_or_create(
            entry=entry, dimension=rw_dim, defaults={'value': sz['label']})
        for std_sys, val, primary in sz['equivs']:
            SizeEquivalence.objects.get_or_create(
                entry=entry, standard_system=std_sys, value=val,
                defaults={'is_primary': primary, 'display_order': 0})

    # Marluvas 33-48 (mismo patrón, datos de ENT_MERCADO_TALLAS)
    BR_SIZES = [
        {'label': '33', 'order': 1, 'equivs': [('EU','35',True),('US_MEN','3.5',True),('UK_MEN','2.5',True),('CM','218',True)]},
        {'label': '34', 'order': 2, 'equivs': [('EU','36',True),('US_MEN','4',True),('UK_MEN','3',True),('CM','225',True)]},
        {'label': '35', 'order': 3, 'equivs': [('EU','37',True),('US_MEN','4.5',True),('UK_MEN','3.5',True),('CM','231',True)]},
        {'label': '36', 'order': 4, 'equivs': [('EU','38',True),('US_MEN','5.5',True),('UK_MEN','4.5',True),('CM','238',True)]},
        {'label': '37', 'order': 5, 'equivs': [('EU','39',True),('US_MEN','6',True),('UK_MEN','5',True),('CM','245',True)]},
        {'label': '38', 'order': 6, 'equivs': [('EU','40',True),('US_MEN','7',True),('UK_MEN','6',True),('CM','252',True)]},
        {'label': '39', 'order': 7, 'equivs': [('EU','41',True),('US_MEN','7.5',True),('UK_MEN','6.5',True),('CM','258',True)]},
        {'label': '40', 'order': 8, 'equivs': [('EU','42',True),('US_MEN','8.5',True),('UK_MEN','7.5',True),('CM','265',True)]},
        {'label': '41', 'order': 9, 'equivs': [('EU','43',True),('US_MEN','9',True),('US_MEN','9.5',False),('UK_MEN','8',True),('CM','272',True)]},
        {'label': '42', 'order': 10, 'equivs': [('EU','44',True),('US_MEN','10',True),('UK_MEN','9',True),('CM','278',True)]},
        {'label': '43', 'order': 11, 'equivs': [('EU','45',True),('US_MEN','10.5',True),('UK_MEN','9.5',True),('CM','285',True)]},
        {'label': '44', 'order': 12, 'equivs': [('EU','46',True),('US_MEN','11.5',True),('UK_MEN','10.5',True),('CM','292',True)]},
        {'label': '45', 'order': 13, 'equivs': [('EU','47',True),('US_MEN','12',True),('UK_MEN','11',True),('CM','298',True)]},
        {'label': '46', 'order': 14, 'equivs': [('EU','48',True),('US_MEN','13',True),('UK_MEN','12',True),('CM','305',True)]},
        {'label': '47', 'order': 15, 'equivs': [('EU','49',True),('US_MEN','13.5',True),('UK_MEN','12.5',True),('CM','312',True)]},
        {'label': '48', 'order': 16, 'equivs': [('EU','50',True),('US_MEN','14',True),('UK_MEN','13',True),('CM','318',True)]},
    ]

    for sz in BR_SIZES:
        entry, _ = SizeEntry.objects.get_or_create(
            system=br_sys, label=sz['label'], defaults={'display_order': sz['order']})
        SizeEntryValue.objects.get_or_create(
            entry=entry, dimension=br_dim, defaults={'value': sz['label']})
        for std_sys, val, primary in sz['equivs']:
            SizeEquivalence.objects.get_or_create(
                entry=entry, standard_system=std_sys, value=val,
                defaults={'is_primary': primary, 'display_order': 0})

    # Assignments (con error controlado si brand no existe)
    for brand_code, sys in [('rana_walk', rw_sys), ('marluvas', br_sys)]:
        try:
            brand = Brand.objects.get(code=brand_code)
            BrandSizeSystemAssignment.objects.get_or_create(
                brand=brand, size_system=sys, defaults={'is_default': True})
        except Brand.DoesNotExist:
            pass
```

**Verificación post-migración:**
```bash
python manage.py shell -c "
from apps.sizing.models import SizeSystem, SizeEntry, SizeEquivalence, BrandSizeSystemAssignment
print('Systems:', SizeSystem.objects.count())  # 2
print('RW entries:', SizeEntry.objects.filter(system__code='RW_S1_S6').count())  # 6
print('BR entries:', SizeEntry.objects.filter(system__code='BR_CALZADO_33_48').count())  # 16
print('Assignments:', BrandSizeSystemAssignment.objects.count())  # 2 (o 0 si brands no existen)
print('Total equivalences:', SizeEquivalence.objects.count())  # ~160
"
```

---

### Item 0.2 — FK nullable brand_sku en ExpedienteProductLine

```python
# En apps/expedientes/models.py → class ExpedienteProductLine
brand_sku = models.ForeignKey(
    'brands.BrandSKU', on_delete=models.SET_NULL,
    null=True, blank=True, related_name='expediente_lines',
    help_text="SKU específico con talla. Nullable para backward compat.")

@property
def size_display(self):
    if self.brand_sku and self.brand_sku.size:
        return self.brand_sku.size
    return '—'
```

---

### Item 0.3 — Fix bug valid_to=null en resolve_client_price()

**Grep previo OBLIGATORIO:**
```bash
grep -n "valid_" apps/pricing/models.py | head -10
# Si aparece DateRangeField → PARAR y escalar al arquitecto
```

**Fix (asumiendo campos separados):**
```python
from django.db.models import Q
pricelists = PriceList.objects.filter(
    Q(valid_from__lte=today),
    Q(valid_to__isnull=True) | Q(valid_to__gte=today),
    ...
)
```

---

### Item 0.4 — 6 campos nullable

| Campo | Modelo | Tipo |
|-------|--------|------|
| pricelist_used | ExpedienteProductLine | FK nullable → PriceList |
| base_price | ExpedienteProductLine | Decimal(10,2) nullable |
| moq_per_size | PriceListItem | PositiveIntegerField nullable |
| credit_status | ExpedientePago | CharField(20) nullable, choices PENDING/CONFIRMED/REJECTED |
| credit_released | Expediente | BooleanField default=False |
| incoterms | Expediente | CharField(3) nullable, choices EXW/FOB/CIF/DDP |

---

### Item 0.5 — Hook post_command_hooks en dispatcher

```python
# En el dispatcher, después de ejecutar command exitosamente:
post_command_hooks = []  # Módulo-level

def dispatch_command(expediente, command_code, user, **kwargs):
    result = handler(expediente, user, **kwargs)
    for hook in post_command_hooks:
        hook(expediente=expediente, command_code=command_code, user=user, result=result)
    return result
```

Hooks NO se invocan si el command lanza excepción.

---

### GATE FASE 0

```bash
python manage.py test apps/sizing/ -v2
python manage.py test apps/expedientes/ -v2
python manage.py test apps/pricing/ -v2
# TODO: agregar tests específicos de S18
```

Todos verdes → avanzar a Fase 1.

---

## FASE 1 — ENDPOINTS BACKEND

### Item 1.1 — Serializers (S18-06)

5 serializers: ProductLineSerializer (con brand_sku + size_display), FactoryOrderSerializer (CRUD), PagoSerializer (con credit_status por pago), BundleSerializer (credit_released + credit_exposure, NO credit_status a nivel expediente), SizeSystemSerializer (read-only nested).

### Item 1.2 — 5 PATCH por estado (S18-07)

| Endpoint | Estado FROZEN |
|----------|--------------|
| PATCH `/expedientes/{id}/confirmado/` | CONFIRMADO |
| PATCH `/expedientes/{id}/preparacion/` | PREPARACION |
| PATCH `/expedientes/{id}/produccion/` | PRODUCCION |
| PATCH `/expedientes/{id}/despacho/` | DESPACHO |
| PATCH `/expedientes/{id}/transito/` | TRANSITO |

Cada uno valida `expediente.current_status == estado`. Si no → 409.
Tenant: `for_user(request.user)`, nunca `.all()`.

### Item 1.3 — CRUD FactoryOrder (S18-08)

GET/POST/PATCH/DELETE en `/expedientes/{id}/factory-orders/`.
Auto-gen `factory_order_number` si no viene: `FO-{expediente.code}-{seq:03d}`.
**Sync obligatoria:** Después de POST/PATCH/DELETE invocar:
```python
def sync_factory_order_number(expediente):
    principal = expediente.factory_orders.order_by('id').first()
    expediente.factory_order_number = principal.factory_order_number if principal else None
    expediente.save(update_fields=['factory_order_number'])
```

### Item 1.4 — POST pagos + confirmación (S18-09)

POST `/expedientes/{id}/pagos/` → crea pago PENDING.
PATCH `/expedientes/{id}/pagos/{id}/confirmar/` → CONFIRMED + recalculate + sync CreditExposure.
**Nunca auto-release al registrar.** Solo al confirmar.

### Item 1.5 — POST merge (S18-10)

POST `/expedientes/{id}/merge/` con `follower_ids[]`.
Valida estados REGISTRO / PI_SOLICITADA / CONFIRMADO (pre-producción).
`select_for_update` ordenado por ID.
Followers → `c_cancel`.
Recalcular crédito del master.

### Item 1.6 — POST separate-products (S18-11)

POST `/expedientes/{id}/separate-products/` con `product_line_ids[]`.
No permitir separar TODAS las líneas.
Nuevo expediente hereda metadata.
Recalcular crédito en ambos.

### Item 1.7 — Actualizar C1 (S18-13)

C1 acepta `product_lines` con `brand_sku` FK, `incoterms`, `purchase_order_number`.
Si brand_sku viene → auto-resolver precio vía resolve_client_price() → snapshot en pricelist_used + base_price.
Backward compat: POST sin campos nuevos funciona igual.

### Item 1.8 — recalculate_expediente_credit (S18-15)

**ÚNICA fuente de verdad para credit_exposure y credit_released:**
```python
def recalculate_expediente_credit(expediente):
    total_lines = sum(l.unit_price * l.quantity for l in expediente.product_lines.all())
    total_paid = sum(p.amount for p in expediente.pagos.filter(credit_status='CONFIRMED'))
    expediente.credit_exposure = total_lines - total_paid
    expediente.credit_released = (expediente.credit_exposure <= 0)
    expediente.save(update_fields=['credit_exposure', 'credit_released'])
```

### Item 1.9 — Sync CreditExposure + EventLog (S18-16)

Post-recálculo: si credit_released cambió → sincronizar CreditExposure del cliente + EventLog.

### Item 1.10 — Chain resolver pricing (S18-17)

Refactorear resolve_client_price() a chain-of-responsibility:
```python
PRICE_RESOLVERS = [
    resolve_from_brand_client_pricelist,
    resolve_from_brand_default_pricelist,
    resolve_from_product_master_base_price,
]
```

### Item 1.11 — EventLog estandarizado (S18-18)

3 campos aditivos nullable: event_type, previous_status, new_status.
Todos los commands populan event_type='state_change'.
PATCH → 'data_edit'. Merge → 'merge'. Split → 'split'. Pago → 'payment'.

---

## TANDA DE MIGRACIONES

```bash
python manage.py makemigrations sizing
python manage.py makemigrations expedientes
python manage.py makemigrations pricing
python manage.py makemigrations clientes
# Verificar cada una con sqlmigrate — solo CreateModel + AddField + RunPython
python manage.py migrate
python manage.py check
python manage.py test
```

---

## CRITERIO SPRINT 18 DONE

1. App `sizing/` con 6 modelos + seed RW/Marluvas + admin funcional
2. EPL acepta brand_sku FK nullable
3. resolve_client_price() funciona con valid_to=null
4. Hook post_command_hooks invoca hooks
5. 5 PATCH por estado responden correctamente
6. CRUD FactoryOrder + sync_factory_order_number
7. Pagos: POST PENDING + confirmar CONFIRMED + recálculo
8. Merge y Split funcionales
9. C1 backward compatible con campos nuevos
10. Bundle con credit_released + credit_exposure
11. `python manage.py test` verde
12. `bandit -ll backend/` sin high/critical
