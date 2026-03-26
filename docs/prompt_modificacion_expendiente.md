# Prompt: Modificación Completa del Módulo de Expedientes

**Destinatario:** Antigravite (Agente de código)  
**Repositorio:** `Ale241302/mwt_one`  
**Fecha:** 2026-03-25  
**Alcance:** Backend Django (modelos + migraciones + API) y Frontend Next.js/TypeScript  

---

## Contexto

El sistema MWT gestiona expedientes de importación. Actualmente existen:

### Backend — campos actuales del modelo `Expediente`
- `expediente_id` — auto-generado
- `brand` — enum (SKECHERS, ON, SPEEDO, TOMS, ASICS, VIVAIA, TECMATER)
- `mode` — enum (FULL, COMISION)
- `client` — FK a LegalEntity
- `freight_mode` — enum (MARITIMO, AEREO, TERRESTRE)
- `dispatch_mode` — enum (MWT, directo)
- `price_basis` — enum (CIF, FOB, EXW)
- `destination` — enum (CR, USA)
- `status` — enum de estado operativo
- `notes` — texto libre
- `legal_entity_id` — FK a entidad MWT emisora (fijo "MWT-CR")
- Campos de crédito, costos, eventos, artefactos relacionados

### Frontend — pantallas actuales
- **`/expedientes`**: listado con columnas `custom_ref`, `status`, `client_name`, `brand_name`, `credit_days_elapsed`, `total_cost`, `last_event_at`. Filtros por estado, marca y búsqueda.
- **`/expedientes/nuevo`**: formulario de creación con selects: `cliente`, `brand`, `mode`, `destination`, `freight_mode`, `dispatch_mode`, `price_basis`, más textarea `notes`. POST a `expedientes/create/`.
- **`/expedientes/[id]`**: detalle con timeline de estados, KPIs, artefactos en acordeón, tabla de costos, historial de eventos, toggle vista interna/cliente.

---

## Objetivo

Mantener todo lo que ya funciona y agregar los nuevos campos descritos a continuación. **No eliminar ni renombrar campos existentes.** Todos los campos nuevos son **opcionales (nullable)** en el backend salvo que se indique lo contrario.

---

## PARTE 1 — BACKEND

### 1.1 Nuevos campos en el modelo `Expediente` (PostgreSQL)

Agregar una sola migración aditiva con los siguientes campos:

| Campo | Tipo Django | Null/Blank | Descripción |
|-------|-------------|------------|-------------|
| `purchase_order_number` | `CharField(max_length=100)` | null=True, blank=True | Número de orden de compra del cliente |
| `operado_por` | `CharField(max_length=20, choices=[('CLIENTE','Cliente'),('MWT','Muito Work Limitada')])` | null=True, blank=True | Quién opera el expediente |
| `url_orden_compra` | `URLField(max_length=500)` | null=True, blank=True | URL del archivo de orden de compra |

### 1.2 Nuevo modelo `ExpedienteProductLine` (líneas de productos)

Crear modelo relacionado al expediente para vincular productos:

