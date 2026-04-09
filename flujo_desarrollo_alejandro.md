# Flujo de Desarrollo — Alejandro
## Plataforma MWT ONE · consola.mwt.one

**Documento:** Guía de orden de desarrollo de módulos del sistema  
**Repositorio:** [github.com/Ale241302/mwt_one](https://github.com/Ale241302/mwt_one)  
**Fecha:** 2026-04-08  
**Estado:** ACTIVO — referencia principal para sprints Alejandro

---

## Propósito

Este archivo define el **orden oficial de desarrollo** de los módulos del sistema MWT ONE,
estableciendo qué debe construirse primero, qué depende de qué, y cuáles módulos son nuevos
(no existen aún en el backend). Es la referencia que Alejandro consulta al inicio de cada sprint.

---

## Módulos del Sistema — Estado Actual

### Apps Django existentes en `backend/apps/`

| App | Backend | Frontend Consola |
|-----|---------|-----------------| 
| `expedientes` | ✅ 39 endpoints — 100% funcional | ✅ Completado Sprint 7 |
| `brands` | ✅ Existe (fixtures + generate_brands_fixtures.py) | ❌ Sin UI en consola |
| `transfers` | ✅ Existe app | ❌ Sin UI en consola |
| `liquidations` | ✅ Existe app | ❌ Sin UI |
| `qr` | ✅ Existe app | ❌ Sin UI |
| `core` | ✅ Existe app (base) | — |
| `integrations` | ✅ Existe app | — |

### Apps Django AUSENTES (deben crearse)

| App | Motivo |
|-----|--------|
| `products` | No existe — líneas, tallas, referencias de producto |
| `sizes` | Parte del catálogo de producto — tallas por SKU |
| `nodes` | Referenciado en transfers pero sin app/modelo dedicado confirmado |
| `inventory` | No existe — stock por nodo logístico |
| `suppliers` | No existe — proveedores de producto |
| `clients` | Existe referenciado en expedientes pero sin app dedicada confirmada |
| `users` | Django usa auth.User base pero sin modelo extendido confirmado |
| `groups_permissions` | Django tiene Group nativo pero sin API REST expuesta |
| `finance` | No existe — pagos, facturas, liquidaciones y reportes financieros |
| `ai_agents` | No existe — configuración de agentes IA (OpenAI, Google, Anthropic) |

---

## Convenciones Invariables para Todos los Módulos

```
REGLAS QUE CLAUDE Y ALEJANDRO DEBEN RESPETAR EN CADA MÓDULO:

1. Backend:   Django REST Framework · ModelViewSet o APIView · JWT auth
2. Frontend:  Next.js 14 App Router · [lang]/(mwt)/(dashboard)/{modulo}/
3. Formularios: Drawer lateral para crear/editar — SALVO casos indicados
4. Listados:  Tabla con paginación, búsqueda y filtros
5. Acciones destructivas: Modal de confirmación con razón obligatoria
6. Design tokens: ENT_PLAT_DESIGN_TOKENS en todos los componentes
7. Permisos:  MVP = CEO superuser. RBAC real activa post-MVP (Módulo 11)
8. Endpoints: Seguir patrón /api/{recurso}/ con trailing slash
9. Soft delete: Todos los modelos deben tener is_active + deleted_at
10. UUIDs:    Todos los modelos usan UUID como PK
```

---

## Orden de Desarrollo — Módulos

> Los módulos se listan en el orden exacto en que deben desarrollarse.
> Un módulo no debe iniciarse hasta que sus dependencias estén completadas.

---

### Módulo 1 — Brands (Marcas)

**Nombre técnico:** `brands`  
**App Django:** `backend/apps/brands/` — **YA EXISTE** en el backend  
**Estado backend:** ✅ Existe (fixtures). Debe verificarse modelo real antes de implementar UI.  
**Estado frontend:** ❌ Sin UI en consola  
**Prioridad:** P1 — backend existe, falta UI  

**Descripción:**  
Marcas de producto que opera MWT. Actualmente existen como fixtures (`marluvas`, `tecmater`, `ranawalk`).
El campo `brand` en expedientes referencia este modelo. Primer módulo a completar por ser prerequisito
de Productos, Nodos y Usuarios.

**Rutas Frontend:**
```
[lang]/(mwt)/(dashboard)/configuracion/brands/page        → Lista brands
[lang]/(mwt)/(dashboard)/configuracion/brands/nueva/page  → Crear brand
[lang]/(mwt)/(dashboard)/configuracion/brands/[id]/page   → Detalle + editar
```

**Criterio de done:**
- [ ] CRUD desde consola (respetando modelo existente en `backend/apps/brands/`)
- [ ] `GET /api/brands/` retorna lista compatible con formulario crear expediente
- [ ] Slug único validado al crear
- [ ] Brand inactiva no aparece en selects de expediente

**Dependencias:** Ninguna — es la base del sistema  
**Desbloquea:** Módulo 2 (Productos), Módulo 3 (Nodos), Módulo 10 (Usuarios)

---

### Módulo 2 — Productos

**Nombre técnico:** `products`  
**App Django:** `backend/apps/products/` — **NUEVA APP** (no existe)  
**Estado backend:** ❌ Debe crearse  
**Estado frontend:** ❌ Sin UI  
**Prioridad:** P1 — prerequisito para inventario y catálogo Rana Walk  

**Descripción:**  
Catálogo de productos por brand. Cada producto tiene: línea de producto (ej: GOL, VEL, ORB, LEO, BIS),
referencia/SKU base, precio base por moneda. Las tallas se manejan en el Módulo 2b (ver abajo).

**Modelos clave:** `ProductLine`, `Product`

**Rutas Frontend:**
```
[lang]/(mwt)/(dashboard)/productos/page           → Lista productos (filtrable por brand/línea)
[lang]/(mwt)/(dashboard)/productos/lineas/page    → Lista líneas de producto
[lang]/(mwt)/(dashboard)/productos/nuevo/page     → Crear producto
[lang]/(mwt)/(dashboard)/productos/[id]/page      → Detalle producto
```

**Criterio de done:**
- [ ] CRUD de líneas de producto por brand
- [ ] CRUD de productos por línea
- [ ] SKU base único validado
- [ ] Filtros por brand y línea en lista principal

**Dependencias:** Módulo 1 (Brands)  
**Desbloquea:** Módulo 2b (Tallas), Módulo 4 (Inventario)

---

### Módulo 2b — Tallas

**Nombre técnico:** `product_sizes`  
**App Django:** Dentro de `backend/apps/products/` — modelo `ProductSize`  
**Estado backend:** ❌ Debe crearse junto con Productos  
**Estado frontend:** ❌ Sin UI  
**Prioridad:** P1 — unidad mínima de inventario (SKU por talla)  

**Descripción:**  
Extensión del módulo Productos. Cada producto tiene tallas asociadas que generan SKUs únicos
(`{sku_base}-{size}`). Las tallas son la unidad mínima que se mueve en inventario y transfers.
Ejemplo: Rana Walk maneja tallas del 35 al 45 (numéricas) y S/M/L (por talla).

**Modelo clave:** `ProductSize`
```python
class ProductSize(models.Model):
    id           = UUIDField(primary_key=True)
    product      = ForeignKey(Product, related_name='sizes')
    size         = CharField(max_length=10)   # '35', '36', ..., 'S', 'M', 'L'
    sku          = CharField(max_length=60, unique=True)
    is_active    = BooleanField(default=True)
```

**UI requerida (dentro del detalle de producto):**
- Tabla de tallas del producto: talla, SKU completo, estado activo
- Botón "Agregar talla" — input rápido
- Bulk creator: rango numérico (35–45) o lista de tallas de una vez
- Desactivar talla individual (soft delete)

**Criterio de done:**
- [ ] Tallas visibles y editables dentro del detalle de cada producto
- [ ] Bulk creation de tallas (rango numérico o lista personalizada)
- [ ] SKU auto-generado `{sku_base}-{size}` validado como único
- [ ] Talla inactiva no aparece en selects de inventario o transfers

**Dependencias:** Módulo 2 (Productos)  
**Desbloquea:** Módulo 4 (Inventario), Módulo 7 (Transfers)

---

### Módulo 3 — Nodos Logísticos

**Nombre técnico:** `nodes`  
**App Django:** `backend/apps/nodes/` — **NUEVA APP**  
**Estado backend:** ❌ Referenciado en transfers pero app no confirmada  
**Estado frontend:** ❌ Sin UI  
**Prioridad:** P0 — prerequisito para Inventario y Transfers UI  

**Descripción:**  
Puntos físicos donde existe producto: bodegas, almacenes, tiendas, centros de distribución.
Cada transfer mueve producto entre nodos. El inventario vive en nodos.
Tipos: `bodega_mwt`, `bodega_cliente`, `distribuidor`, `tienda`, `fba`, `dtc`, `aduana`.

**Rutas Frontend:**
```
[lang]/(mwt)/(dashboard)/nodos/page          → Lista nodos logísticos
[lang]/(mwt)/(dashboard)/nodos/nuevo/page    → Crear nodo
[lang]/(mwt)/(dashboard)/nodos/[id]/page     → Detalle + inventario + transfers
```

**Criterio de done:**
- [ ] CRUD completo desde consola
- [ ] `GET /api/nodes/` usado por transfers, inventario y expedientes
- [ ] Detalle muestra stock actual e historial de transfers del nodo
- [ ] Nodo inactivo no disponible como destino en nuevos transfers

**Dependencias:** Módulo 1 (Brands) — nodo puede asociarse a una brand  
**Desbloquea:** Módulo 4 (Inventario), Módulo 7 (Transfers)

---

### Módulo 4 — Inventario

**Nombre técnico:** `inventory`  
**App Django:** `backend/apps/inventory/` — **NUEVA APP** (no existe)  
**Estado backend:** ❌ Debe crearse  
**Estado frontend:** ❌ Sin UI  
**Prioridad:** P1 — prerequisito para catálogo Rana Walk y gestión de stock  

**Descripción:**  
Stock actual de producto (por SKU con talla) en cada nodo logístico. Se actualiza con entradas
(transfers recibidos), salidas (ventas/despachos) y ajustes manuales. Tiene log inmutable de movimientos.

**Modelos clave:** `InventoryRecord`, `InventoryMovement`

**Rutas Frontend:**
```
[lang]/(mwt)/(dashboard)/inventario/page                → Vista general stock por nodo
[lang]/(mwt)/(dashboard)/inventario/[node_id]/page      → Stock detallado de un nodo
[lang]/(mwt)/(dashboard)/inventario/movimientos/page    → Historial movimientos
[lang]/(mwt)/(dashboard)/inventario/ajuste/page         → Formulario ajuste manual
```

**Criterio de done:**
- [ ] Vista de stock en tiempo real por nodo
- [ ] Ajuste manual desde consola con trazabilidad
- [ ] Historial de movimientos inmutable (log)
- [ ] Alertas de stock bajo visibles en la UI
- [ ] `quantity_available = quantity - quantity_reserved` calculado en backend

**Dependencias:** Módulo 2b (Tallas), Módulo 3 (Nodos)  
**Desbloquea:** Módulo 7 (Transfers), catálogo Rana Walk

---

### Módulo 5 — Proveedores

**Nombre técnico:** `suppliers`  
**App Django:** `backend/apps/suppliers/` — **NUEVA APP** (no existe)  
**Estado backend:** ❌ Debe crearse  
**Estado frontend:** ❌ Sin UI  
**Prioridad:** P1 — gestión de proveedores de producto y logística  

**Descripción:**  
Gestión de los proveedores con quienes MWT opera: fábricas, agentes de aduana, transportistas,
distribuidores. Cada proveedor puede asociarse a brands específicas. Se usa en expedientes
para tracking de costos de origen.

**Modelo clave:**
```python
class Supplier(models.Model):
    id           = UUIDField(primary_key=True)
    name         = CharField(max_length=200)
    legal_name   = CharField(max_length=200, blank=True)
    tax_id       = CharField(max_length=50, blank=True)
    country      = CharField(max_length=3)               # ISO 3166-1 alpha-3
    supplier_type = CharField(choices=[
        ('fabrica', 'Fábrica'),
        ('agente', 'Agente Aduanal'),
        ('transporte', 'Transporte'),
        ('distribuidor', 'Distribuidor'),
        ('otro', 'Otro'),
    ])
    email        = EmailField(blank=True)
    phone        = CharField(max_length=30, blank=True)
    contact_name = CharField(max_length=100, blank=True)
    currency     = CharField(max_length=3, default='USD')
    payment_days = PositiveIntegerField(default=30)
    notes        = TextField(blank=True)
    is_active    = BooleanField(default=True)
    created_at   = DateTimeField(auto_now_add=True)
    updated_at   = DateTimeField(auto_now=True)
    deleted_at   = DateTimeField(null=True, blank=True)
```

**Rutas Frontend:**
```
[lang]/(mwt)/(dashboard)/proveedores/page          → Lista proveedores
[lang]/(mwt)/(dashboard)/proveedores/nuevo/page    → Crear proveedor
[lang]/(mwt)/(dashboard)/proveedores/[id]/page     → Detalle + historial
```

**Criterio de done:**
- [ ] CRUD completo desde consola
- [ ] Filtro por tipo de proveedor y país
- [ ] `GET /api/suppliers/` disponible para uso en expedientes
- [ ] Proveedor inactivo no aparece en selects de expediente

**Dependencias:** Módulo 1 (Brands)  
**Desbloquea:** Módulo 7 (Transfers), Módulo 9 (Expedientes — campo proveedor)

---

### Módulo 6 — Inventarios (Vista Consolidada)

> **Nota:** Este módulo es la vista consolidada y de reportes del inventario.
> Depende de que el Módulo 4 (Inventario base) esté completado.
> Incluye: resumen por brand, alertas globales, exportación, y dashboard de stock.

**Nombre técnico:** `inventory_dashboard`  
**App Django:** Extensión de `backend/apps/inventory/` — endpoints adicionales  
**Estado:** ❌ Pendiente — requiere Módulo 4  
**Prioridad:** P2 — mejora operativa post-inventario base  

**Funcionalidades adicionales:**
- Dashboard con KPIs de stock por brand y nodo
- Exportación CSV/Excel del inventario completo
- Alertas configurables de stock mínimo por SKU
- Comparativa de stock entre nodos
- Vista de rotación de inventario (SKUs sin movimiento en N días)

**Rutas Frontend adicionales:**
```
[lang]/(mwt)/(dashboard)/inventario/dashboard/page    → KPIs y resumen ejecutivo
[lang]/(mwt)/(dashboard)/inventario/exportar/page     → Exportación
[lang]/(mwt)/(dashboard)/inventario/alertas/page      → Configuración de alertas
```

**Dependencias:** Módulo 4 (Inventario base)  
**Desbloquea:** Reportes ejecutivos, auditorías de stock

---

### Módulo 7 — Transfers

**Nombre técnico:** `transfers`  
**App Django:** `backend/apps/transfers/` — **YA EXISTE** en el backend  
**Estado backend:** ✅ App existe  
**Estado frontend:** ❌ Sin UI en consola  
**Prioridad:** P1 — movimiento de producto entre nodos  

**Descripción:**  
Registro de movimientos de producto entre nodos logísticos. Un transfer tiene:
origen, destino, lista de SKUs con cantidades, estado del envío, documentos adjuntos.
Al completarse, actualiza el inventario de ambos nodos automáticamente.

**Rutas Frontend:**
```
[lang]/(mwt)/(dashboard)/transfers/page          → Lista transfers
[lang]/(mwt)/(dashboard)/transfers/nuevo/page    → Crear transfer
[lang]/(mwt)/(dashboard)/transfers/[id]/page     → Detalle + tracking
```

**Criterio de done:**
- [ ] CRUD de transfers desde consola
- [ ] Al completar transfer: inventario origen decrece, destino aumenta (automático)
- [ ] Estados: `borrador → en_transito → recibido → cancelado`
- [ ] Vista de líneas de transfer con SKU, talla, cantidad
- [ ] Adjuntar documentos (guía de transporte, packing list)

**Dependencias:** Módulo 2b (Tallas), Módulo 3 (Nodos), Módulo 4 (Inventario)  
**Desbloquea:** Módulo 6 (Inventarios consolidado), trazabilidad completa

---

### Módulo 8 — Clientes

**Nombre técnico:** `clients`  
**App Django:** `backend/apps/clients/` — **NUEVA APP DEDICADA**  
**Estado backend:** ⚠️ `GET /api/clients/` existe referenciado en Sprint 7 pero sin app dedicada  
**Estado frontend:** ❌ Sin UI  
**Prioridad:** P0 — ya se usa en expedientes  

**Descripción:**  
Gestión de clientes con quienes MWT opera expedientes. El endpoint `GET /api/clients/`
ya es consumido en el formulario de crear expediente (Sprint 7). Requiere app dedicada
con modelo completo y UI de administración.

**Modelo clave:**
```python
class Client(models.Model):
    id           = UUIDField(primary_key=True)
    name         = CharField(max_length=200)
    legal_name   = CharField(max_length=200, blank=True)
    tax_id       = CharField(max_length=50, blank=True)    # NIT / RUT / TIN
    country      = CharField(max_length=3)                 # ISO 3166-1 alpha-3
    email        = EmailField(blank=True)
    phone        = CharField(max_length=30, blank=True)
    address      = TextField(blank=True)
    credit_days  = PositiveIntegerField(default=30)
    credit_limit = DecimalField(max_digits=12, decimal_places=2, null=True)
    currency     = CharField(max_length=3, default='USD')
    notes        = TextField(blank=True)
    is_active    = BooleanField(default=True)
    created_at   = DateTimeField(auto_now_add=True)
    updated_at   = DateTimeField(auto_now=True)
    deleted_at   = DateTimeField(null=True, blank=True)
```

**Rutas Frontend:**
```
[lang]/(mwt)/(dashboard)/clientes/page          → Lista clientes
[lang]/(mwt)/(dashboard)/clientes/nuevo/page    → Crear cliente
[lang]/(mwt)/(dashboard)/clientes/[id]/page     → Detalle + historial expedientes
```

**Criterio de done:**
- [ ] CRUD completo desde consola
- [ ] `GET /api/clients/` retorna `[{ id, name }]` — compatible con S7-01
- [ ] Detalle muestra expedientes vinculados paginados
- [ ] Estado de crédito calculado (semáforo verde/amarillo/rojo)
- [ ] Cliente inactivo no aparece en el select de crear expediente

**Dependencias:** Módulo 7 (Transfers) — para relacionar expedientes  
**Desbloquea:** Módulo 9 (Expedientes — integración completa con clientes)

---

### Módulo 9 — Expedientes

**Nombre técnico:** `expedientes`  
**App Django:** `backend/apps/expedientes/` — **YA EXISTE — 100% funcional**  
**Estado backend:** ✅ 39 endpoints completos  
**Estado frontend:** ✅ Completado en Sprint 7  
**Prioridad:** Mejoras continuas — integración con nuevos módulos  

**Descripción:**  
Módulo central del sistema MWT ONE. Ya completado en Sprint 7. En esta fase se refiere
a mejoras de integración: vincular clientes (Módulo 8), proveedores (Módulo 5),
y nodos logísticos (Módulo 3) dentro del flujo de expediente.

**Mejoras pendientes en Expedientes (post Sprint 7):**
- [ ] Campo proveedor visible en expediente (vinculado con Módulo 5)
- [ ] Estado de crédito del cliente visible en detalle de expediente
- [ ] Links directos a nodo logístico de origen/destino
- [ ] Integración con inventario: reservar stock al crear expediente

**Dependencias:** Módulos 3, 5, 8  
**Nota:** El módulo base ya está completo. Esta entrada refiere a integraciones adicionales.

---

### Módulo 10 — Usuarios Portal & Consola

**Nombre técnico:** `users`  
**App Django:** `backend/apps/users/` — **NUEVA APP** (extender auth.User)  
**Estado backend:** ❌ Django usa auth.User base pero sin modelo extendido confirmado  
**Estado frontend:** ❌ Sin UI  
**Prioridad:** P1 — base para multi-usuario / RBAC real  

**Descripción:**  
Gestión de usuarios que acceden a la consola y/o al portal cliente. Cada usuario:
- Se asocia a una o más **brands** (organizaciones operativas)
- Se asocia a uno o más **grupos** (hereda permisos — requiere Módulo 11)
- Tiene credenciales de acceso (email + contraseña)
- Puede ser de tipo: operador interno, acceso portal cliente, logístico, financiero

**Modelo clave:**
```python
class MWTUser(AbstractUser):
    id               = UUIDField(primary_key=True)
    # username, email, groups heredados de AbstractUser
    phone            = CharField(max_length=30, blank=True)
    avatar_url       = URLField(blank=True)
    associated_brands = ManyToManyField('brands.Brand', blank=True)
    is_active        = BooleanField(default=True)
    created_at       = DateTimeField(auto_now_add=True)
    updated_at       = DateTimeField(auto_now=True)
    last_login_ip    = GenericIPAddressField(null=True, blank=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']
```

**Rutas Frontend:**
```
[lang]/(mwt)/(dashboard)/configuracion/usuarios/page          → Lista usuarios
[lang]/(mwt)/(dashboard)/configuracion/usuarios/nuevo/page    → Crear usuario
[lang]/(mwt)/(dashboard)/configuracion/usuarios/[id]/page     → Detalle + permisos
```

**Endpoints clave:**
```
GET    /api/users/                           → Listar usuarios
POST   /api/users/                           → Crear usuario
GET    /api/users/{id}/                      → Detalle usuario
PATCH  /api/users/{id}/                      → Editar usuario
POST   /api/users/{id}/deactivate/           → Desactivar usuario (soft)
POST   /api/users/{id}/reset-password/       → Resetear contraseña
POST   /api/users/{id}/groups/               → Asignar grupos
POST   /api/users/{id}/brands/               → Asociar brands
GET    /api/auth/me/                         → Perfil usuario autenticado
POST   /api/auth/login/                      → Login (JWT)
POST   /api/auth/logout/                     → Logout (blacklist token)
POST   /api/auth/refresh/                    → Refresh token JWT
```

**Criterio de done:**
- [ ] CRUD completo desde consola
- [ ] Usuario puede asociarse a ≥1 grupo y ≥1 brand
- [ ] Usuario inactivo no puede hacer login
- [ ] Reset de contraseña funcional
- [ ] `GET /api/auth/me/` retorna perfil + grupos + brands del usuario autenticado

**Dependencias:** Módulo 1 (Brands), Módulo 11 (Roles & Permisos)  
**Desbloquea:** Multi-usuario real en la plataforma, RBAC activo

---

### Módulo 11 — Roles & Permisos

**Nombre técnico:** `permission_groups`  
**App Django:** Extender `django.contrib.auth.Group` con metadatos propios  
**Estado backend:** ❌ Django tiene Group nativo pero sin API REST expuesta  
**Estado frontend:** ❌ Sin UI  
**Prioridad:** P1 — base del sistema RBAC (debe existir antes de activar multi-usuario real)  

**Descripción:**  
Sistema de grupos que define qué puede hacer cada tipo de usuario en la consola.
Un grupo agrupa un conjunto de permisos de Django (`django.contrib.auth.Permission`).
Los usuarios se asocian a uno o más grupos y heredan sus permisos.

**Grupos base sugeridos (seed automático en migrations):**

| Grupo | Descripción |
|-------|-------------|
| `superadmin` | Acceso total — equivalente al CEO actual |
| `operador` | Crear/avanzar expedientes, registrar costos — sin acceso a finanzas |
| `financiero` | Ver costos, registrar pagos, emitir facturas |
| `visor` | Solo lectura — sin acciones destructivas |
| `logistica` | Gestión de nodos, inventario, transfers |

**Modelo clave:**
```python
class MWTGroup(models.Model):
    id          = UUIDField(primary_key=True)
    auth_group  = OneToOneField('auth.Group', on_delete=CASCADE, related_name='mwt_group')
    description = TextField(blank=True)
    is_active   = BooleanField(default=True)
    created_at  = DateTimeField(auto_now_add=True)
    updated_at  = DateTimeField(auto_now=True)
```

**Rutas Frontend:**
```
[lang]/(mwt)/(dashboard)/configuracion/grupos/page          → Lista de grupos
[lang]/(mwt)/(dashboard)/configuracion/grupos/nuevo/page    → Crear grupo
[lang]/(mwt)/(dashboard)/configuracion/grupos/[id]/page     → Detalle + editar permisos
```

**Endpoints clave:**
```
GET    /api/groups/                              → Listar todos los grupos
POST   /api/groups/                              → Crear grupo nuevo
GET    /api/groups/{id}/                         → Detalle de grupo
PATCH  /api/groups/{id}/                         → Editar nombre/descripción
DELETE /api/groups/{id}/                         → Desactivar grupo (soft)
GET    /api/groups/{id}/permissions/             → Listar permisos del grupo
POST   /api/groups/{id}/permissions/             → Asignar permisos al grupo
DELETE /api/groups/{id}/permissions/{perm_id}/   → Quitar permiso del grupo
GET    /api/permissions/                         → Listar todos los permisos disponibles
```

**Criterio de done:**
- [ ] CRUD completo de grupos funcional desde consola
- [ ] Checklist de permisos disponibles cargado desde `GET /api/permissions/`
- [ ] Asignación/revocación de permisos en tiempo real
- [ ] Soft delete: grupos inactivos no aparecen en selects de usuario
- [ ] Grupos base seed creados automáticamente en migrations

**Dependencias:** Módulo 10 (Usuarios)  
**Desbloquea:** RBAC real activo en toda la plataforma, Módulo 12 (Financiero — permisos del rol `financiero`)

---

### Módulo 12 — Financiero

**Nombre técnico:** `finance`  
**App Django:** `backend/apps/finance/` — **NUEVA APP** (no existe)  
**Estado backend:** ❌ Debe crearse. La app `liquidations` existente puede ser base o fusionarse.  
**Estado frontend:** ❌ Sin UI  
**Prioridad:** P1 — cierre del ciclo operativo: cobros, pagos y liquidaciones  

**Descripción:**  
Gestión financiera de la operación MWT. Centraliza: facturas a clientes, pagos a proveedores,
liquidaciones de expedientes y reportes de flujo de caja. Es el último módulo en el orden
porque consume datos de todos los anteriores (expedientes, clientes, proveedores, transfers).
El rol `financiero` del Módulo 11 es quien opera este módulo en producción.

**Modelos clave:**
```python
class Invoice(models.Model):
    """Factura emitida a un cliente (cuentas por cobrar)"""
    id              = UUIDField(primary_key=True)
    expediente      = ForeignKey('expedientes.Expediente', on_delete=PROTECT)
    client          = ForeignKey('clients.Client', on_delete=PROTECT)
    invoice_number  = CharField(max_length=50, unique=True)
    currency        = CharField(max_length=3, default='USD')
    subtotal        = DecimalField(max_digits=14, decimal_places=2)
    tax             = DecimalField(max_digits=14, decimal_places=2, default=0)
    total           = DecimalField(max_digits=14, decimal_places=2)
    status          = CharField(choices=[
                          ('borrador', 'Borrador'),
                          ('emitida', 'Emitida'),
                          ('pagada', 'Pagada'),
                          ('vencida', 'Vencida'),
                          ('anulada', 'Anulada'),
                      ])
    issued_at       = DateField(null=True)
    due_at          = DateField(null=True)        # issued_at + client.credit_days
    paid_at         = DateTimeField(null=True)
    notes           = TextField(blank=True)
    is_active       = BooleanField(default=True)
    created_at      = DateTimeField(auto_now_add=True)
    updated_at      = DateTimeField(auto_now=True)
    deleted_at      = DateTimeField(null=True, blank=True)


class Payment(models.Model):
    """Pago recibido de un cliente (puede cubrir una o varias facturas)"""
    id              = UUIDField(primary_key=True)
    client          = ForeignKey('clients.Client', on_delete=PROTECT)
    amount          = DecimalField(max_digits=14, decimal_places=2)
    currency        = CharField(max_length=3, default='USD')
    payment_method  = CharField(choices=[
                          ('transferencia', 'Transferencia Bancaria'),
                          ('cheque', 'Cheque'),
                          ('efectivo', 'Efectivo'),
                          ('otro', 'Otro'),
                      ])
    reference       = CharField(max_length=100, blank=True)  # Núm. de transferencia
    payment_date    = DateField()
    invoices        = ManyToManyField(Invoice, through='PaymentInvoice')
    notes           = TextField(blank=True)
    created_by      = ForeignKey('users.MWTUser', on_delete=SET_NULL, null=True)
    created_at      = DateTimeField(auto_now_add=True)


class SupplierPayment(models.Model):
    """Pago realizado a un proveedor (cuentas por pagar)"""
    id              = UUIDField(primary_key=True)
    supplier        = ForeignKey('suppliers.Supplier', on_delete=PROTECT)
    expediente      = ForeignKey('expedientes.Expediente', on_delete=PROTECT, null=True)
    amount          = DecimalField(max_digits=14, decimal_places=2)
    currency        = CharField(max_length=3, default='USD')
    payment_method  = CharField(max_length=30)
    reference       = CharField(max_length=100, blank=True)
    payment_date    = DateField()
    notes           = TextField(blank=True)
    created_by      = ForeignKey('users.MWTUser', on_delete=SET_NULL, null=True)
    created_at      = DateTimeField(auto_now_add=True)


class Liquidation(models.Model):
    """Liquidación final de un expediente — puede fusionarse con app liquidations existente"""
    id              = UUIDField(primary_key=True)
    expediente      = OneToOneField('expedientes.Expediente', on_delete=PROTECT)
    total_ingresos  = DecimalField(max_digits=14, decimal_places=2)
    total_costos    = DecimalField(max_digits=14, decimal_places=2)
    margen          = DecimalField(max_digits=14, decimal_places=2)  # ingresos - costos
    currency        = CharField(max_length=3, default='USD')
    status          = CharField(choices=[
                          ('borrador', 'Borrador'),
                          ('aprobada', 'Aprobada'),
                          ('cerrada', 'Cerrada'),
                      ])
    approved_by     = ForeignKey('users.MWTUser', on_delete=SET_NULL, null=True)
    approved_at     = DateTimeField(null=True)
    created_at      = DateTimeField(auto_now_add=True)
    updated_at      = DateTimeField(auto_now=True)
```

**Endpoints Backend:**

| Método | Endpoint | Descripción | Auth |
|--------|----------|-------------|------|
| GET | `/api/finance/invoices/` | Listar facturas (filtrar por cliente, estado, fecha) | Financiero |
| POST | `/api/finance/invoices/` | Crear factura | Financiero |
| GET | `/api/finance/invoices/{id}/` | Detalle factura | Financiero |
| PATCH | `/api/finance/invoices/{id}/` | Editar factura (solo si está en borrador) | Financiero |
| POST | `/api/finance/invoices/{id}/emit/` | Emitir factura (borrador → emitida) | Financiero |
| POST | `/api/finance/invoices/{id}/cancel/` | Anular factura | CEO |
| GET | `/api/finance/payments/` | Listar pagos de clientes | Financiero |
| POST | `/api/finance/payments/` | Registrar pago de cliente | Financiero |
| GET | `/api/finance/payments/{id}/` | Detalle de pago | Financiero |
| GET | `/api/finance/supplier-payments/` | Listar pagos a proveedores | Financiero |
| POST | `/api/finance/supplier-payments/` | Registrar pago a proveedor | Financiero |
| GET | `/api/finance/liquidations/` | Listar liquidaciones | Financiero |
| POST | `/api/finance/liquidations/` | Crear liquidación de expediente | Financiero |
| GET | `/api/finance/liquidations/{id}/` | Detalle liquidación | Financiero |
| POST | `/api/finance/liquidations/{id}/approve/` | Aprobar liquidación | CEO |
| GET | `/api/finance/dashboard/` | KPIs financieros: AR, AP, margen por brand | CEO |
| GET | `/api/finance/report/cash-flow/` | Flujo de caja por rango de fechas | CEO |
| GET | `/api/finance/report/aging/` | Reporte de antigedad de cartera (AR aging) | CEO |

**Rutas Frontend:**
```
[lang]/(mwt)/(dashboard)/financiero/page                        → Dashboard financiero (KPIs)
[lang]/(mwt)/(dashboard)/financiero/facturas/page               → Lista de facturas
[lang]/(mwt)/(dashboard)/financiero/facturas/nueva/page         → Crear factura
[lang]/(mwt)/(dashboard)/financiero/facturas/[id]/page          → Detalle factura
[lang]/(mwt)/(dashboard)/financiero/pagos/page                  → Pagos recibidos de clientes
[lang]/(mwt)/(dashboard)/financiero/pagos/nuevo/page            → Registrar pago
[lang]/(mwt)/(dashboard)/financiero/pagos-proveedor/page        → Pagos a proveedores
[lang]/(mwt)/(dashboard)/financiero/liquidaciones/page          → Lista liquidaciones
[lang]/(mwt)/(dashboard)/financiero/liquidaciones/[id]/page     → Detalle liquidación
[lang]/(mwt)/(dashboard)/financiero/reportes/flujo-caja/page    → Reporte flujo de caja
[lang]/(mwt)/(dashboard)/financiero/reportes/aging/page         → AR Aging (cartera vencida)
```

**UI — Componentes requeridos:**

- **Dashboard financiero:** KPIs en cards — Cuentas por cobrar (AR) total, Cuentas por pagar (AP) total, Margen operativo del mes, Facturas vencidas (#)
- **Lista facturas:** Tabla — número, cliente, expediente, total, estado, fecha emisión, fecha vencimiento
- **Crear factura:** Página nueva — selección expediente (carga cliente automático), ítems de costo, totales
- **Detalle factura:** Vista completa + historial de pagos vinculados + botón emitir/anular
- **Registrar pago:** Drawer — cliente, monto, método, referencia, vinculación a facturas pendientes
- **Liquidaciones:** Tabla resumen por expediente — ingresos vs costos vs margen — semáforo de rentabilidad
- **Reporte aging:** Tabla de cartera vencida agrupada por rango (0-30, 31-60, 61-90, +90 días)
- **Flujo de caja:** Gráfico de barras mensual — ingresos vs egresos (chart con ENT_PLAT_DESIGN_TOKENS)

**Criterio de done:**
- [ ] CRUD completo de facturas desde consola
- [ ] Flujo factura: `borrador → emitida → pagada` controlado desde UI
- [ ] Registro de pagos vinculado a facturas (un pago puede cubrir múltiples facturas)
- [ ] Registro de pagos a proveedores con referencia a expediente
- [ ] Liquidación de expediente con cálculo automático de margen
- [ ] Dashboard financiero con KPIs en tiempo real
- [ ] Reporte AR Aging exportable
- [ ] Reporte de flujo de caja por período
- [ ] Facturas vencidas disparan badge de alerta en menú lateral
- [ ] Solo usuario con rol `financiero` o `superadmin` puede ver y operar este módulo

**Nota sobre `liquidations` app existente:**  
Antes de crear `finance` desde cero, Claude debe leer `backend/apps/liquidations/` para evaluar
si el modelo existente puede extenderse o si se crea app paralela. Evitar duplicación de modelos.

**Dependencias:** Módulos 5 (Proveedores), 8 (Clientes), 9 (Expedientes), 10 (Usuarios), 11 (Roles & Permisos)  
**Desbloquea:** Cierre del ciclo operativo completo de MWT ONE, Módulo 13 (Agentes IA)

---

### Módulo 13 — Agentes IA

**Nombre técnico:** `ai_agents`  
**App Django:** `backend/apps/ai_agents/` — **NUEVA APP** (no existe)  
**Estado backend:** ❌ Debe crearse  
**Estado frontend:** ❌ Sin UI  
**Prioridad:** P2 — capacidades de automatización inteligente sobre la operación MWT  

**Descripción:**  
Módulo de configuración y gestión de agentes de inteligencia artificial que operan dentro
de la plataforma MWT ONE. Permite definir agentes con nombre, rol, prompt base, proveedor
de IA (OpenAI, Google, Anthropic/Claude) y API Key propia. Cada agente puede asociarse
a un módulo o flujo específico del sistema (expedientes, inventario, finanzas, etc.).

Va de último en el orden de desarrollo porque los agentes consumirán datos de todos los
módulos anteriores para operar con contexto real de la plataforma.

**Modelos clave:**
```python
class AIProvider(models.TextChoices):
    OPENAI    = 'openai',    'OpenAI'
    GOOGLE    = 'google',    'Google (Gemini)'
    ANTHROPIC = 'anthropic', 'Anthropic (Claude)'

class AIModel(models.TextChoices):
    # OpenAI
    GPT_4O          = 'gpt-4o',          'GPT-4o'
    GPT_4O_MINI     = 'gpt-4o-mini',     'GPT-4o Mini'
    GPT_4_TURBO     = 'gpt-4-turbo',     'GPT-4 Turbo'
    O1_PREVIEW      = 'o1-preview',      'o1 Preview'
    O1_MINI         = 'o1-mini',         'o1 Mini'
    # Google
    GEMINI_15_PRO   = 'gemini-1.5-pro',  'Gemini 1.5 Pro'
    GEMINI_15_FLASH = 'gemini-1.5-flash','Gemini 1.5 Flash'
    GEMINI_2_FLASH  = 'gemini-2.0-flash','Gemini 2.0 Flash'
    # Anthropic
    CLAUDE_35_SONNET = 'claude-3-5-sonnet-20241022', 'Claude 3.5 Sonnet'
    CLAUDE_35_HAIKU  = 'claude-3-5-haiku-20241022',  'Claude 3.5 Haiku'
    CLAUDE_3_OPUS    = 'claude-3-opus-20240229',      'Claude 3 Opus'


class AIAgent(models.Model):
    """Configuración de un agente IA dentro de MWT ONE"""
    id           = UUIDField(primary_key=True, default=uuid4)
    name         = CharField(max_length=100)           # Nombre del agente ej: "Asistente Expedientes"
    slug         = SlugField(max_length=100, unique=True)
    description  = TextField(blank=True)               # Para qué sirve este agente
    provider     = CharField(max_length=20, choices=AIProvider.choices)
    model        = CharField(max_length=60, choices=AIModel.choices)
    system_prompt = TextField()                        # Prompt base / instrucciones del agente
    temperature  = FloatField(default=0.7)             # 0.0 – 2.0
    max_tokens   = PositiveIntegerField(default=2048)
    api_key      = CharField(max_length=200)           # Encriptada — ver nota de seguridad
    module_scope = CharField(max_length=50, blank=True,
                             choices=[
                                 ('global',      'Global — todos los módulos'),
                                 ('expedientes', 'Expedientes'),
                                 ('inventory',   'Inventario'),
                                 ('finance',     'Financiero'),
                                 ('transfers',   'Transfers'),
                                 ('clientes',    'Clientes'),
                             ])
    is_active    = BooleanField(default=True)
    created_at   = DateTimeField(auto_now_add=True)
    updated_at   = DateTimeField(auto_now=True)
    deleted_at   = DateTimeField(null=True, blank=True)


class AIAgentLog(models.Model):
    """Log de ejecuciones del agente — para auditoría y debugging"""
    id           = UUIDField(primary_key=True, default=uuid4)
    agent        = ForeignKey(AIAgent, on_delete=PROTECT, related_name='logs')
    user         = ForeignKey('users.MWTUser', on_delete=SET_NULL, null=True)
    input_text   = TextField()                         # Prompt enviado por el usuario
    output_text  = TextField()                         # Respuesta del modelo
    tokens_used  = PositiveIntegerField(default=0)
    latency_ms   = PositiveIntegerField(default=0)
    status       = CharField(max_length=20, choices=[
                       ('success', 'Éxito'),
                       ('error',   'Error'),
                       ('timeout', 'Timeout'),
                   ])
    error_detail = TextField(blank=True)
    created_at   = DateTimeField(auto_now_add=True)
```

> ⚠️ **Nota de seguridad — API Keys:**  
> El campo `api_key` en `AIAgent` **NUNCA debe almacenarse en texto plano**.  
> Usar `django-fernet-fields` o cifrado simétrico con `SECRET_KEY` como KEK.  
> La API Key nunca debe retornarse en ningún endpoint GET — solo confirmación de que está configurada (`has_api_key: true`).  
> Claude debe leer `backend/apps/integrations/` antes de implementar para ver si ya existe un patrón de cifrado de credenciales en el proyecto.

**Endpoints Backend:**

| Método | Endpoint | Descripción | Auth |
|--------|----------|-------------|------|
| GET | `/api/ai-agents/` | Listar agentes configurados | superadmin |
| POST | `/api/ai-agents/` | Crear agente nuevo | superadmin |
| GET | `/api/ai-agents/{id}/` | Detalle del agente (sin exponer api_key) | superadmin |
| PATCH | `/api/ai-agents/{id}/` | Editar configuración del agente | superadmin |
| DELETE | `/api/ai-agents/{id}/` | Desactivar agente (soft delete) | superadmin |
| POST | `/api/ai-agents/{id}/test/` | Probar agente con mensaje de prueba | superadmin |
| GET | `/api/ai-agents/{id}/logs/` | Historial de ejecuciones del agente | superadmin |
| GET | `/api/ai-agents/models/` | Listar modelos disponibles por proveedor | superadmin |

**Rutas Frontend:**
```
[lang]/(mwt)/(dashboard)/configuracion/agentes-ia/page          → Lista de agentes IA
[lang]/(mwt)/(dashboard)/configuracion/agentes-ia/nuevo/page    → Crear agente (página completa)
[lang]/(mwt)/(dashboard)/configuracion/agentes-ia/[id]/page     → Detalle + editar + logs
```

**UI — Componentes requeridos:**

- **Lista agentes:** Tabla — nombre, proveedor (logo/badge), modelo, módulo asignado, estado activo, última ejecución
- **Crear / editar agente:** Página completa (formulario largo) con secciones:
  - **Identidad:** nombre, slug, descripción, módulo asignado
  - **Proveedor & Modelo:** selector de proveedor (OpenAI / Google / Claude) con logos, luego selector de modelo filtrado por proveedor seleccionado
  - **Configuración:** temperature (slider 0–2), max_tokens (input numérico)
  - **API Key:** input tipo password — solo escritura, nunca se muestra el valor existente. Badge `✓ Configurada` si ya existe
  - **System Prompt:** textarea grande con contador de tokens estimados
- **Panel de prueba (Test Agent):** dentro del detalle — input de mensaje libre → botón "Probar" → muestra respuesta del modelo en tiempo real con streaming si el proveedor lo soporta. Muestra tokens usados y latencia.
- **Logs de ejecución:** Tabla paginada — fecha, usuario, tokens, latencia, status. Drawer para ver input/output completo de cada log.

**Criterio de done:**
- [ ] CRUD completo de agentes desde consola
- [ ] Selector de proveedor actualiza dinámicamente los modelos disponibles
- [ ] API Key almacenada cifrada — nunca expuesta en GET
- [ ] Panel de prueba funcional (POST a `/api/ai-agents/{id}/test/`)
- [ ] Log de cada ejecución registrado automáticamente
- [ ] Agente inactivo no puede ejecutarse ni aparecer en integraciones
- [ ] Solo usuarios con rol `superadmin` pueden crear/editar agentes
- [ ] Temperature y max_tokens con validación de rango en frontend y backend

**Dependencias:** Módulo 10 (Usuarios), Módulo 11 (Roles & Permisos), Módulo 12 (Financiero)  
**Desbloquea:** Automatización inteligente en cualquier módulo del sistema — IA sobre expedientes, inventario, finanzas

---

## Mapa de Dependencias

```
Módulo 1  (Brands)
  ├── Módulo 2  (Productos)
  │     └── Módulo 2b (Tallas)
  │           ├── Módulo 4  (Inventario)
  │           │     └── Módulo 6  (Inventarios Consolidado)
  │           └── Módulo 7  (Transfers)
  ├── Módulo 3  (Nodos)
  │     ├── Módulo 4  (Inventario)
  │     └── Módulo 7  (Transfers)
  ├── Módulo 5  (Proveedores)
  │     └── Módulo 9  (Expedientes — integración)
  │           └── Módulo 12 (Financiero)
  │                 └── Módulo 13 (Agentes IA)
  ├── Módulo 8  (Clientes)
  │     └── Módulo 9  (Expedientes — integración)
  │           └── Módulo 12 (Financiero)
  │                 └── Módulo 13 (Agentes IA)
  └── Módulo 10 (Usuarios)
        └── Módulo 11 (Roles & Permisos)
              ├── Módulo 12 (Financiero — rol financiero activo)
              └── Módulo 13 (Agentes IA — solo superadmin)
```

---

## Tabla Resumen de Módulos

| # | Módulo | App Django | Estado Backend | Estado Frontend | Dependencias |
|---|--------|-----------|----------------|-----------------|--------------|
| 1 | Brands | `brands` | ✅ Existe | ❌ Sin UI | Ninguna |
| 2 | Productos | `products` | ❌ Nueva | ❌ Sin UI | M1 |
| 2b | Tallas | `products` (ProductSize) | ❌ Nueva | ❌ Sin UI | M2 |
| 3 | Nodos | `nodes` | ❌ Nueva | ❌ Sin UI | M1 |
| 4 | Inventario | `inventory` | ❌ Nueva | ❌ Sin UI | M2b, M3 |
| 5 | Proveedores | `suppliers` | ❌ Nueva | ❌ Sin UI | M1 |
| 6 | Inventarios (consolidado) | `inventory` (extensión) | ❌ Pendiente | ❌ Sin UI | M4 |
| 7 | Transfers | `transfers` | ✅ Existe | ❌ Sin UI | M2b, M3, M4 |
| 8 | Clientes | `clients` | ⚠️ Parcial | ❌ Sin UI | M7 |
| 9 | Expedientes | `expedientes` | ✅ Completo | ✅ Sprint 7 | M3, M5, M8 |
| 10 | Usuarios Portal & Consola | `users` | ❌ Nueva | ❌ Sin UI | M1, M11 |
| 11 | Roles & Permisos | `permission_groups` | ❌ Nueva | ❌ Sin UI | M10 |
| 12 | Financiero | `finance` | ❌ Nueva | ❌ Sin UI | M5, M8, M9, M10, M11 |
| 13 | Agentes IA | `ai_agents` | ❌ Nueva | ❌ Sin UI | M10, M11, M12 |

---

## Instrucciones para Claude al Iniciar un Sprint de Alejandro

```
CUANDO leas este archivo al inicio de un sprint, debes:

1. Identificar qué módulo(s) de esta lista aplican al sprint actual
2. LEER el modelo Django existente (si ya existe) antes de crear endpoints — no inventar campos
3. Respetar las convenciones de UI: drawer lateral para CRUD, página nueva solo para
   formularios complejos (igual que expedientes/nuevo)
4. Los endpoints deben seguir el patrón /api/{recurso}/ con trailing slash
5. Verificar dependencias: si un módulo requiere otro, confirmar que ese otro existe primero
6. El sistema de permisos en MVP = CEO superuser. NO implementar guards de RBAC
   en el frontend durante sprints anteriores al Módulo 11 salvo que el CEO lo solicite
7. Todos los nuevos modelos Django deben tener: UUID pk, is_active, created_at,
   updated_at, deleted_at (soft delete)
8. Respetar ENT_PLAT_DESIGN_TOKENS para estilos
9. Consultar MODULOS_FALTANTES_FRONTEND_BACKEND.md para especificaciones detalladas
   de cada módulo (modelos, endpoints, UI completa)
10. Para el Módulo 12 (Financiero): leer `backend/apps/liquidations/` antes de crear
    la app `finance` para evitar duplicación de modelos
11. Para el Módulo 13 (Agentes IA): leer `backend/apps/integrations/` antes de crear
    la app `ai_agents` para reutilizar patrón de cifrado de credenciales existente.
    La API Key NUNCA debe retornarse en ningún endpoint GET.
```

---

*Stamp: v1.2 — actualizado 2026-04-09 — agregado Módulo 13 Agentes IA*  
*Origen: Revisión base de conocimiento MWT ONE — carpetas Sprints/ y docs/ — instrucciones CEO Alejandro*
