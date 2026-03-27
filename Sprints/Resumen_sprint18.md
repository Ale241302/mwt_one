# Resumen Sprint 18 — Motor Dimensional + Endpoints Backend

**Fecha:** 27 de marzo de 2026
**PRs mergeados:** [#45](https://github.com/Ale241302/mwt_one/pull/45) (Fase 0) · [#46](https://github.com/Ale241302/mwt_one/pull/46) (Fase 1)
**Commits clave:** `9f133fd` (Fase 0) · `65afbaa` (Fase 1)

---

## ✅ FASE 0 — Motor Dimensional + Fixes

### T0.1 — App `apps/sizing/` (nueva desde cero)

Creada app completa con **6 modelos**:

| Modelo | Descripción |
|---|---|
| `SizeSystem` | Sistema de tallas de plataforma (sin FK a Brand) |
| `SizeDimension` | N dimensiones por sistema (EU, US_MEN, CM, etc.) |
| `SizeEntry` | Talla individual (S1, 42, etc.) |
| `SizeEntryValue` | Valor de dimensión por talla, con `clean()` que valida mismo sistema |
| `SizeEquivalence` | Mapeo 1:N a estándar externo (campo libre, sin choices) |
| `BrandSizeSystemAssignment` | M:N Brand ↔ SizeSystem |

**Archivos creados:**
- `apps/sizing/models.py` — 6 modelos
- `apps/sizing/services.py` — `validate_entry_completeness()`
- `apps/sizing/admin.py` — `SizeSystemAdmin` + `SizeEntryAdmin` con inlines y override `save_model()`
- `apps/sizing/serializers.py` — `SizeSystemSerializer` read-only nested
- `apps/sizing/views.py` + `apps/sizing/urls.py`
- `apps/sizing/tests.py` — tests básicos
- `apps/sizing/migrations/0001_initial.py` — CreateModel
- `apps/sizing/migrations/0002_seed_rw_marluvas.py` — Seed idempotente

**Seed incluido:**
- Sistema `RW_S1_S6` (Rana Walk): 6 entries (S1–S6) con equivalencias EU, US_MEN, US_WOMEN, UK_MEN, BR, CM
- Sistema `BR_CALZADO_33_48` (Marluvas): 16 entries (33–48) con equivalencias EU, US_MEN, UK_MEN, CM
- Assignments a `brand.code='rana_walk'` y `brand.code='marluvas'` (con try/except)
- Total esperado: ~160 equivalencias

### T0.2 — FK `brand_sku` nullable en `ExpedienteProductLine`

Agregado campo `ForeignKey('brands.BrandSKU', null=True, blank=True)` y property `size_display`.

### T0.3 — Fix bug `valid_to=null` en `resolve_client_price()`

Reemplazado filtro de `PriceList` con:
```python
Q(valid_to__isnull=True) | Q(valid_to__gte=today)
```

### T0.4 — 6 campos nullable (additive-only)

| Campo | Modelo | Tipo |
|---|---|---|
| `pricelist_used` | `ExpedienteProductLine` | FK → `pricing.PriceList` |
| `base_price` | `ExpedienteProductLine` | `DecimalField` |
| `moq_per_size` | `PriceListItem` | `PositiveIntegerField` |
| `credit_status` | `ExpedientePago` | `CharField` choices PENDING/CONFIRMED/REJECTED |
| `credit_released` | `Expediente` | `BooleanField(default=False)` |
| `incoterms` | `Expediente` | `CharField` choices EXW/FOB/CIF/DDP |

### T0.5 — Hook `post_command_hooks` en dispatcher

Agregada lista módulo-level `post_command_hooks = []` que se invoca después de cada comando exitoso (no si lanza excepción).

**Migración aplicada:** `apps/expedientes/migrations/0_sprint18_fields.py`

---

## ✅ FASE 1 — Endpoints Backend

### T1.1 — 5 Serializers (`apps/expedientes/serializers.py`)

- `ProductLineSerializer` — incluye `brand_sku`, `size_display` (read-only), `pricelist_used`, `base_price`
- `FactoryOrderSerializer` — CRUD completo
- `PagoSerializer` — incluye `credit_status`
- `BundleSerializer` — campos `credit_released` + `credit_exposure` (sin `credit_status` a nivel Expediente)
- `SizeSystemSerializer` — read-only nested (en `apps/sizing/serializers.py`)

### T1.2 — 5 PATCH endpoints por estado (`apps/expedientes/views_sprint18.py`)

| Endpoint | Estado requerido | HTTP si no coincide |
|---|---|---|
| `PATCH /expedientes/{id}/confirmado/` | CONFIRMADO | 409 |
| `PATCH /expedientes/{id}/preparacion/` | PREPARACION | 409 |
| `PATCH /expedientes/{id}/produccion/` | PRODUCCION | 409 |
| `PATCH /expedientes/{id}/despacho/` | DESPACHO | 409 |
| `PATCH /expedientes/{id}/transito/` | TRANSITO | 409 |

Todos usan `Expediente.objects.for_user(request.user)` (tenant isolation).

### T1.3 — CRUD FactoryOrder (`/expedientes/{id}/factory-orders/`)

- Auto-genera `factory_order_number = FO-{code}-{seq:03d}` en POST
- `sync_factory_order_number()` tras POST, PATCH y DELETE
- `factory_order_number` del expediente es derivado (read-only), nunca editable directo

### T1.4 — Pagos POST + confirmación

- `POST /expedientes/{id}/pagos/` → crea con `credit_status='PENDING'`
- `PATCH /expedientes/{id}/pagos/{id}/confirmar/` → `CONFIRMED` + `recalculate_expediente_credit()`
- Nunca auto-libera crédito al crear pago

### T1.5 — Merge (`POST /expedientes/{id}/merge/`)

- Valida estados pre-producción (REGISTRO, PI_SOLICITADA, CONFIRMADO)
- `select_for_update()` ordenado por ID (evita deadlocks)
- Cancela followers, mueve líneas al master
- `recalculate_expediente_credit(master)` al final

### T1.6 — Split (`POST /expedientes/{id}/separate-products/`)

- Valida que NO se separan todas las líneas → error 400
- Nuevo expediente hereda metadata del original
- `recalculate_expediente_credit()` en ambos expedientes

### T1.7 — Extensión C1 backward compatible (`apps/expedientes/services/commands_registro_s18.py`)

Acepta opcionales: `brand_sku`, `incoterms`, `purchase_order_number`.
Si viene `brand_sku` → auto-resuelve precio vía `resolve_client_price()` → snapshot en `pricelist_used` + `base_price`.

### T1.8 — `recalculate_expediente_credit()` (`apps/expedientes/services/credit.py`)

Única fuente de verdad para `credit_exposure` y `credit_released`:
```python
credit_exposure = total_lines - total_confirmed_payments
credit_released = (credit_exposure <= 0)  # bidireccional
```

### T1.9 — Sync `CreditExposure` + `EventLog`

Si `credit_released` cambia tras recálculo → sincroniza `CreditExposure` del cliente + crea `EventLog(event_type='credit_change')`.

### T1.10 — Chain-of-responsibility pricing (`apps/pricing/services.py`)

```python
PRICE_RESOLVERS = [
    resolve_from_brand_client_pricelist,   # más específico
    resolve_from_brand_default_pricelist,
    resolve_from_product_master_base_price, # fallback
]
```

### T1.11 — EventLog estandarizado

3 campos nullable agregados: `event_type`, `previous_status`, `new_status`.

| Operación | `event_type` |
|---|---|
| Command (transición de estado) | `state_change` |
| PATCH edición de datos | `data_edit` |
| Merge | `merge` |
| Split | `split` |
| Pago confirmado | `payment` |

---

## ⚠️ Pasos manuales pendientes post-merge

### 1. Agregar en `backend/config/settings/base.py` → `INSTALLED_APPS`
```python
'apps.sizing',   # Sprint 18
```

### 2. Agregar en `backend/config/urls.py` → `urlpatterns`
```python
path('api/expedientes/', include('apps.expedientes.urls_sprint18')),
```

### 3. Reiniciar Django y correr migraciones
```powershell
docker compose restart django
docker compose exec django python manage.py makemigrations sizing expedientes pricing
docker compose exec django python manage.py migrate
docker compose exec django python manage.py check
```

### 4. Verificar seed
```powershell
docker compose exec django python manage.py shell -c "
from apps.sizing.models import SizeSystem, SizeEntry, SizeEquivalence
print('Systems:', SizeSystem.objects.count())        # 2
print('RW:', SizeEntry.objects.filter(system__code='RW_S1_S6').count())   # 6
print('BR:', SizeEntry.objects.filter(system__code='BR_CALZADO_33_48').count())  # 16
print('Equivalences:', SizeEquivalence.objects.count())  # ~160
"
```

### 5. Gate final
```powershell
docker compose exec django python manage.py test
```

---

## 📁 Archivos nuevos en este sprint

```
backend/
├── apps/
│   ├── sizing/                          ← App nueva completa
│   │   ├── __init__.py
│   │   ├── admin.py
│   │   ├── apps.py
│   │   ├── models.py
│   │   ├── serializers.py
│   │   ├── services.py
│   │   ├── tests.py
│   │   ├── urls.py
│   │   ├── views.py
│   │   └── migrations/
│   │       ├── 0001_initial.py
│   │       └── 0002_seed_rw_marluvas.py
│   └── expedientes/
│       ├── migrations/
│       │   └── 0_sprint18_fields.py     ← AddField (nullable, no-op)
│       ├── serializers.py               ← Actualizado
│       ├── urls_sprint18.py             ← Nuevo
│       ├── views_sprint18.py            ← Nuevo
│       └── services/
│           ├── commands_registro_s18.py ← Nuevo
│           ├── credit.py                ← Nuevo
│           └── dispatcher.py           ← Nuevo
└── apps/pricing/
    └── services.py                      ← Refactorizado (chain resolver)
```

---

## 🔗 Conventional Commits

```
feat: create sizing app with 6 models and RW/Marluvas seed
feat: add brand_sku FK to ExpedienteProductLine
fix: resolve valid_to null bug in resolve_client_price
feat: add PATCH state endpoints with HTTP 409 validation
feat: add FactoryOrder CRUD with sync
feat: add payments POST and confirm flow
feat: add merge and split endpoints
refactor: chain-of-responsibility for pricing resolver
feat: add recalculate_expediente_credit as single source of truth
feat: add EventLog standardized fields (event_type, previous/new_status)
```