```python
class ExpedienteProductLine(models.Model):
    expediente = models.ForeignKey(Expediente, on_delete=models.CASCADE, related_name='product_lines')
    product_id = models.CharField(max_length=100)   # ID externo del producto
    size_id = models.CharField(max_length=50)        # ID de la talla
    quantity = models.PositiveIntegerField()
    price_id = models.CharField(max_length=100)      # ID del precio aplicado
    quantity_modified = models.PositiveIntegerField(null=True, blank=True)  # si fue modificada
    price_id_modified = models.CharField(max_length=100, null=True, blank=True)  # si fue modificada
    separated_to_expediente = models.ForeignKey(
        'self', null=True, blank=True, on_delete=models.SET_NULL,
        related_name='separated_lines'
    )  # referencia si los productos se separaron a otro expediente
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

El endpoint `expedientes/create/` debe aceptar un array `product_lines` con objetos `{product_id, size_id, quantity, price_id}`.

### 1.3 Campos por estado (agregar al modelo `Expediente`)

Todos los campos nuevos son **nullable**. Organízalos por fase operativa:

#### Estado: REGISTRO
| Campo | Tipo | Descripción |
|-------|------|-------------|
| `ref_number` | `CharField(100)` | Número de pedido (REF) — editable en este estado |
| `credit_days_client` | `IntegerField` | Días de crédito del cliente (si `operado_por=CLIENTE`) |
| `credit_days_mwt` | `IntegerField` | Días de crédito MWT (si `operado_por=MWT`) |
| `credit_limit_client` | `DecimalField(12,2)` | Crédito disponible del cliente |
| `credit_limit_mwt` | `DecimalField(12,2)` | Crédito disponible MWT |
| `order_value` | `DecimalField(12,2)` | Valor total del pedido |

#### Estado: PRODUCCION
| Campo | Tipo | Descripción |
|-------|------|-------------|
| `sap_number` | `CharField(100)` | Número SAP de fábrica |
| `proforma_client_number` | `CharField(100)` | Número de proforma (si `operado_por=CLIENTE`) |
| `proforma_mwt_number` | `CharField(100)` | Número proforma Muito Work Limitada (si `operado_por=MWT`) |
| `fabrication_start_date` | `DateField` | Fecha inicio fabricación |
| `fabrication_end_date` | `DateField` | Fecha finalización fabricación |
| `url_proforma_cliente` | `URLField(500)` | URL proforma cliente |
| `url_proforma_muito_work` | `URLField(500)` | URL proforma Muito Work Limitada |
| `merged_expedientes` | `ManyToManyField('self', blank=True, symmetrical=False)` | Expedientes fusionados — la info de este estado en adelante se comparte |

**Lógica de fusión:** cuando dos expedientes se fusionan, los campos desde el estado PRODUCCION en adelante deben sincronizarse. Si uno cambia, se refleja en el otro. Implementar con señales (`post_save`) o un mecanismo de referencia maestra (`master_expediente_id = FK(self, null=True)`).

#### Estado: PREPARACION
| Campo | Tipo | Descripción |
|-------|------|-------------|
| `shipping_method` | `CharField(100)` | Método de envío |
| `incoterms` | `CharField(20)` | Incoterms (EXW, FOB, CIF, etc.) |
| `cargo_manager` | `CharField(20, choices=[('CLIENTE','Cliente'),('FABRICA','Fábrica')])` | Gestor de la carga |
| `shipping_value` | `DecimalField(12,2)` | Valor del envío |
| `payment_mode_shipping` | `CharField(20, choices=[('PREPAGO','Prepago'),('CONTRAENTREGA','Contraentrega')])` | Modo de pago del flete |
| `url_list_empaque` | `URLField(500)` | URL lista de empaque |
| `url_cotizacion_envio` | `URLField(500)` | URL cotización de envío |

Las `product_lines` del expediente actúan como **líneas originales de la orden**. Las modificaciones (precio, cantidad, separación) se registran en los campos `quantity_modified`, `price_id_modified`, `separated_to_expediente` del modelo `ExpedienteProductLine`. El API debe exponer un resumen de movimientos de líneas en el endpoint de detalle.

#### Estado: DESPACHO
| Campo | Tipo | Descripción |
|-------|------|-------------|
| `airline_or_shipping_company` | `CharField(200)` | Aerolínea o naviera |
| `awb_bl_number` | `CharField(100)` | Número AWB (aéreo) o BL (marítimo) |
| `origin_location` | `CharField(200)` | Lugar de origen |
| `arrival_location` | `CharField(200)` | Lugar de arribo |
| `shipment_date` | `DateField` | Fecha de embarque |
| `payment_date_dispatch` | `DateField` | Fecha de pago en despacho |
| `invoice_client_number` | `CharField(100)` | Número factura cliente (si `operado_por=CLIENTE`) |
| `invoice_mwt_number` | `CharField(100)` | Número factura Muito Work Limitada (si `operado_por=MWT`) |
| `dispatch_additional_info` | `TextField` | Información adicional de despacho |
| `url_certificado_origen` | `URLField(500)` | URL certificado de origen |
| `url_factura_cliente` | `URLField(500)` | URL factura cliente |
| `url_factura_muito_work` | `URLField(500)` | URL factura Muito Work Limitada |
| `url_awb_bl` | `URLField(500)` | URL documento AWB o BL |

#### Estado: TRANSITO
| Campo | Tipo | Descripción |
|-------|------|-------------|
| `intermediate_airport_or_port` | `CharField(200)` | Aeropuerto o puerto intermedio |
| `transit_arrival_date` | `DateField` | Fecha de arribo en tránsito |
| `url_packing_list_detallado` | `URLField(500)` | URL packing list detallado |

### 1.4 Nuevo modelo `ExpedientePago`

Crear modelo para registrar uno o más pagos por expediente:

```python
class ExpedientePago(models.Model):
    TIPO_PAGO = [('COMPLETO', 'Completo'), ('PARCIAL', 'Pago Parcial')]
    METODO_PAGO = [('TRANSFERENCIA', 'Transferencia Bancaria'), ('NOTA_CREDITO', 'Nota de Crédito')]

    expediente = models.ForeignKey(Expediente, on_delete=models.CASCADE, related_name='pagos')
    tipo_pago = models.CharField(max_length=20, choices=TIPO_PAGO)
    metodo_pago = models.CharField(max_length=30, choices=METODO_PAGO)
    payment_date = models.DateField()
    amount_paid = models.DecimalField(max_digits=12, decimal_places=2)
    additional_info = models.TextField(null=True, blank=True)
    url_comprobante = models.URLField(max_length=500, null=True, blank=True)  # puede haber más de uno
    created_at = models.DateTimeField(auto_now_add=True)
