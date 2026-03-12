# MODULOS_FALTANTES_FRONTEND_BACKEND.md
# Módulos Faltantes — consola.mwt.one

**Documento:** KB de referencia para sprints futuros
**Fecha:** 2026-03-12
**Estado:** BORRADOR — pendiente aprobación CEO
**Propósito:** Este archivo guía a Claude (AG-03 Frontend / AG-04 Backend) sobre qué módulos
completos deben construirse en los próximos sprints para tener una consola operativa total.
**Contexto base:** Sprint 7 completó el frontend operativo de expedientes. Este documento cubre
todo lo que aún falta para que la consola sea autónoma y multi-usuario.

---

## Estado actual del sistema (post Sprint 7)

### Apps Django existentes en `backend/apps/`

| App | Estado backend | Frontend en consola |
|-----|---------------|---------------------|
| `expedientes` | ✅ 39 endpoints, 100% funcional | ✅ Sprint 7 completado |
| `brands` | ✅ Existe en backend (fixtures + generate_brands_fixtures.py) | ❌ Sin UI en consola |
| `transfers` | ✅ Existe app | ❌ Sin UI en consola (Sprint 8) |
| `liquidations` | ✅ Existe app | ❌ Sin UI (Sprint 8) |
| `qr` | ✅ Existe app | ❌ Sin UI (Sprint 8) |
| `core` | ✅ Existe app (base) | — |
| `integrations` | ✅ Existe app | — |

### Apps Django AUSENTES (deben crearse)

| App | Motivo |
|-----|--------|
| `users` (custom) | Django usa auth.User base pero sin modelo extendido confirmado |
| `groups_permissions` | Django tiene Group nativo pero sin API REST expuesta |
| `clients` | Existe referenciado en expedientes pero sin app dedicada confirmada |
| `products` | No existe — líneas, tallas, referencias de producto |
| `inventory` | No existe — stock por nodo logístico |
| `nodes` | Referenciado en transfers pero sin app/modelo dedicado confirmado |

---

## Convenciones para todos los módulos de este documento

```
REGLAS INVARIABLES — Claude debe respetarlas en todos los módulos:

1. Backend: Django REST Framework · ModelViewSet o APIView · JWT auth
2. Frontend: Next.js 14 App Router · [lang]/(mwt)/(dashboard)/{modulo}/
3. Formularios: Drawer lateral para crear/editar — SALVO casos indicados
4. Listados: Tabla con paginación, búsqueda y filtros
5. Acciones destructivas: Modal de confirmación con razón obligatoria
6. Design tokens: ENT_PLAT_DESIGN_TOKENS en todos los componentes
7. Permisos: En Sprint 8-MVP se asume CEO = superuser. RBAC real entra post-MVP
   EXCEPTO el módulo de Grupos (que define los permisos para cuando RBAC se active)
8. Endpoints: Seguir patrón /api/{recurso}/ con trailing slash
9. Soft delete: Todos los modelos deben tener is_active + deleted_at (no borrado físico)
10. UUIDs: Todos los modelos usan UUID como PK (consistente con expedientes)
```

---

## MÓDULO 1 — Grupos de Permisos

**Nombre técnico:** `permission_groups`
**App Django:** Extender `django.contrib.auth.Group` con metadatos propios
**Sprint sugerido:** 8 (base del sistema RBAC)
**Prioridad:** P1 — debe existir antes de activar multi-usuario real

### Descripción

Sistema de grupos que define qué puede hacer cada tipo de usuario en la consola.
Un grupo agrupa un conjunto de permisos de Django (`django.contrib.auth.Permission`).
Los usuarios se asocian a uno o más grupos y heredan sus permisos.

**Grupos base sugeridos (seed):**

| Grupo | Descripción |
|-------|-------------|
| `superadmin` | Acceso total — equivalente al CEO actual |
| `operador` | Crear/avanzar expedientes, registrar costos — sin acceso a finanzas |
| `financiero` | Ver costos, registrar pagos, emitir facturas |
| `visor` | Solo lectura — sin acciones destructivas |
| `logistica` | Gestión de nodos, inventario, transfers |

### Modelo Django

```python
# backend/apps/permission_groups/models.py

class MWTGroup(models.Model):
    """Extensión de django.contrib.auth.Group con metadatos MWT"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    auth_group = models.OneToOneField(
        'auth.Group', on_delete=models.CASCADE, related_name='mwt_group'
    )
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['auth_group__name']
```

