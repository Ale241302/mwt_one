# PLAN ESTRATEGICO: SISTEMA DISTRIBUIDO POR MODULOS INDEPENDIENTES
## MWT ONE — Backend Refactor: De Monolito FK a Modulos Desacoplados

**Fecha:** 2026-04-17
**Version:** 1.0
**Autor:** Analisis consolidado por 4 Agentes Especializados + Director de Proyecto
**Estado:** Borrador — Requiere aprobacion del CEO

---

## Tabla de Contenidos

1. [Vision Arquitectonica](#1-vision-arquitectonica)
2. [Mapeo de Modulos y IDs](#2-mapeo-de-modulos-y-sus-ids-de-referencia)
3. [Flujo Real del Negocio: OC -> SAP -> Expediente](#3-flujo-real-del-negocio-oc--sap--expediente)
4. [Fases de Migracion](#4-fases-de-migracion-plan-de-6-meses)
5. [Patron de Comunicacion entre Modulos](#5-patron-de-comunicacion-entre-modulos)
6. [Gestion de Integridad Referencial sin FKs](#6-gestion-de-la-integridad-referencial-sin-fks)
7. [Estrategia de Migracion de Datos](#7-estrategia-de-migracion-de-datos)
8. [Infraestructura](#8-infraestructura-para-la-nueva-arquitectura)
9. [Riesgos y Mitigaciones](#9-riesgos-y-mitigaciones)
10. [Cronograma Consolidado](#10-cronograma-consolidado)
11. [Decisiones Arquitectonicas Clave](#11-decisiones-arquitectonicas-clave)
12. [Primer Paso Inmediato](#12-primer-paso-inmediato)

---

## 1. Vision Arquitectonica

> **Regla Fundamental:** Ninguna tabla tiene ForeignKeys a otra app. Solo campos `UUID` que almacenan IDs de entidades externas. La integridad referencial y las relaciones se manejan por **logica de aplicacion**, no por constraints de BD.

### Diagrama de Arquitectura

```
+-------------------------------------------------------------------------+
|                    CAPA DE ORQUESTACION (API Gateway)                   |
|         Django REST Framework · Autenticacion · Rate Limiting           |
+-------------------------------------------------------------------------+
|  +---------+  +---------+  +---------+  +---------+  +---------+      |
|  |Brands   |  |Productos|  |Clientes |  |Nodos    |  |Proveed. |      |
|  |(catalogo)|  |(SKUs)   |  |(credito)|  |(bodegas)|  |(fabricas)|     |
|  +----+----+  +----+----+  +----+----+  +----+----+  +----+----+      |
|       |            |            |            |            |            |
|       +------------+------------+------------+------------+            |
|                              |                                         |
|                    +-------------------+                                |
|                    |  Inventario       |  <- solo IDs: product_id,    |
|                    |  (stock x nodo)   |    node_id, supplier_id      |
|                    +-------------------+                                |
|                              |                                         |
|  +---------+  +---------+  +---------+  +---------+  +---------+      |
|  |Transfers|  |Expedient|  |Financier|  |Cobros   |  |Template |      |
|  |(movtos) |  |(estados)|  |(facturas)|  |(cobranza)|  |(notifs) |     |
|  +----+----+  +----+----+  +----+----+  +----+----+  +----+----+      |
|       |            |            |            |            |            |
|       +------------+------------+------------+------------+            |
|                              |                                         |
|  +------------------------------------------------------------------+  |
|  |  Historial (Event Sourcing)  |  Dashboard (Read Model / Cache)   |  |
|  |  --------------------------  |  -----------------------------    |  |
|  |  Todos los modulos publican  |  Agrega datos de todos los        |  |
|  |  eventos aqui. Sin FKs.      |  modulos para KPIs y reportes.    |  |
|  +------------------------------------------------------------------+  |
+-------------------------------------------------------------------------+
|                    CAPA DE INFRAESTRUCTURA                              |
|      PostgreSQL (modulos aislados) · Redis (event bus) · MinIO          |
+-------------------------------------------------------------------------+
```

---

## 2. Mapeo de Modulos y sus IDs de Referencia

Cada modulo es dueno de sus propias tablas. Cuando necesita referenciar a otro modulo, guarda solo el `UUID` como campo `CharField(36)` o `UUIDField` sin `ForeignKey`.

### 2.1 Modulos Catalizadores (Sin dependencias externas)

| Modulo | Modelos Principales | IDs que recibe de otros | IDs que exporta |
|--------|---------------------|------------------------|-----------------|
| **Brands** | Brand, BrandConfig, BrandSKU, BrandTechnicalSheet | — | brand_id |
| **Productos** | ProductMaster, ProductVariant, ProductLine, ProductSize | brand_id | product_id, sku_id, variant_id |
| **Proveedores** | Supplier, SupplierContact, SupplierKPI | brand_id (opcional) | supplier_id |
| **Nodos** | Node, NodeType, NodeCapacity | brand_id (opcional) | node_id |

### 2.2 Modulos Operativos (Dependen de catalizadores)

| Modulo | Modelos Principales | IDs que recibe | IDs que exporta |
|--------|---------------------|----------------|-----------------|
| **Clientes** | Client, ClientGroup, ClientSubsidiary, CreditLine | brand_id (asociacion) | client_id, subsidiary_id |
| **Inventario** | InventoryRecord, InventoryMovement, StockAlert | product_id, variant_id, node_id, sku_id | inventory_record_id |
| **Transfers** | Transfer, TransferLine, TransferDocument | node_id (origen/destino), product_id, variant_id, supplier_id | transfer_id |

### 2.3 Modulos Core (Nucleo de negocio)

| Modulo | Modelos Principales | IDs que recibe | IDs que exporta |
|--------|---------------------|----------------|-----------------|
| **Expedientes** | Expediente, Artifact, CostLine, PaymentLine, EventLog | brand_id, client_id, subsidiary_id, node_id, product_id, variant_id, supplier_id | expediente_id, artifact_id |
| **Financiero** | Invoice, Payment, SupplierPayment, Liquidation | expediente_id, client_id, supplier_id, subsidiary_id | invoice_id, payment_id |
| **Cobros** | CollectionRun, CollectionReminder, CollectionRule | expediente_id, client_id, invoice_id | collection_run_id |

### 2.4 Modulos Transversales

| Modulo | Modelos Principales | IDs que recibe | IDs que exporta |
|--------|---------------------|----------------|-----------------|
| **Template** | NotificationTemplate, DocumentTemplate, EmailTemplate | brand_id (para scoping) | template_id |
| **Historial** | Event, AuditLog, TimelineEntry | TODOS (cualquier modulo publica aqui) | event_id |
| **Dashboard** | KPI, Report, Widget | TODOS (lectura solo) | — |
| **Portal** | PortalSession, PortalView, PortalOrder | client_id, subsidiary_id, expediente_id | — |

---

## 3. Flujo Real del Negocio: OC -> SAP -> Expediente

> **Hallazgo critico del dominio:** El sistema MWT NO maneja "expedientes" de la forma tradicional. El flujo real es:
>
> **Orden de Compra (OC) -> Numeros SAP (Expedientes hijos) -> Detalle por SAP**

### 3.1 Dashboard de Expedientes

El dashboard muestra:
- **Para Cliente:** Solo sus propias OCs y sus SAPs asociados
- **Para Admin (CEO):** Todas las OCs de todos los clientes

### 3.2 Creacion de OC (Orden de Compra)

Cuando se crea un "expediente", realmente se crea una **OC** con los siguientes datos:

| Campo | Tipo | Descripcion |
|-------|------|-------------|
| client_id | UUID | Cliente que realiza la orden |
| brand_id | UUID | Marca del producto |
| mode | String | Modalidad operativa |
| destination | String | Destino (CR, USA) |
| dispatch_mode | String | Modo de despacho |
| price_basis | String | Base de precio |
| operado_por | String | Quien opera (CLIENTE / MWT) |
| notes | Text | Nota opcional |

#### Lineas de Producto (1 o mas)

| Campo | Tipo | Descripcion |
|-------|------|-------------|
| product_master_id | UUID | Linea de producto |
| quantity | Integer | Cantidad |
| unit_price | Decimal | Valor del producto (puede ser diferente al catalogo) |
| total_line | Decimal | Cantidad x Precio |

> **Regla de negocio:** El usuario puede guardar un valor diferente al del catalogo al momento de crear la OC.

### 3.3 Detalle de OC

Al entrar al detalle de una OC se ven:

| Seccion | Contenido |
|---------|-----------|
| **Info General** | Cliente, marca, modo, destino, estado, total |
| **Lineas de Producto** | Lista de productos con cantidad y valor |
| **Proformas Asociadas** | Proformas emitidas para esta OC |
| **Numeros SAP** | Expedientes/SAPs generados a partir de esta OC |
| **Pagos** | Estado de pagos |

### 3.4 SAP (Expediente Hijo)

Una OC puede tener **uno o mas SAPs**. Cada SAP:
- Tiene un **numero SAP unico**
- Puede contener **una o mas lineas de producto** de la OC (una linea puede ir a un SAP, otra a otro)
- Tiene un **tipo de envio propio** (aereo, maritimo, terrestre)
- Tiene su propio **flujo de estados** (REGISTRO -> PRODUCCION -> PREPARACION -> DESPACHO -> TRANSITO -> DESTINO)

> **Regla de negocio:** Cada linea de producto de la OC puede ir a un SAP diferente. Cada SAP tiene diferente tipo de envio.

```
OC #OC-001
|-- Linea 1: GOL-001 x 100 uds
|   \-- SAP-2026-001 (Envio: Aereo) -> Registro -> Produccion -> ...
|-- Linea 2: VEL-003 x 50 uds
|   \-- SAP-2026-002 (Envio: Maritimo) -> Registro -> Produccion -> ...
\-- (podria haber mas SAPs)
```

### 3.5 Detalle del SAP (Hoy: Detalle del Expediente)

Cuando entras al detalle de un SAP, se muestra lo que hoy es el detalle del expediente:

| Seccion | Contenido |
|---------|-----------|
| **Info General** | Numero SAP, OC origen, estado, tipo de envio |
| **Lineas de Producto** | Que productos de la OC van en este SAP |
| **Artefactos** | Documentos requeridos (DANFE, proforma, packing list, etc.) |
| **Costos** | Costos asociados al envio |
| **Timeline / Estados** | Progreso por fase |
| **Pagos** | Estado de pago de este SAP |
| **Notificaciones** | Alertas y recordatorios |

### 3.6 Implicaciones para la Arquitectura Distribuida

Este flujo de negocio implica que:

1. **OC** y **SAP** son entidades separadas, no una sola.
2. **OC** pertenece mas al modulo de **Clientes/Orders** que a Expedientes.
3. **SAP** (expediente) es el core de **Expedientes**.
4. **Una OC -> Muchos SAPs** (relacion 1:N).
5. **Una linea de OC -> Un SAP** (distribucion de productos).

#### Modelo de Datos Propuesto (sin FKs)

```python
# apps/orders/models.py  (NUEVO MODULO)
class OrdenCompra(BaseModel):
    """Orden de Compra del cliente. Es el punto de entrada."""
    oc_number = models.CharField(max_length=50, unique=True)
    client_id = models.UUIDField(db_index=True)          # ref a Clientes
    brand_id = models.UUIDField(db_index=True)           # ref a Brands
    mode = models.CharField(max_length=50)
    destination = models.CharField(max_length=10)
    dispatch_mode = models.CharField(max_length=20)
    price_basis = models.CharField(max_length=50)
    operado_por = models.CharField(max_length=20)
    notes = models.TextField(blank=True)
    status = models.CharField(max_length=20, default='BORRADOR')
    total_amount = models.DecimalField(max_digits=14, decimal_places=2)
    currency = models.CharField(max_length=3, default='USD')

class OrdenCompraLinea(BaseModel):
    """Linea de producto dentro de una OC."""
    oc_id = models.UUIDField(db_index=True)              # ref a OrdenCompra
    product_master_id = models.UUIDField(db_index=True)  # ref a Productos
    variant_id = models.UUIDField(null=True, blank=True) # ref a Variante
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    total_line = models.DecimalField(max_digits=14, decimal_places=2)

# apps/expedientes/models.py  (REFACTORIZADO)
class ExpedienteSAP(BaseModel):
    """Expediente / Numero SAP. Hijo de una OC."""
    sap_number = models.CharField(max_length=50, unique=True)
    oc_id = models.UUIDField(db_index=True)              # ref a Orders
    client_id = models.UUIDField(db_index=True)          # ref a Clientes
    brand_id = models.UUIDField(db_index=True)           # ref a Brands
    status = models.CharField(max_length=20, default='REGISTRO')
    shipping_method = models.CharField(max_length=50)
    origin_node_id = models.UUIDField(null=True, blank=True)     # ref a Nodos
    destination_node_id = models.UUIDField(null=True, blank=True)

class SAPLinea(BaseModel):
    """Linea de producto asignada a un SAP especifico."""
    sap_id = models.UUIDField(db_index=True)             # ref a ExpedienteSAP
    oc_linea_id = models.UUIDField(db_index=True)        # ref a OrdenCompraLinea
    product_master_id = models.UUIDField(db_index=True)  # ref a Productos
    variant_id = models.UUIDField(null=True, blank=True)
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
```

---

## 4. Fases de Migracion (Plan de 6 Meses)

> **Estrategia: Migracion Gradual, no Big-Bang.**
> Cada fase desacopla un grupo de modulos y valida antes de continuar. La app sigue funcionando en produccion durante todo el proceso.

---

### FASE 0: CIMIENTOS (Semanas 1-2)

**Objetivo:** Preparar la infraestructura y las convenciones antes de tocar modelos.

| Tarea | Detalle | Riesgo |
|-------|---------|--------|
| 0.1 Crear UUIDReferenceField custom | Un CharField(36) con validacion UUID + metodo helper resolve(module_name) que hace fetch al modulo destino | Bajo |
| 0.2 Crear ModuleRegistry | Diccionario central que mapea module_name -> base_url/api/ para que los servicios se comuniquen | Bajo |
| 0.3 Crear EventBus interno | Usar Django signals + Redis pub/sub para que los modulos publiquen eventos de dominio | Medio |
| 0.4 Crear Historial app base | Tabla Event con: event_id, module_source, entity_type, entity_id, payload_json, timestamp | Bajo |
| 0.5 Crear Dashboard read model | Tablas materializadas que se actualizan por eventos, no por joins | Bajo |
| 0.6 Hacer backup completo de BD | Snapshot de PostgreSQL + dump de datos | — |

**Entregable:** Infraestructura de desacoplamiento lista. Sin cambios en datos reales.

---

### FASE 1: MODULOS CATALIZADORES (Semanas 3-6)

**Objetivo:** Desacoplar los modulos base que no dependen de nadie.

#### 1.1 Brands -> Independiente

```python
# ANTES (con FK)
brand = models.ForeignKey('brands.Brand', on_delete=models.PROTECT)

# DESPUES (solo ID)
brand_id = models.UUIDField(null=True, blank=True, db_index=True)
```

**Pasos:**
- Crear `BrandService` en `apps/brands/services/` que expone `get_brand(brand_id)`
- Reemplazar todas las FKs a `brands.Brand` en otras apps por `brand_id UUIDField`
- Crear data migration que copia los IDs actuales a los nuevos campos
- Eliminar FKs (soft: dejarlas nullable primero, luego borrar)

#### 1.2 Nodos -> Extraer de Transfers

Hoy `Node` vive dentro de `transfers`. Hay que extraerlo a `apps/nodos/` propio.

**Pasos:**
- Crear app `apps/nodos/` con modelo `Node` (solo nodos, sin FK a transfers)
- Migrar datos de `transfers.Node` a `nodos.Node`
- Reemplazar `transfers.Node` FKs en `expedientes` e `inventario` por `node_id UUIDField`

#### 1.3 Proveedores -> Independiente

**Pasos:**
- Eliminar FK `supplier` en `expedientes` y `commercial`
- Reemplazar por `supplier_id UUIDField`
- Crear `SupplierService.get(supplier_id)`

**Entregable:** Brands, Nodos, Proveedores operan sin FKs. Tests pasando.

---

### FASE 2: CATALOGO E INVENTARIO (Semanas 7-10)

**Objetivo:** Desacoplar Productos, Tallas/Sizing, e Inventario. Esto es critico para Rana Walk.

#### 2.1 Productos -> Reconciliar y Desacoplar

Hoy hay 3 modelos: `Producto`, `ProductMaster`, `ProductVariant` + `BrandSKU` en brands. Necesitamos unificar.

**Estrategia:**
```
ProductMaster (SKU base) -> ProductVariant (talla/color) -> SKU unico
```
- `ProductMaster` tiene `brand_id UUIDField`
- `ProductVariant` tiene `product_master_id UUIDField` (intra-app, OK)
- `BrandSKU` se migra a `ProductVariant.sku_code`

**Pasos:**
- Crear modelo `ProductSize` (variante por talla)
- Generar SKUs unicos: `{product_master.sku_base}-{size}`
- Reemplazar FK `product` en `expedientes.ProductLine` por `product_master_id UUIDField`
- Reemplazar FK `brand_sku` en `expedientes` por `variant_id UUIDField`

#### 2.2 Inventario -> Desacoplar de Productos y Nodos

Hoy `InventoryEntry` tiene FK a `productos.Producto` y `transfers.Node`.

**Pasos:**
- Reemplazar FK `product` por `product_master_id UUIDField`
- Reemplazar FK `node` por `node_id UUIDField`
- Crear `InventoryMovement` (log inmutable): `product_master_id`, `variant_id`, `node_id`, `quantity_delta`, `reason`, `transfer_id` (opcional), `expediente_id` (opcional)
- Ninguna FK. Solo IDs.

#### 2.3 Conectar Inventario <-> Transfers por Eventos

Cuando un `Transfer` cambia a estado `recibido`:
1. `Transfers` publica evento `TransferCompleted(transfer_id)`
2. `Inventario` escucha y crea `InventoryMovement` entries
3. `Dashboard` escucha y actualiza KPIs

**Entregable:** Stock por SKU-talla por nodo, trazable, sin FKs entre apps.

---

### FASE 3: ORDERS (OC) + CLIENTES + EXPEDIENTES (Semanas 11-16)

**Objetivo:** Separar OC de Expedientes, desacoplar Clientes, y refactorizar Expedientes.

#### 3.1 Crear Modulo Orders (OC)

Este es un modulo **NUEVO** que no existia en la arquitectura anterior.

```python
# apps/orders/models.py
class OrdenCompra(BaseModel):
    oc_number = models.CharField(max_length=50, unique=True)
    client_id = models.UUIDField(db_index=True)
    brand_id = models.UUIDField(db_index=True)
    mode = models.CharField(max_length=50)
    destination = models.CharField(max_length=10)
    dispatch_mode = models.CharField(max_length=20)
    price_basis = models.CharField(max_length=50)
    operado_por = models.CharField(max_length=20)
    notes = models.TextField(blank=True)
    status = models.CharField(max_length=20, default='BORRADOR')
    total_amount = models.DecimalField(max_digits=14, decimal_places=2)
    currency = models.CharField(max_length=3, default='USD')
    created_by_id = models.UUIDField(null=True, blank=True)

class OrdenCompraLinea(BaseModel):
    oc_id = models.UUIDField(db_index=True)
    product_master_id = models.UUIDField(db_index=True)
    variant_id = models.UUIDField(null=True, blank=True)
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    total_line = models.DecimalField(max_digits=14, decimal_places=2)
```

**Migracion de datos:**
- Las OCs existentes se extraen de los `Expediente` que tienen `purchase_order_number`
- Las lineas de producto se migran desde `expedientes.ProductLine`

#### 3.2 Clientes -> Simplificar Jerarquia

Hoy `Clientes` tiene jerarquia de 4 niveles con FKs a `core.LegalEntity`. Simplificar:

```
Cliente (plano) -> Subsidiary (opcional)
```

**Pasos:**
- Reemplazar FK `legal_entity` en `ClientSubsidiary` por `legal_entity_id UUIDField`
- Reemplazar FK `client` en `expedientes`/`orders` por `client_id UUIDField`
- Reemplazar FK `subsidiary` en `expedientes`/`orders` por `subsidiary_id UUIDField`

#### 3.3 Expedientes -> Refactorizar como "SAP"

El modelo `Expediente` hoy tiene 70+ campos y multiples FKs. Refactorizar para reflejar el flujo real:

```python
# apps/expedientes/models.py (REFACTORIZADO)
class ExpedienteSAP(BaseModel):
    """Expediente = Numero SAP. Hijo de una OC."""
    sap_number = models.CharField(max_length=50, unique=True)
    oc_id = models.UUIDField(db_index=True)              # ref a Orders
    client_id = models.UUIDField(db_index=True)          # ref a Clientes
    brand_id = models.UUIDField(db_index=True)           # ref a Brands
    status = models.CharField(max_length=20, default='REGISTRO')
    
    # Estado de credito
    credit_blocked = models.BooleanField(default=False)
    credit_warning = models.BooleanField(default=False)
    credit_exposure = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    credit_days_elapsed = models.PositiveIntegerField(default=0)
    
    # Logistica
    shipping_method = models.CharField(max_length=50, blank=True)
    origin_node_id = models.UUIDField(null=True, blank=True)
    destination_node_id = models.UUIDField(null=True, blank=True)
    
    # Proformas
    proforma_client_number = models.CharField(max_length=100, blank=True)
    proforma_mwt_number = models.CharField(max_length=100, blank=True)
    
    # Totales
    total_cost = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    total_value = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    currency = models.CharField(max_length=3, default='USD')
    
    # Tracking
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class SAPLinea(BaseModel):
    """Linea de producto asignada a este SAP."""
    sap_id = models.UUIDField(db_index=True)
    oc_linea_id = models.UUIDField(db_index=True)
    product_master_id = models.UUIDField(db_index=True)
    variant_id = models.UUIDField(null=True, blank=True)
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)

class SAPCosto(BaseModel):
    """Costo asociado a un SAP."""
    sap_id = models.UUIDField(db_index=True)
    cost_category = models.CharField(max_length=50)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, default='USD')
    notes = models.TextField(blank=True)

class SAPPago(BaseModel):
    """Pago asociado a un SAP."""
    sap_id = models.UUIDField(db_index=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, default='USD')
    payment_method = models.CharField(max_length=50)
    reference = models.CharField(max_length=100, blank=True)
    payment_date = models.DateField()
    status = models.CharField(max_length=20, default='PENDIENTE')
```

**Migracion de datos:**
- Cada `Expediente` existente se convierte en un `ExpedienteSAP`
- `oc_id` se extrae del campo `purchase_order_number` (busqueda en Orders)
- Los estados se preservan
- `EventLog` se migra a `Historial`

#### 3.4 Maquina de Estados del SAP

```
REGISTRO --C1--> PRODUCCION --C3--> PREPARACION --C5--> DESPACHO
                                              --C4--> CANCELADO
                                                          |
                                                          v
                                                    TRANSITO --C7--> DESTINO
                                                                     |
                                                              --C6--> CANCELADO
```

**Eventos publicados por cada transicion:**
- `sap.status_changed` -> Dashboard, Notificaciones, Inventario
- `sap.credit_warning` -> Cobros, Financiero
- `sap.document_required` -> Template

**Entregable:** OC separada de SAP. Flujo de negocio real reflejado en la arquitectura. Sin FKs entre apps.

---

### FASE 4: TRANSFERS Y COMERCIAL (Semanas 17-20)

#### 4.1 Transfers -> Desacoplar de Inventario y Nodos

Hoy `TransferLine` tiene FK a `transfers.Node` (que ya se movio a `nodos`).

**Pasos:**
- Reemplazar FK `origin_node` y `destination_node` por `origin_node_id UUIDField` y `destination_node_id UUIDField`
- Reemplazar FK `product` en `TransferLine` por `product_master_id UUIDField` + `variant_id UUIDField`
- Publicar eventos `TransferCreated`, `TransferShipped`, `TransferReceived`
- `Inventario` escucha `TransferReceived` y actualiza stock

#### 4.2 Commercial -> Desacoplar de Clientes y Brands

Hoy `commercial` tiene FKs a `brands.Brand`, `clientes.Cliente`, `clientes.ClientSubsidiary`, `expedientes.FactoryOrder`.

**Pasos:**
- Reemplazar todas las FKs por campos `*_id UUIDField`
- `RebateProgram`, `CommissionRule`, `ArtifactPolicy` solo guardan `brand_id`, `client_id`, `subsidiary_id`
- Resolver entidades via `BrandService`, `ClientService` cuando se necesiten en endpoints

---

### FASE 5: FINANCIERO, COBROS, NOTIFICACIONES (Semanas 21-24)

#### 5.1 Financiero -> Nueva App

Recomendacion: Crear `apps/finance/` nueva, dejar `liquidations` como legacy.

```python
# apps/finance/models.py
class Invoice(BaseModel):
    invoice_id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    sap_id = models.UUIDField(db_index=True)             # ref a Expedientes/SAP
    oc_id = models.UUIDField(db_index=True)              # ref a Orders
    client_id = models.UUIDField(db_index=True)          # ref a Clientes
    subsidiary_id = models.UUIDField(null=True, blank=True)
    invoice_number = models.CharField(max_length=50, unique=True)
    currency = models.CharField(max_length=3, default='USD')
    subtotal = models.DecimalField(max_digits=14, decimal_places=2)
    tax = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=14, decimal_places=2)
    status = models.CharField(choices=[
        ('borrador', 'Borrador'),
        ('emitida', 'Emitida'),
        ('pagada', 'Pagada'),
        ('vencida', 'Vencida'),
        ('anulada', 'Anulada'),
    ])
    issued_at = models.DateField(null=True)
    due_at = models.DateField(null=True)
    paid_at = models.DateTimeField(null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class Payment(BaseModel):
    payment_id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    client_id = models.UUIDField(db_index=True)
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    currency = models.CharField(max_length=3, default='USD')
    payment_method = models.CharField(choices=[
        ('transferencia', 'Transferencia Bancaria'),
        ('cheque', 'Cheque'),
        ('efectivo', 'Efectivo'),
        ('otro', 'Otro'),
    ])
    reference = models.CharField(max_length=100, blank=True)
    payment_date = models.DateField()
    invoice_ids = models.JSONField(default=list)  # lista de UUIDs, no M2M
    notes = models.TextField(blank=True)
    created_by_id = models.UUIDField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

class SupplierPayment(BaseModel):
    supplier_payment_id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    supplier_id = models.UUIDField(db_index=True)
    sap_id = models.UUIDField(null=True, blank=True)
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    currency = models.CharField(max_length=3, default='USD')
    payment_method = models.CharField(max_length=30)
    reference = models.CharField(max_length=100, blank=True)
    payment_date = models.DateField()
    notes = models.TextField(blank=True)
    created_by_id = models.UUIDField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
```

#### 5.2 Cobros -> Nueva App

```python
# apps/cobros/models.py
class CollectionRule(BaseModel):
    rule_id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    brand_id = models.UUIDField(null=True, blank=True)
    days_before_due = models.IntegerField()
    days_after_due = models.IntegerField()
    template_id = models.UUIDField()
    is_active = models.BooleanField(default=True)

class CollectionRun(BaseModel):
    run_id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    rule_id = models.UUIDField()
    status = models.CharField(choices=[...])
    total_invoices = models.IntegerField()
    total_amount = models.DecimalField(...)
    executed_at = models.DateTimeField(auto_now_add=True)

class CollectionReminder(BaseModel):
    reminder_id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    collection_run_id = models.UUIDField(db_index=True)
    invoice_id = models.UUIDField(db_index=True)
    client_id = models.UUIDField(db_index=True)
    sap_id = models.UUIDField(null=True, blank=True)
    status = models.CharField(choices=[...])
    sent_at = models.DateTimeField(null=True)
```

#### 5.3 Template -> Desacoplar de Notificaciones

Hoy `notifications` tiene FK a `notifications.NotificationTemplate`. Separar:

```python
# apps/template/models.py
class NotificationTemplate(BaseModel):
    template_id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    brand_id = models.UUIDField(null=True, blank=True)
    name = models.CharField(max_length=100)
    subject = models.CharField(max_length=200)
    body_html = models.TextField()
    body_text = models.TextField()
    variables_schema = models.JSONField(default=dict)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
```

`notifications` usa `template_id UUIDField` sin FK.

---

### FASE 6: DASHBOARD Y PORTAL (Semanas 25-26)

#### 6.1 Dashboard -> Read Model Materializado

El Dashboard NO tiene modelos propios de negocio. Es un **read model** que se alimenta de eventos.

```python
# apps/dashboard/models.py
class DashboardKPI(BaseModel):
    kpi_id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    module = models.CharField(max_length=50)
    metric_name = models.CharField(max_length=100)
    metric_value = models.DecimalField(max_digits=20, decimal_places=4)
    metric_currency = models.CharField(max_length=3, null=True, blank=True)
    dimensions = models.JSONField(default=dict)
    calculated_at = models.DateTimeField(auto_now_add=True)

class DashboardWidget(BaseModel):
    widget_id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    user_id = models.UUIDField(null=True, blank=True)
    widget_type = models.CharField(max_length=50)
    config = models.JSONField(default=dict)
    position = models.IntegerField(default=0)
```

**Calculo:** Un worker de Celery escucha eventos y recalcula KPIs cada N minutos.

#### 6.2 Portal -> Capa de Presentacion

El Portal no tiene modelos de dominio propios. Consume APIs de otros modulos.

```python
# apps/portal/models.py
class PortalSession(BaseModel):
    session_id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    client_id = models.UUIDField(db_index=True)
    subsidiary_id = models.UUIDField(null=True, blank=True)
    token = models.CharField(max_length=255)
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

class PortalViewLog(BaseModel):
    view_id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    session_id = models.UUIDField(db_index=True)
    entity_type = models.CharField(max_length=50)
    entity_id = models.UUIDField()
    viewed_at = models.DateTimeField(auto_now_add=True)
```

---

## 5. Patron de Comunicacion entre Modulos

### 5.1 Opcion A: Servicios Internos (Recomendada para MWT ONE)

Como todos los modulos viven en el mismo proceso Django (monolito logico), la comunicacion mas eficiente es via **Service Layer**:

```python
# apps/core/services.py
class ModuleService:
    """Base para todos los servicios de modulo"""
    
    @classmethod
    def get(cls, model_class, entity_id):
        """Obtiene una entidad por UUID sin FK"""
        try:
            return model_class.objects.get(pk=entity_id)
        except model_class.DoesNotExist:
            return None

# apps/brands/services.py
class BrandService(ModuleService):
    @classmethod
    def get_brand(cls, brand_id):
        from apps.brands.models import Brand
        return cls.get(Brand, brand_id)
    
    @classmethod
    def get_brand_name(cls, brand_id):
        brand = cls.get_brand(brand_id)
        return brand.name if brand else "Desconocido"

# Uso en otro modulo:
from apps.brands.services import BrandService

class ExpedienteSerializer(serializers.Serializer):
    brand_id = serializers.UUIDField()
    brand_name = serializers.SerializerMethodField()
    
    def get_brand_name(self, obj):
        return BrandService.get_brand_name(obj.brand_id)
```

**Ventaja:** Sin overhead de HTTP, funciona dentro del mismo proceso.

### 5.2 Opcion B: Event Bus (para operaciones asincronas)

Para operaciones que no requieren respuesta inmediata:

```python
# apps/core/events.py
class EventBus:
    @staticmethod
    def publish(event_type, payload):
        """Publica evento a Redis pub/sub"""
        import redis
        r = redis.from_url(settings.REDIS_URL)
        r.publish(f"mwt:events:{event_type}", json.dumps(payload))
    
    @staticmethod
    def subscribe(event_type, handler):
        """Registra handler para un tipo de evento"""
        # Implementado en Celery tasks o signals

# Ejemplo: Cuando un SAP cambia de estado
# apps/expedientes/services.py
def avanzar_sap(sap_id, nuevo_estado):
    sap = ExpedienteSAP.objects.get(pk=sap_id)
    estado_anterior = sap.status
    sap.status = nuevo_estado
    sap.save()
    
    EventBus.publish('sap.status_changed', {
        'sap_id': str(sap_id),
        'oc_id': str(sap.oc_id),
        'client_id': str(sap.client_id),
        'estado_anterior': estado_anterior,
        'estado_nuevo': nuevo_estado,
        'timestamp': timezone.now().isoformat()
    })

# apps/dashboard/signals.py
from apps.core.events import EventBus

def on_sap_status_changed(payload):
    data = json.loads(payload)
    # Actualizar KPIs materializados
    DashboardKPI.objects.update_or_create(
        module='expedientes',
        metric_name='sap_count_by_status',
        dimensions={'status': data['estado_nuevo']},
        defaults={'metric_value': F('metric_value') + 1}
    )

EventBus.subscribe('sap.status_changed', on_sap_status_changed)
```

### 5.3 Opcion C: API Interna (para futura separacion en microservicios)

Si en el futuro se quieren separar los modulos en contenedores independientes:

```python
# apps/core/api_client.py
class InternalAPIClient:
    def __init__(self, module_name):
        self.base_url = ModuleRegistry.get_url(module_name)
        self.headers = {'Authorization': f'Internal {settings.INTERNAL_API_TOKEN}'}
    
    def get(self, endpoint, params=None):
        return requests.get(f"{self.base_url}{endpoint}", 
                          headers=self.headers, params=params)
    
    def get_entity(self, entity_type, entity_id):
        return self.get(f"/{entity_type}/{entity_id}/")

# Uso:
client = InternalAPIClient('brands')
brand_data = client.get_entity('brands', brand_id).json()
```

---

## 6. Gestion de la Integridad Referencial sin FKs

### 6.1 El Problema

Sin ForeignKeys, PostgreSQL no impide que se borre un `Brand` que esta referenciado por `ExpedienteSAP.brand_id`. Hay que manejarlo en aplicacion.

### 6.2 Solucion: Soft Delete + Referential Integrity Service

```python
# apps/core/integrity.py
class ReferentialIntegrityService:
    """Verifica integridad referencial por logica de aplicacion"""
    
    CHECKS = {
        'brands.Brand': [
            ('expedientes.ExpedienteSAP', 'brand_id'),
            ('productos.ProductMaster', 'brand_id'),
            ('clientes.ClientExternalCode', 'brand_id'),
            ('orders.OrdenCompra', 'brand_id'),
        ],
        'clientes.Cliente': [
            ('expedientes.ExpedienteSAP', 'client_id'),
            ('finance.Invoice', 'client_id'),
            ('orders.OrdenCompra', 'client_id'),
        ],
        # ... mas checks
    }
    
    @classmethod
    def can_delete(cls, model_path, entity_id):
        """Retorna (bool, list_of_refs) indicando si se puede borrar"""
        refs = []
        for (app_model, field_name) in cls.CHECKS.get(model_path, []):
            model = apps.get_model(app_model)
            count = model.objects.filter(**{field_name: entity_id}).count()
            if count > 0:
                refs.append({'model': app_model, 'field': field_name, 'count': count})
        return (len(refs) == 0, refs)
    
    @classmethod
    def cascade_soft_delete(cls, model_path, entity_id):
        """Soft delete en cascada: marca is_active=False en todas las referencias"""
        for (app_model, field_name) in cls.CHECKS.get(model_path, []):
            model = apps.get_model(app_model)
            model.objects.filter(**{field_name: entity_id}).update(is_active=False)
```

### 6.3 Convencion de Soft Delete en Todos los Modelos

```python
# apps/core/models.py
class BaseModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        abstract = True
    
    def soft_delete(self):
        self.is_active = False
        self.deleted_at = timezone.now()
        self.save(update_fields=['is_active', 'deleted_at'])
        EventBus.publish(f'{self._meta.app_label}.deleted', {
            'entity_type': self._meta.model_name,
            'entity_id': str(self.id)
        })
```

---

## 7. Estrategia de Migracion de Datos

### 7.1 Patron: Add -> Populate -> Verify -> Drop

Para cada FK que se elimina:

```
Fase A: ADD
  - Agregar campo nuevo: brand_id UUIDField(null=True, blank=True, db_index=True)
  - Makemigrations + migrate

Fase B: POPULATE
  - Data migration que copia: obj.brand_id = obj.brand_id (si ya es UUID)
    o: obj.brand_id = uuid.UUID(obj.brand.slug) (si brand usa slug como PK)
  
Fase C: VERIFY
  - Script que verifica: 
    SELECT COUNT(*) FROM expedientes_expedientesap WHERE brand_id IS NULL

Fase D: SWITCH
  - Actualizar codigo: reemplazar obj.brand por BrandService.get(obj.brand_id)
  - Deploy

Fase E: DROP (proximo sprint)
  - Crear migration que elimina FK field
  - Deploy
```

### 7.2 Manejo de Brand.slug como PK

`Brand` usa `slug` como PK (string), no UUID. Esto rompe la convencion.

**Opciones:**
1. **Migrar Brand a UUID:** Agregar `id UUIDField`, popular desde slug, cambiar todas las referencias. Riesgoso.
2. **Usar slug como "ID":** Guardar `brand_id = CharField(max_length=50)` en lugar de UUIDField. Mantiene compatibilidad.

**Recomendacion:** Opcion 2 (menor riesgo). El campo se llama `brand_id` pero es `CharField(50)` para brands.

---

## 8. Infraestructura para la Nueva Arquitectura

### 8.1 Docker Compose Actualizado

```yaml
# docker-compose.yml (servicios relevantes)
services:
  postgres:
    image: pgvector/pgvector:pg16
    # ... igual
  
  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data
    command: redis-server --requirepass ${REDIS_PASSWORD} --appendonly yes
  
  django:
    build: ./backend
    environment:
      DJANGO_SETTINGS_MODULE: config.settings.base
      EVENT_BUS_ENABLED: "true"
  
  celery-worker:
    # ... igual, pero con mas workers para procesar eventos
  
  dashboard-worker:
    build: ./backend
    command: celery -A config worker -l info -Q dashboard,dashboard.events
```

### 8.2 Settings para Modularidad

```python
# config/settings/base.py
INSTALLED_APPS = [
    # Core
    'apps.core',
    'apps.historial',
    'apps.dashboard',
    # Catalizadores (sin deps)
    'apps.brands',
    'apps.nodos',
    'apps.proveedores',
    # Catalogo
    'apps.productos',
    'apps.inventario',
    # Operativos
    'apps.clientes',
    'apps.orders',
    'apps.transfers',
    'apps.expedientes',
    'apps.commercial',
    # Transversales
    'apps.finance',
    'apps.cobros',
    'apps.template',
    'apps.notifications',
    'apps.portal',
    'apps.users',
    # Legacy (hasta migrar)
    'apps.liquidations',
    'apps.agreements',
]
```

---

## 9. Riesgos y Mitigaciones

| Riesgo | Impacto | Mitigacion |
|--------|---------|------------|
| **Datos huerfanos** (borro brand pero expedientes tienen brand_id invalido) | Alto | Soft delete obligatorio + ReferentialIntegrityService |
| **Performance** (N+1 queries al resolver entidades por ID) | Medio | Cache en Redis por 5 min + prefetch en serializers |
| **Consistencia eventual** (eventos async pueden perderse) | Medio | Eventos con retry + DLQ en Celery + logs en Historial |
| **Complejidad** (mas codigo para manejar relaciones) | Medio | ModuleService base + generacion de codigo para lookups |
| **Migrations masivas** (27 apps x N campos) | Medio | Fases pequenas (1-2 apps por sprint), rollback plan |
| **Frontend roto** (serializers cambian de estructura) | Medio | Mantener compatibilidad: incluir brand como nested object en serializers |
| **Tests rotos** (300+ tests usan .brand en lugar de .brand_id) | Alto | Buscar/reemplazar masivo + fixture updates |
| **OC/Expediente refactor** (cambio fundamental del dominio) | Alto | Plan de migracion de datos detallado + validacion en staging |

---

## 10. Cronograma Consolidado

```
Mes 1 (S33-S34):  FASE 0 (Cimientos) + FASE 1 (Brands, Nodos, Proveedores)
Mes 2 (S35-S36):  FASE 2 (Productos, Inventario, Sizing)
Mes 3 (S37-S38):  FASE 3 (Orders/OC, Clientes, Expedientes/SAP refactor)
Mes 4 (S39-S40):  FASE 4 (Transfers, Commercial)
Mes 5 (S41-S42):  FASE 5 (Finance, Cobros, Template, Notifications)
Mes 6 (S43-S44):  FASE 6 (Dashboard, Portal, cleanup, tests E2E)
```

### Timeline Visual

```
S33  S34  S35  S36  S37  S38  S39  S40  S41  S42  S43  S44
|----|----|----|----|----|----|----|----|----|----|----|
[F0] [F1] [F2] [F2] [F3] [F3] [F4] [F4] [F5] [F5] [F6] [F6]
     Brands      Productos   Orders      Transfers   Finance     Dashboard
     Nodos       Inventario  Clientes    Commercial  Cobros      Portal
     Proveed.    Sizing      Expedientes             Template    Cleanup
                                                       Notifs
```

---

## 11. Decisiones Arquitectonicas Clave

| # | Decision | Opcion elegida | Justificacion |
|---|----------|---------------|---------------|
| 1 | UUID o CharField para IDs? | UUIDField (36 chars) | Ya se usa en expedientes. Consistencia. |
| 2 | Soft delete o hard delete? | Soft delete obligatorio (is_active + deleted_at) | Sin FKs, no hay CASCADE. Soft delete evita huerfanos. |
| 3 | Monolito o microservicios? | Monolito logico (mismo proceso) | MWT ONE no tiene trafico para justificar microservicios. El desacoplamiento es logico, no fisico. |
| 4 | Como se comunican modulos? | Service Layer (sincrono) + Event Bus (async) | Service layer para lecturas (rapido). Event bus para escrituras (desacoplado). |
| 5 | Que pasa con Brand.slug como PK? | Mantener slug como PK, usar CharField(50) para referencias | Migrar a UUID es riesgoso y no aporta valor. |
| 6 | El Historial es Event Sourcing puro? | No. Tabla Event central + JSON payload | Event sourcing puro es overkill. Un log de cambios con snapshot es suficiente. |
| 7 | Dashboard como read model? | Si, tablas materializadas actualizadas por eventos | Evita joins cross-module. Los KPIs se calculan async. |
| 8 | OC separada de Expediente/SAP? | **Si.** `orders.OrdenCompra` es entidad propia | El flujo de negocio real es OC -> SAP(s). La arquitectura debe reflejarlo. |

---

## 12. Primer Paso Inmediato

Si decides aprobar este plan, el primer commit deberia ser:

```python
# apps/core/models.py
import uuid
from django.db import models
from django.utils import timezone

class BaseModel(models.Model):
    """Modelo base para TODOS los modulos del sistema distribuido."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        abstract = True
    
    def soft_delete(self):
        self.is_active = False
        self.deleted_at = timezone.now()
        self.save(update_fields=['is_active', 'deleted_at'])


class UUIDReferenceField(models.UUIDField):
    """Campo que almacena UUID de otra entidad SIN ForeignKey."""
    def __init__(self, *args, **kwargs):
        kwargs['editable'] = False
        kwargs['null'] = True
        kwargs['blank'] = True
        super().__init__(*args, **kwargs)
```

Y luego:

```python
# apps/core/services.py
class ModuleService:
    """Servicio base para todos los modulos."""
    
    @classmethod
    def get(cls, model_class, entity_id):
        if entity_id is None:
            return None
        try:
            return model_class.objects.get(pk=entity_id, is_active=True)
        except model_class.DoesNotExist:
            return None
```

---

## Anexos

### A. Mapa de ForeignKeys Actuales (a eliminar)

| App Origen | Campo FK | App Destino | Reemplazar por |
|------------|----------|-------------|----------------|
| `expedientes.Expediente` | `brand` | `brands.Brand` | `brand_id UUIDField` |
| `expedientes.Expediente` | `client` | `core.LegalEntity` | `client_id UUIDField` |
| `expedientes.Expediente` | `nodo_destino` | `transfers.Node` | `destination_node_id UUIDField` |
| `expedientes.ProductLine` | `product` | `productos.ProductMaster` | `product_master_id UUIDField` |
| `expedientes.ProductLine` | `brand_sku` | `brands.BrandSKU` | `variant_id UUIDField` |
| `inventario.InventoryEntry` | `product` | `productos.Producto` | `product_master_id UUIDField` |
| `inventario.InventoryEntry` | `node` | `transfers.Node` | `node_id UUIDField` |
| `commercial.RebateProgram` | `brand` | `brands.Brand` | `brand_id UUIDField` |
| `commercial.RebateAssignment` | `client` | `clientes.Cliente` | `client_id UUIDField` |
| `users.MWTUser` | `legal_entity` | `core.LegalEntity` | `legal_entity_id UUIDField` |
| `users.MWTUser` | `brand` | `brands.Brand` | `brand_id UUIDField` |
| `notifications.NotificationLog` | `expediente` | `expedientes.Expediente` | `sap_id UUIDField` |
| `knowledge.ConversationLog` | `expediente_ref` | `expedientes.Expediente` | `sap_id UUIDField` |
| `agreements.CreditPolicy` | `brand` | `brands.Brand` | `brand_id UUIDField` |
| `liquidations.Liquidation` | `matched_expediente` | `expedientes.Expediente` | `sap_id UUIDField` |

**Total estimado: ~80 ForeignKeys a eliminar/reemplazar**

### B. Convenciones de Nomenclatura

| Concepto | Convencion | Ejemplo |
|----------|------------|---------|
| Campo ID referencia | `{entidad}_id` | `brand_id`, `client_id`, `sap_id` |
| Servicio de modulo | `{Modulo}Service` | `BrandService`, `ClientService` |
| Evento de dominio | `{entidad}.{accion}` | `sap.status_changed`, `oc.created` |
| Tabla de read model | `{modulo}_{metrica}` | `dashboard_kpi`, `dashboard_widget` |
| Nombre de app Django | `apps.{nombre}` | `apps.orders`, `apps.finance` |

---

*Plan generado el 2026-04-17. Fuentes: Auditoria Backend (471 archivos Python, 94 migraciones, ~300 FKs), Auditoria Frontend (247 archivos), Auditoria Infraestructura (9 servicios Docker), Auditoria Director (13 modulos, flujo de desarrollo), y analisis del dominio de negocio OC->SAP->Expediente.*