```

**Lógica de crédito:** cada vez que se registra o modifica un pago, el backend debe recalcular el crédito disponible del cliente o MWT (según `operado_por`) y actualizar `credit_limit_client` o `credit_limit_mwt` restando el saldo pendiente. Esta lógica va en `services/financial.py`.

### 1.5 Endpoints nuevos / modificados

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| `POST` | `expedientes/create/` | Aceptar nuevos campos opcionales + `product_lines[]` |
| `PATCH` | `expedientes/{id}/update-registro/` | Actualizar campos del estado REGISTRO |
| `PATCH` | `expedientes/{id}/update-produccion/` | Actualizar campos del estado PRODUCCION |
| `PATCH` | `expedientes/{id}/update-preparacion/` | Actualizar campos del estado PREPARACION |
| `PATCH` | `expedientes/{id}/update-despacho/` | Actualizar campos del estado DESPACHO |
| `PATCH` | `expedientes/{id}/update-transito/` | Actualizar campos del estado TRANSITO |
| `POST` | `expedientes/{id}/pagos/` | Registrar un pago nuevo |
| `PATCH` | `expedientes/{id}/pagos/{pago_id}/` | Modificar un pago existente |
| `POST` | `expedientes/{id}/merge/` | Fusionar con otro expediente (body: `{target_expediente_id}`) |
| `POST` | `expedientes/{id}/separate-products/` | Separar líneas de productos (body: `{product_line_ids[], target_expediente_id?}`) — si no se provee target, crear nuevo expediente |
| `DELETE` | `expedientes/{id}/url-orden-compra/` | Eliminar solo el campo `url_orden_compra` (set null) |

El endpoint `GET ui/expedientes/{id}/` debe incluir en el bundle:
- `product_lines`: lista de líneas originales + sus modificaciones
- `product_lines_summary`: resumen de movimientos (cuántas líneas originales, modificadas, separadas)
- `pagos`: lista de pagos registrados
- `credit_status`: crédito disponible actualizado según pagos

---

## PARTE 2 — FRONTEND

### 2.1 Formulario `/expedientes/nuevo` — campos adicionales

Mantener todos los campos actuales. Agregar los siguientes campos **opcionales** al formulario:

| Campo | Tipo UI | Descripción |
|-------|---------|-------------|
| `purchase_order_number` | `<input type="text">` | Número de orden de compra |
| `operado_por` | `<select>` | Opciones: `CLIENTE` = "Cliente", `MWT` = "Muito Work Limitada" |
| `product_lines` | Sección dinámica | Array de líneas. Botón "+ Agregar producto". Cada línea tiene: `product_id` (select/input), `size_id` (select/input), `quantity` (input number), `price_id` (select/input). Botón "×" para eliminar una línea. |

### 2.2 Vista detalle `/expedientes/[id]` — sección por estado

La vista detalle ya tiene un timeline de estados. Cuando el usuario hace clic en un estado, mostrar **únicamente los campos de ese estado**. Los campos que no corresponden al estado activo deben estar ocultos.

#### Comportamiento general de edición
- Todos los campos son **editables inline** (click en el campo → edición). Al confirmar, llama al endpoint `PATCH` correspondiente.
- Los campos de tipo URL muestran: si hay valor → link clicable + botón "Editar" + botón "Eliminar". Si no hay valor → botón "Subir archivo" que sube a storage y guarda la URL resultante.
- Los campos fecha usan `<input type="date">`.
- Los campos de selección usan `<select>`.
- Los campos de texto libre usan `<input type="text">` o `<textarea>` según largo esperado.

#### Estado: REGISTRO

Mostrar y permitir editar:
- `ref_number` — input text — label: "N° de Pedido (REF)"
- `purchase_order_number` — input text — label: "N° de Orden de Compra"
- `client` — select (LegalEntities) — label: "Cliente"
- `operado_por` — select (Cliente / Muito Work Limitada) — label: "Operado por"
- Si `operado_por === 'CLIENTE'`: mostrar `credit_days_client` y `credit_limit_client`
- Si `operado_por === 'MWT'`: mostrar `credit_days_mwt` y `credit_limit_mwt`
- `order_value` — input number — label: "Valor del Pedido"
- `url_orden_compra` — campo URL con opción de **eliminar solo este campo** (DELETE al endpoint dedicado)

> ⚠️ Cuando `operado_por` cambia de CLIENTE a MWT (o viceversa), ocultar los campos del operado anterior y mostrar los del nuevo. Nunca mostrar ambos al mismo tiempo.

#### Estado: PRODUCCION

Mostrar y permitir editar:
- `sap_number` — input text — label: "N° SAP"
- Si `operado_por === 'CLIENTE'`: `proforma_client_number` — label: "N° de Proforma"
- Si `operado_por === 'MWT'`: `proforma_mwt_number` — label: "N° de Proforma Muito Work Limitada"
- `fabrication_start_date` — input date — label: "Fecha Inicio Fabricación"
- `fabrication_end_date` — input date — label: "Fecha Finalización Fabricación"
- `url_proforma_cliente` — campo URL
- `url_proforma_muito_work` — campo URL

**Botones de acción especiales en este estado:**

1. **"Unir expedientes"** — abre modal con buscador de expedientes. Seleccionar uno o más. Al confirmar, llama a `POST expedientes/{id}/merge/`. Mostrar badge con los expedientes fusionados actualmente. Nota informativa: _"Los campos de este estado en adelante se sincronizarán con los expedientes fusionados."_

2. **"Separar productos"** — abre modal que muestra la lista de `product_lines`. El usuario selecciona cuáles separar con checkboxes. Luego elige: "Crear nuevo expediente" o "Mover a expediente existente" (con buscador). Al confirmar, llama a `POST expedientes/{id}/separate-products/`.

#### Estado: PREPARACION

Mostrar y permitir editar:
- `shipping_method` — input text — label: "Método de Envío"
- `incoterms` — select con opciones estándar (EXW, FOB, FCA, CFR, CIF, CPT, CIP, DAP, DPU, DDP) — label: "Incoterms"
- `cargo_manager` — select (Cliente / Fábrica) — label: "Gestor de la Carga"
- `shipping_value` — input number — label: "Valor de Envío (USD)"
- `payment_mode_shipping` — select (Prepago / Contraentrega) — label: "Modo de Pago del Flete"
- `url_list_empaque` — campo URL
- `url_cotizacion_envio` — campo URL

**Sección de líneas de productos:**
- Tabla **"Líneas originales"**: muestra las `product_lines` tal como se crearon (product_id, size_id, quantity, price_id).
- Tabla **"Líneas modificadas"**: muestra las líneas que tuvieron cambios de precio (`price_id_modified`), cantidad (`quantity_modified`) o fueron separadas (`separated_to_expediente` ≠ null).
- **Resumen de movimientos**: componente tipo badge/chips que muestra: total original, total modificadas, total separadas.

#### Estado: DESPACHO

Mostrar y permitir editar:
- `airline_or_shipping_company` — input text — label: "Aerolínea / Naviera"
- `awb_bl_number` — input text — label: "N° AWB / BL"
- `origin_location` — input text — label: "Lugar de Origen"
- `arrival_location` — input text — label: "Lugar de Arribo"
- `shipment_date` — input date — label: "Fecha de Embarque"
- `payment_date_dispatch` — input date — label: "Fecha de Pago"
- Si `operado_por === 'CLIENTE'`: `invoice_client_number` — label: "N° Factura Cliente"
- Si `operado_por === 'MWT'`: `invoice_mwt_number` — label: "N° Factura Muito Work Limitada"
- `dispatch_additional_info` — textarea — label: "Información Adicional"
- `url_certificado_origen` — campo URL
- Si `operado_por === 'CLIENTE'`: `url_factura_cliente` — campo URL
- Si `operado_por === 'MWT'`: `url_factura_muito_work` — campo URL
- `url_awb_bl` — campo URL

> ⚠️ Igual que en REGISTRO: los campos de Muito Work Limitada y los del cliente son mutuamente excluyentes según `operado_por`.

#### Estado: TRANSITO

Mostrar y permitir editar:
- `intermediate_airport_or_port` — input text — label: "Aeropuerto / Puerto Intermedio"
- `transit_arrival_date` — input date — label: "Fecha de Arribo"
- `url_packing_list_detallado` — campo URL

#### Sección de Pagos (visible en cualquier estado desde DESPACHO en adelante)

Mostrar lista de pagos registrados. Cada pago muestra: tipo, método, fecha, monto, información adicional, link al comprobante.

Botón **"+ Registrar Pago"** que abre modal con:
- `tipo_pago` — select — "Completo" / "Pago Parcial"
- `metodo_pago` — select — "Transferencia Bancaria" / "Nota de Crédito"
- `payment_date` — input date — "Fecha de Pago"
- `amount_paid` — input number — "Valor Pagado (USD)"
- `additional_info` — textarea — "Información Adicional" (opcional)
- `url_comprobante` — campo de subida de archivo — "Comprobante" (opcional, puede haber más de uno)

Después de registrar un pago, el frontend debe refrescar el indicador de crédito disponible (`credit_limit_client` o `credit_limit_mwt`) en los KPIs del detalle.

---

## PARTE 3 — REGLAS GENERALES

### Campos condicionales por `operado_por`
- Si `operado_por === 'CLIENTE'`: mostrar siempre los campos con sufijo `_client` y ocultar los `_mwt`.
- Si `operado_por === 'MWT'`: mostrar siempre los campos con sufijo `_mwt` y ocultar los `_client`.
- Si `operado_por` es null (sin definir): mostrar ambos grupos o ninguno, según decisión de UX. Recomendado: mostrar un mensaje "Define el operado para ver estos campos".

### Manejo de archivos/URLs
- Los campos `url_*` no suben archivos directamente al backend Django. El frontend sube el archivo a un storage externo (Cloud Storage / S3) y guarda la URL resultante en el campo del modelo.
- En el UI: mostrar link azul si hay URL, con ícono de abrir en nueva pestaña. Botón "Editar" reemplaza la URL. Botón "Eliminar" pone el campo en null (solo disponible donde aplica).
- El campo `url_orden_compra` tiene eliminación dedicada (DELETE endpoint propio).

### Sincronización de expedientes fusionados
- Cuando se editan campos de los estados PRODUCCION, PREPARACION, DESPACHO, TRANSITO en un expediente fusionado, el cambio debe propagarse a todos los expedientes del grupo fusionado.
- En el detalle, mostrar un banner informativo: _"Este expediente está fusionado con [lista de refs]. Los cambios desde Producción se sincronizan automáticamente."_

### Separación de productos
- Al separar productos a un nuevo expediente: el nuevo hereda `brand`, `client`, `operado_por`, `mode` del original. Los campos de estado quedan vacíos.
- Al separar a un expediente existente: simplemente reasignar las líneas.
- Las líneas separadas permanecen visibles en el expediente original con indicador "separado → REF-XXXX".

---

## PARTE 4 — MIGRACIÓN

Generar **una sola migración aditiva** con todos los campos nuevos. Todos son `null=True, blank=True`. No hacer ALTER destructivo ni renombrar campos existentes.

Orden sugerido:
1. Agregar campos nuevos al modelo `Expediente`
2. Crear modelo `ExpedienteProductLine`
3. Crear modelo `ExpedientePago`
4. Registrar en admin Django
5. Escribir serializers
6. Escribir/actualizar endpoints
7. Tests en `backend/tests/test_expediente_fields.py`

---

## PARTE 5 — LO QUE NO DEBES TOCAR

- ❌ No eliminar ni renombrar campos existentes del modelo `Expediente`
- ❌ No modificar el listado `/expedientes/page.tsx` más allá de lo necesario
- ❌ No cambiar la lógica de estados canónicos ni el `ENT_OPS_STATE_MACHINE.md`
- ❌ No tocar `docker-compose.yml`, nginx ni settings de infra
- ❌ No crear nuevas rutas de navegación (solo extender las existentes)

---

## Checklist de entrega

```
BACKEND
[ ] Migración única con todos los campos nuevos
[ ] Modelo ExpedienteProductLine creado y registrado en admin
[ ] Modelo ExpedientePago creado y registrado en admin
[ ] Campo operado_por en Expediente con lógica condicional
[ ] Endpoints PATCH por estado implementados
[ ] Endpoint POST pagos/ implementado con lógica de crédito
[ ] Endpoint merge/ implementado con sincronización por señales
[ ] Endpoint separate-products/ implementado
[ ] DELETE url-orden-compra/ implementado
[ ] Bundle de detalle incluye product_lines, product_lines_summary, pagos, credit_status
[ ] Tests en test_expediente_fields.py (al menos smoke test por campo nuevo)

FRONTEND
[ ] Formulario /nuevo con campos opcionales nuevos y sección product_lines dinámica
[ ] Detalle /[id]: campos visibles solo en su estado correspondiente
[ ] Lógica condicional operado_por (cliente ↔ MWT) en todos los estados
[ ] Campos URL con acciones: ver, editar, eliminar (donde aplique)
[ ] Modal "Unir expedientes" con buscador
[ ] Modal "Separar productos" con checkboxes y destino
[ ] Sección pagos con modal de registro
[ ] Banner de expedientes fusionados
[ ] Tabla líneas originales vs modificadas en PREPARACION
[ ] Crédito disponible se refresca al registrar pago
```