### Endpoints Backend

| Método | Endpoint | Descripción | Auth |
|--------|----------|-------------|------|
| GET | `/api/groups/` | Listar todos los grupos | CEO |
| POST | `/api/groups/` | Crear grupo nuevo | CEO |
| GET | `/api/groups/{id}/` | Detalle de grupo | CEO |
| PATCH | `/api/groups/{id}/` | Editar nombre/descripción | CEO |
| DELETE | `/api/groups/{id}/` | Desactivar grupo (soft) | CEO |
| GET | `/api/groups/{id}/permissions/` | Listar permisos del grupo | CEO |
| POST | `/api/groups/{id}/permissions/` | Asignar permisos al grupo | CEO |
| DELETE | `/api/groups/{id}/permissions/{perm_id}/` | Quitar permiso del grupo | CEO |
| GET | `/api/permissions/` | Listar todos los permisos disponibles | CEO |

### Rutas Frontend (consola.mwt.one)

```
[lang]/(mwt)/(dashboard)/configuracion/grupos/page          → Lista de grupos
[lang]/(mwt)/(dashboard)/configuracion/grupos/nuevo/page    → Crear grupo
[lang]/(mwt)/(dashboard)/configuracion/grupos/[id]/page     → Detalle + editar permisos
```

### UI — Componentes requeridos

- **Lista grupos:** Tabla con nombre, descripción, # usuarios, # permisos, estado (activo/inactivo), acciones
- **Crear grupo:** Formulario en página nueva — nombre, descripción + checklist de permisos disponibles
- **Detalle grupo:** Ver permisos asignados + lista de usuarios en el grupo
- **Asignar permisos:** Checklist agrupado por módulo (expedientes, transfers, inventario, etc.)

### Criterio de done

- [ ] CRUD completo de grupos funcional desde consola
- [ ] Checklist de permisos disponibles cargado desde `GET /api/permissions/`
- [ ] Asignación/revocación de permisos en tiempo real
- [ ] Soft delete: grupos inactivos no aparecen en selects de usuario
- [ ] Grupos base seed creados automáticamente en migrations

---

## MÓDULO 2 — Clientes

**Nombre técnico:** `clients`
**App Django:** `backend/apps/clients/` (crear nueva app dedicada)
**Sprint sugerido:** 8
**Prioridad:** P0 — `GET /api/clients/` ya se usa en expedientes (S7-01)

### Descripción

Gestión de los clientes con quienes MWT opera expedientes. Actualmente el endpoint
`GET /api/clients/` existe (referenciado en Sprint 7 para poblar select de crear expediente)
pero no hay UI para administrar clientes desde la consola.

### Modelo Django

```python
# backend/apps/clients/models.py

class Client(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    name = models.CharField(max_length=200)
    legal_name = models.CharField(max_length=200, blank=True)
    tax_id = models.CharField(max_length=50, blank=True)           # NIT / RUT / TIN
    country = models.CharField(max_length=3)                       # ISO 3166-1 alpha-3
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=30, blank=True)
    address = models.TextField(blank=True)
    credit_days = models.PositiveIntegerField(default=30)          # días crédito (reloj ART-05)
    credit_limit = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    currency = models.CharField(max_length=3, default='USD')       # moneda base
    notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
```

### Endpoints Backend

| Método | Endpoint | Descripción | Auth |
|--------|----------|-------------|------|
| GET | `/api/clients/` | Listar clientes activos | CEO |
| POST | `/api/clients/` | Crear cliente | CEO |
| GET | `/api/clients/{id}/` | Detalle cliente | CEO |
| PATCH | `/api/clients/{id}/` | Editar cliente | CEO |
| POST | `/api/clients/{id}/deactivate/` | Desactivar (soft delete) | CEO |
| GET | `/api/clients/{id}/expedientes/` | Expedientes del cliente | CEO |
| GET | `/api/clients/{id}/credit-status/` | Estado de crédito actual | CEO |

### Rutas Frontend (consola.mwt.one)

```
[lang]/(mwt)/(dashboard)/clientes/page           → Lista clientes
[lang]/(mwt)/(dashboard)/clientes/nuevo/page      → Crear cliente
[lang]/(mwt)/(dashboard)/clientes/[id]/page       → Detalle + historial expedientes
```

### UI — Componentes requeridos

- **Lista clientes:** Tabla — nombre, país, días crédito, moneda, # expedientes activos, estado
- **Crear cliente:** Página nueva (no drawer) — todos los campos del modelo
- **Detalle cliente:** Datos + tab "Expedientes" con historial + badge estado crédito
- **Estado crédito:** Semáforo — verde (<60% usado), amarillo (60-75%), rojo (>75%)

### Criterio de done

- [ ] CRUD completo desde consola
- [ ] `GET /api/clients/` retorna `[{ id, name }]` — compatible con S7-01
- [ ] Detalle muestra expedientes vinculados paginados
- [ ] Estado de crédito calculado y visible en detalle
- [ ] Cliente inactivo no aparece en el select de crear expediente

---

## MÓDULO 3 — Usuarios

**Nombre técnico:** `users`
**App Django:** `backend/apps/users/` (extender auth.User)
**Sprint sugerido:** 8-9
**Prioridad:** P1 — base para multi-usuario / RBAC real

### Descripción

Gestión de usuarios que pueden ingresar a la consola. Cada usuario:
- Se asocia a una o más **empresas** (brands/organizaciones operativas)
- Se asocia a uno o más **grupos** (hereda permisos de ese grupo)
- Tiene credenciales de acceso (email + contraseña)

### Modelo Django

```python
# backend/apps/users/models.py

class MWTUser(AbstractUser):
    """Extiende auth.User con campos MWT"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    # username heredado de AbstractUser
    # email heredado de AbstractUser (usar como login principal)
    # groups heredado de AbstractUser (ManyToMany a auth.Group)
    phone = models.CharField(max_length=30, blank=True)
    avatar_url = models.URLField(blank=True)
    associated_brands = models.ManyToManyField(
        'brands.Brand', blank=True, related_name='users'
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']
```

### Endpoints Backend

| Método | Endpoint | Descripción | Auth |
|--------|----------|-------------|------|
| GET | `/api/users/` | Listar usuarios | CEO |
| POST | `/api/users/` | Crear usuario | CEO |
| GET | `/api/users/{id}/` | Detalle usuario | CEO |
| PATCH | `/api/users/{id}/` | Editar usuario | CEO |
| POST | `/api/users/{id}/deactivate/` | Desactivar usuario | CEO |
| POST | `/api/users/{id}/reset-password/` | Resetear contraseña | CEO |
| POST | `/api/users/{id}/groups/` | Asignar grupos al usuario | CEO |
| DELETE | `/api/users/{id}/groups/{group_id}/` | Quitar grupo del usuario | CEO |
| POST | `/api/users/{id}/brands/` | Asociar usuario a brands | CEO |
| GET | `/api/auth/me/` | Perfil del usuario autenticado | Auth |
| POST | `/api/auth/login/` | Login (JWT) | Público |
| POST | `/api/auth/logout/` | Logout (blacklist token) | Auth |
| POST | `/api/auth/refresh/` | Refresh token JWT | Auth |

### Rutas Frontend (consola.mwt.one)

```
[lang]/(mwt)/(dashboard)/configuracion/usuarios/page           → Lista usuarios
[lang]/(mwt)/(dashboard)/configuracion/usuarios/nuevo/page     → Crear usuario
[lang]/(mwt)/(dashboard)/configuracion/usuarios/[id]/page      → Detalle + permisos
```

### UI — Componentes requeridos

- **Lista usuarios:** Tabla — nombre, email, grupos, brands asociadas, último acceso, estado
- **Crear usuario:** Página nueva — nombre, email, contraseña temporal, selección de grupos (multi-select), selección de brands (multi-select)
- **Detalle usuario:** Datos personales + grupos asignados + brands asociadas + historial acceso
- **Asignar grupos:** Multi-select de grupos cargado desde `GET /api/groups/`
- **Asociar brands:** Multi-select de brands cargado desde `GET /api/brands/`
- **Reset contraseña:** Modal con contraseña nueva (o enviar link por email si hay SMTP)

### Criterio de done

- [ ] CRUD completo desde consola
- [ ] Usuario puede asociarse a ≥1 grupo y ≥1 brand
- [ ] Usuario inactivo no puede hacer login
- [ ] Reset de contraseña funcional
- [ ] `GET /api/auth/me/` retorna perfil + grupos + brands del usuario autenticado

---

## MÓDULO 4 — Brands (Marcas)

**Nombre técnico:** `brands`
**App Django:** `backend/apps/brands/` — **YA EXISTE** en el backend
**Sprint sugerido:** 8
**Prioridad:** P1 — backend existe, falta UI en consola

### Descripción

Marcas de productos que opera MWT. Actualmente existen como fixtures (`generate_brands_fixtures.py`)
pero no hay UI para administrarlas desde la consola. Las marcas actuales son: `marluvas`, `tecmater`, `ranawalk`.
El campo `brand` en expedientes referencia este modelo.

### Modelo Django (existente — verificar contra código)

```python
# IMPORTANTE: Claude debe leer backend/apps/brands/models.py antes de implementar
# y ajustar este spec al modelo real existente

# Estructura probable basada en fixtures:
class Brand(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    slug = models.SlugField(unique=True)          # 'marluvas', 'tecmater', 'ranawalk'
    name = models.CharField(max_length=100)       # nombre display
    brand_type = models.CharField(...)            # 'own', 'client', etc.
    logo_url = models.URLField(blank=True)
    country = models.CharField(max_length=3, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
```

### Endpoints Backend

| Método | Endpoint | Descripción | Auth |
|--------|----------|-------------|------|
| GET | `/api/brands/` | Listar brands activas | Auth |
| POST | `/api/brands/` | Crear brand | CEO |
| GET | `/api/brands/{id}/` | Detalle brand | Auth |
| PATCH | `/api/brands/{id}/` | Editar brand | CEO |
| POST | `/api/brands/{id}/deactivate/` | Desactivar brand | CEO |
| GET | `/api/brands/{slug}/` | Detalle por slug | Auth |

### Rutas Frontend (consola.mwt.one)

```
[lang]/(mwt)/(dashboard)/configuracion/brands/page           → Lista brands
[lang]/(mwt)/(dashboard)/configuracion/brands/nueva/page     → Crear brand
[lang]/(mwt)/(dashboard)/configuracion/brands/[id]/page      → Detalle + editar
```

### UI — Componentes requeridos

- **Lista brands:** Tabla — logo, nombre, slug, tipo, país, # expedientes activos, estado
- **Crear brand:** Drawer lateral — slug (autogenerado desde nombre), nombre, tipo, país, upload logo
- **Detalle brand:** Vista datos + estadísticas expedientes de esa marca

### Criterio de done

- [ ] CRUD desde consola (respetando modelo existente en `backend/apps/brands/`)
- [ ] `GET /api/brands/` retorna lista compatible con formulario crear expediente
- [ ] Slug único validado al crear
- [ ] Brand inactiva no aparece en selects de expediente

---

## MÓDULO 5 — Productos

**Nombre técnico:** `products`
**App Django:** `backend/apps/products/` — **NUEVA APP** (no existe)
**Sprint sugerido:** 9
**Prioridad:** P1 — prerequisito para inventario y catálogo Rana Walk

### Descripción

Administración del catálogo de productos por brand. Cada producto tiene:
- Línea de producto (ej: GOL, VEL, ORB, LEO, BIS para Rana Walk)
- Referencia/SKU base
- Tallas disponibles (genera SKUs por talla)
- Precio base por moneda

### Modelo Django

```python
# backend/apps/products/models.py

class ProductLine(models.Model):
    """Línea de producto — ej: GOL, VEL, ORB"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    brand = models.ForeignKey('brands.Brand', on_delete=models.PROTECT)
    code = models.CharField(max_length=20)            # 'GOL', 'VEL', 'ORB'
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [['brand', 'code']]


class Product(models.Model):
    """Producto base — sin talla"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    line = models.ForeignKey(ProductLine, on_delete=models.PROTECT)
    sku_base = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=200)
    gender = models.CharField(
        max_length=10,
        choices=[('M', 'Masculino'), ('F', 'Femenino'), ('U', 'Unisex')],
        default='U'
    )
    color = models.CharField(max_length=50, blank=True)
    base_price = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    currency = models.CharField(max_length=3, default='USD')
    images = models.JSONField(default=list)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class ProductSize(models.Model):
    """SKU por talla — unidad mínima de inventario"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name='sizes')
    size = models.CharField(max_length=10)           # '35', '36', ... '45', 'S', 'M', 'L'
    sku = models.CharField(max_length=60, unique=True)  # SKU completo con talla
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = [['product', 'size']]
```

### Endpoints Backend

| Método | Endpoint | Descripción | Auth |
|--------|----------|-------------|------|
| GET | `/api/products/lines/` | Listar líneas por brand | Auth |
| POST | `/api/products/lines/` | Crear línea | CEO |
| GET | `/api/products/lines/{id}/` | Detalle línea | Auth |
| PATCH | `/api/products/lines/{id}/` | Editar línea | CEO |
| GET | `/api/products/` | Listar productos (filtrar por brand, line) | Auth |
| POST | `/api/products/` | Crear producto base | CEO |
| GET | `/api/products/{id}/` | Detalle producto | Auth |
| PATCH | `/api/products/{id}/` | Editar producto | CEO |
| GET | `/api/products/{id}/sizes/` | Listar tallas del producto | Auth |
| POST | `/api/products/{id}/sizes/` | Agregar talla | CEO |
| POST | `/api/products/{id}/sizes/bulk/` | Crear múltiples tallas a la vez | CEO |
| DELETE | `/api/products/{id}/sizes/{size_id}/` | Desactivar talla | CEO |

### Rutas Frontend (consola.mwt.one)

```
[lang]/(mwt)/(dashboard)/productos/page                    → Lista productos (filtrable por brand/línea)
[lang]/(mwt)/(dashboard)/productos/lineas/page             → Lista líneas de producto
[lang]/(mwt)/(dashboard)/productos/nuevo/page              → Crear producto
[lang]/(mwt)/(dashboard)/productos/[id]/page               → Detalle + gestión de tallas
```

### UI — Componentes requeridos

- **Lista productos:** Tabla con filtros por brand y línea — SKU base, nombre, tallas disponibles, precio, estado
- **Crear producto:** Página nueva — selección brand, selección línea, campos base
- **Gestión tallas:** En detalle del producto — tabla de tallas + botón "Agregar talla" + bulk creator (rango 35-45 de una vez)
- **Lista líneas:** Tabla separada — brand, code, nombre, # productos

### Criterio de done

- [ ] CRUD de líneas de producto
- [ ] CRUD de productos por línea
- [ ] Bulk creation de tallas (rango numérico o lista)
- [ ] SKU auto-generado: `{sku_base}-{size}` validado como único
- [ ] Filtros por brand y línea en lista principal

---

## MÓDULO 6 — Inventario

**Nombre técnico:** `inventory`
**App Django:** `backend/apps/inventory/` — **NUEVA APP** (no existe)
**Sprint sugerido:** 9-10
**Prioridad:** P1 — prerequisito para catálogo Rana Walk y gestión de stock por nodo

### Descripción

Registro de cantidad de producto disponible en cada nodo logístico. El inventario
es dinámico: se actualiza con entradas (transfers recibidos), salidas (ventas/despachos)
y ajustes manuales del CEO.

### Modelo Django

```python
# backend/apps/inventory/models.py

class InventoryRecord(models.Model):
    """Stock actual por SKU por nodo"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    node = models.ForeignKey('nodes.LogisticNode', on_delete=models.PROTECT)
    product_size = models.ForeignKey('products.ProductSize', on_delete=models.PROTECT)
    quantity = models.IntegerField(default=0)          # cantidad disponible
    quantity_reserved = models.IntegerField(default=0) # reservado en expedientes activos
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [['node', 'product_size']]

    @property
    def quantity_available(self):
        return self.quantity - self.quantity_reserved


class InventoryMovement(models.Model):
    """Log inmutable de cada movimiento de inventario"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    node = models.ForeignKey('nodes.LogisticNode', on_delete=models.PROTECT)
    product_size = models.ForeignKey('products.ProductSize', on_delete=models.PROTECT)
    movement_type = models.CharField(
        max_length=20,
        choices=[
            ('entrada', 'Entrada'),
            ('salida', 'Salida'),
            ('ajuste', 'Ajuste Manual'),
            ('reserva', 'Reserva'),
            ('liberacion', 'Liberación de Reserva'),
        ]
    )
    quantity = models.IntegerField()                   # positivo = entrada, negativo = salida
    reference = models.CharField(max_length=100, blank=True)  # ID de transfer, expediente
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey('users.MWTUser', on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
```

### Endpoints Backend

| Método | Endpoint | Descripción | Auth |
|--------|----------|-------------|------|
| GET | `/api/inventory/` | Stock actual (filtrar por nodo, brand, línea) | Auth |
| GET | `/api/inventory/{node_id}/` | Stock de un nodo específico | Auth |
| POST | `/api/inventory/adjust/` | Ajuste manual de stock | CEO |
| GET | `/api/inventory/movements/` | Historial movimientos | Auth |
| GET | `/api/inventory/alerts/` | SKUs con stock bajo el mínimo configurado | Auth |
| GET | `/api/inventory/summary/` | Resumen total por brand y nodo | Auth |

### Rutas Frontend (consola.mwt.one)

```
[lang]/(mwt)/(dashboard)/inventario/page                   → Vista general stock por nodo
[lang]/(mwt)/(dashboard)/inventario/[node_id]/page         → Stock detallado de un nodo
[lang]/(mwt)/(dashboard)/inventario/movimientos/page       → Historial movimientos
[lang]/(mwt)/(dashboard)/inventario/ajuste/page            → Formulario ajuste manual
```

### UI — Componentes requeridos

- **Vista general:** Tabla matriz — nodos en columnas, SKUs en filas — cantidad disponible/reservada
- **Stock por nodo:** Tabla filtrable por brand y línea — SKU, talla, disponible, reservado, total
- **Ajuste manual:** Drawer — selección nodo, selección SKU, cantidad, notas, referencia
- **Historial movimientos:** Tabla con filtros — fecha, nodo, SKU, tipo movimiento, usuario
- **Alertas stock bajo:** Badge en el menú lateral cuando hay SKUs con stock < mínimo

### Criterio de done

- [ ] Vista de stock en tiempo real por nodo
- [ ] Ajuste manual desde consola con trazabilidad
- [ ] Historial de movimientos inmutable (log)
- [ ] Alertas de stock bajo visibles en la UI
- [ ] `quantity_available = quantity - quantity_reserved` calculado en backend

---

## MÓDULO 7 — Nodo Logístico

**Nombre técnico:** `nodes`
**App Django:** `backend/apps/nodes/` — **NUEVA APP** (transfers lo referencia pero app no confirmada)
**Sprint sugerido:** 8 (antes de Inventory y Transfers UI)
**Prioridad:** P0 — prerequisito para inventario, transfers y Rana Walk

### Descripción

Los nodos logísticos son los puntos físicos donde existe producto: bodegas, almacenes,
tiendas, centros de distribución. Cada transfer mueve producto entre nodos. El inventario
vive en nodos. Un nodo puede ser propiedad de MWT o de un cliente/proveedor.

### Modelo Django

```python
# backend/apps/nodes/models.py

class LogisticNode(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    code = models.CharField(max_length=20, unique=True)       # 'BOD-CR-01', 'BOD-USA-MIA'
    name = models.CharField(max_length=100)
    node_type = models.CharField(
        max_length=20,
        choices=[
            ('bodega_mwt', 'Bodega MWT'),
            ('bodega_cliente', 'Bodega Cliente'),
            ('distribuidor', 'Distribuidor'),
            ('tienda', 'Tienda'),
            ('fba', 'Amazon FBA'),
            ('dtc', 'Direct-to-Consumer'),
            ('aduana', 'Aduana / Puerto'),
        ]
    )
    country = models.CharField(max_length=3)                  # ISO 3166-1 alpha-3
    city = models.CharField(max_length=100, blank=True)
    address = models.TextField(blank=True)
    owner = models.CharField(
        max_length=20,
        choices=[('mwt', 'MWT'), ('client', 'Cliente'), ('third_party', 'Tercero')]
    )
    associated_brand = models.ForeignKey(
        'brands.Brand', on_delete=models.SET_NULL, null=True, blank=True
    )
    contact_name = models.CharField(max_length=100, blank=True)
    contact_email = models.EmailField(blank=True)
    contact_phone = models.CharField(max_length=30, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
```

### Endpoints Backend

| Método | Endpoint | Descripción | Auth |
|--------|----------|-------------|------|
| GET | `/api/nodes/` | Listar nodos activos | Auth |
| POST | `/api/nodes/` | Crear nodo | CEO |
| GET | `/api/nodes/{id}/` | Detalle nodo | Auth |
| PATCH | `/api/nodes/{id}/` | Editar nodo | CEO |
| POST | `/api/nodes/{id}/deactivate/` | Desactivar nodo (soft) | CEO |
| GET | `/api/nodes/{id}/inventory/` | Stock actual en este nodo | Auth |
| GET | `/api/nodes/{id}/transfers/` | Transfers que involucran este nodo | Auth |

### Rutas Frontend (consola.mwt.one)

```
[lang]/(mwt)/(dashboard)/nodos/page              → Lista de nodos logísticos
[lang]/(mwt)/(dashboard)/nodos/nuevo/page        → Crear nodo
[lang]/(mwt)/(dashboard)/nodos/[id]/page         → Detalle + inventario + transfers
```

### UI — Componentes requeridos

- **Lista nodos:** Tabla — código, nombre, tipo, país, ciudad, dueño, brand asociada, estado
- **Crear nodo:** Página nueva — todos los campos del modelo
- **Detalle nodo:** Datos + tab "Inventario" (stock actual) + tab "Transfers" (movimientos recientes)
- **Mapa visual (futuro):** Pins en mapa con cantidad de stock por nodo (post-MVP)

### Criterio de done

- [ ] CRUD completo desde consola
- [ ] `GET /api/nodes/` usado por transfers, inventario y expedientes donde aplique
- [ ] Detalle muestra stock actual e historial de transfers del nodo
- [ ] Nodo inactivo no disponible como destino en nuevos transfers

---

## Resumen de dependencias entre módulos

```
Módulo 4 (Brands)       → prerequisito para: Módulo 5 (Productos), Módulo 7 (Nodos)
Módulo 7 (Nodos)        → prerequisito para: Módulo 6 (Inventario), Transfers UI (Sprint 8)
Módulo 5 (Productos)    → prerequisito para: Módulo 6 (Inventario), catálogo Rana Walk
Módulo 6 (Inventario)   → prerequisito para: catálogo Rana Walk en consola
Módulo 1 (Grupos)       → prerequisito para: Módulo 3 (Usuarios), RBAC real
Módulo 2 (Clientes)     → ya usado en Expedientes (S7-01) — backend existe, falta UI
Módulo 3 (Usuarios)     → prerequisito para: multi-usuario, RBAC
```

### Orden recomendado de implementación

```
Sprint 8:  Módulo 7 (Nodos) · Módulo 4 (Brands UI) · Módulo 2 (Clientes UI) · Módulo 1 (Grupos)
Sprint 9:  Módulo 3 (Usuarios) · Módulo 5 (Productos)
Sprint 10: Módulo 6 (Inventario)
```

---

## Qué revisó Claude para generar este documento

| Fuente | Hallazgo |
|--------|----------|
| `backend/apps/` directory | Apps existentes: brands ✅, core ✅, expedientes ✅, integrations ✅, liquidations ✅, qr ✅, transfers ✅ |
| `backend/apps/brands/` | App existe — modelo real debe verificarse antes de Sprint 8 |
| `frontend/src/` | Next.js 14 App Router con i18n confirmado |
| Sprint 7 (ASANA_TASK_SPRINT7) | `GET /api/clients/` ya referenciado — confirma que clients existe pero sin UI |
| Sprint 6 (LOTE_SM_SPRINT6) | 54 SKUs Rana Walk + nodos CR/USA + transfers confirman necesidad de products, inventory, nodes |
| `generate_brands_fixtures.py` | Brands son fixture estático — necesitan UI admin |

---

## Instrucciones para Claude en sprints futuros

```
CUANDO leas este archivo al inicio de un sprint, debes:

1. Identificar qué módulo(s) de esta lista aplican al sprint actual
2. LEER el modelo Django existente (si ya existe) antes de crear endpoints — no inventar campos
3. Respetar las convenciones de UI: drawer lateral para CRUD, página nueva solo para
   formularios complejos (igual que expedientes/nuevo)
4. Los endpoints deben seguir el patrón /api/{recurso}/ con trailing slash
5. Verificar dependencias: si un módulo requiere otro, confirmar que ese otro existe primero
6. El sistema de permisos en MVP = CEO superuser. NO implementar guards de RBAC
   en el frontend durante Sprints 8-9 salvo que el CEO lo solicite explícitamente
7. Todos los nuevos modelos Django deben tener: UUID pk, is_active, created_at,
   updated_at, deleted_at (soft delete)
8. Respetar ENT_PLAT_DESIGN_TOKENS para estilos
```

---

Stamp: DRAFT v1.0 — generado 2026-03-12
Origen: Revisión base de conocimiento MWT ONE + auditoría estructura github.com/Ale241302/mwt_one + instrucciones CEO
