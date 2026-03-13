# ENT_OPS_TRANSFERS — Transferencias entre Nodos
status: DRAFT
visibility: [INTERNAL]
domain: Operaciones (IDX_OPS)
version: 1.0

---

## A. Concepto

Transfer = movimiento de producto entre dos nodos de la red operativa. Es una entidad estructural, no un artefacto. Registra qué se mueve, de dónde a dónde, bajo qué contexto legal y de pricing, y con qué artefactos asociados.

### A1. Distinción con Expediente

El expediente cubre el flujo de importación: desde la orden de compra hasta que el producto llega al primer nodo destino. El transfer toma control desde ahí: movimientos entre nodos una vez que el producto ya está en la red.

```
Fábrica ──[expediente]──▶ Primer nodo destino ──[transfer]──▶ Siguiente nodo ──[transfer]──▶ ...
```

Un expediente puede generar uno o más transfers al cerrarse. Un transfer existe independientemente de cualquier expediente (puede ser reposición interna, redistribución, etc.).

### A2. Relaciones

```
Transfer ←──from── Node
Transfer ←──to── Node
Transfer ←──genera── Expediente (opcional, cuando expediente cierra y entrega a nodo)
Transfer ←──tiene── Artifact[] (recepción, preparación, despacho, pricing approval, etc.)
Transfer ←──ancla de contexto── Automation (notificaciones, updates)
Transfer ←──ownership── LegalEntity (before/after)
```

---

## B. Modelo

```
Transfer {
  transfer_id: string              # TRF-YYYYMMDD-XXX (auto)
  
  # Movimiento
  from_node: ref → Node
  to_node: ref → Node
  
  # Qué se mueve
  items: TransferLine[]            # SKU + cantidad + talla (detalle)
  
  # Ownership
  ownership_before: ref → LegalEntity  # Quién tenía el producto
  ownership_after: ref → LegalEntity   # Quién lo tiene ahora
  ownership_changes: boolean           # true si cambia de dueño (genera pricing)
  
  # Contexto legal
  legal_context: enum              # internal | nationalization | reexport | distribution | consignment
  customs_required: boolean        # Si requiere trámite aduanal
  
  # Contexto de pricing
  pricing_context: Object | null   # Precio de transferencia entre entidades legales
  cost_lines: CostLine[]          # Costos incrementales (flete, handling, impuestos, etc.)
  
  # Vínculo con expediente
  source_expediente: ref | null    # Si nació de un expediente
  
  # Artefactos asociados
  linked_artifacts: ref[]          # Artefactos pegados a este transfer → ARTIFACT_REGISTRY
  
  # Estado
  status: enum                     # planned | approved | in-transit | received | reconciled | cancelled
  
  # Timestamps
  planned_at: datetime | null
  approved_at: datetime | null
  dispatched_at: datetime | null
  received_at: datetime | null
  reconciled_at: datetime | null
}
```

### B1. TransferLine (detalle por SKU)

```
TransferLine {
  sku: ref → SKU
  quantity_dispatched: int
  quantity_received: int | null    # Se llena al recibir
  discrepancy: int | null          # dispatched - received
  condition: enum | null           # good | damaged | partial
}
```

### B2. CostLine (costos incrementales)

```
CostLine {
  concept: string                  # "Flete DHL", "DAI 5%", "Handling", "Nacionalización"
  amount: decimal
  currency: enum                   # USD | CRC | BRL
  visibility: enum                 # internal | client
  added_at: datetime
  added_by: string
}
```

Regla: cost_lines acumulan el costo real del producto en su viaje por la red. Vista internal = MWT ve todo. Vista client = solo lo que aplica según POL_VISIBILIDAD. Ref → ENT_COMERCIAL_PRICING.D1.

---

## C. Tipos de transfer (legal_context)

| legal_context | Descripción | Ownership cambia | Pricing aplica | Customs |
|--------------|-------------|-----------------|---------------|---------|
| internal | Movimiento entre nodos de la misma LegalEntity | No | No (solo cost tracking) | No |
| nationalization | Ingreso de almacén fiscal a inventario nacional | No (misma entidad) | No | Sí (DAI%, impuestos) |
| reexport | Salida de almacén fiscal hacia otro país | No (misma entidad) | No | Sí (docs reexportación) |
| distribution | Venta/entrega a distribuidor/franquiciado | Sí | Sí (transfer pricing) | Depende |
| consignment | Producto en nodo de tercero, ownership no cambia | No | No (pero hay cost rules) | Depende |

---

## D. Condiciones de transición

| Transición | Requiere |
|-----------|----------|
| planned → approved | Aprobación CEO (si ownership_changes o monto > umbral) |
| approved → in-transit | Artefacto de despacho completado (ART-15) |
| in-transit → received | Artefacto de recepción completado en nodo destino (ART-13) |
| received → reconciled | quantity_dispatched == quantity_received para todas las líneas, o excepción aprobada |
| cualquier → cancelled | Solo CEO. Registra razón. |

---

## E. Transfers típicos por flujo de negocio

### E1. Rana Walk: China → multicanal

```
Expediente cierra en FISCAL-CR
  └── Transfer 1: FISCAL-CR → OWN-WH-CR
      legal_context: nationalization
      customs_required: true
      cost_lines: [DAI%, impuestos, handling]
      
  └── Transfer 2: OWN-WH-CR → FBA-US (via DHL)
      legal_context: internal (misma entidad MWT)
      cost_lines: [preparación, flete DHL, FBA inbound fees]
      linked_artifacts: [ART-14 Preparación, ART-15 Despacho]
      
  └── Transfer 3: FISCAL-CR → FRANQ-BR-WH
      legal_context: distribution
      ownership_changes: true
      pricing_context: {transfer_price: X, model: ref → ENT_COMERCIAL_PRICING}
      customs_required: true
```

### E2. Marluvas: Brasil → CR (contra-pedido)

```
Expediente cierra en OWN-WH-CR o SONDEL-WH-CR (según cliente)
  └── Si OWN-WH-CR: transfer interno a punto de entrega (si aplica)
  └── Si SONDEL-WH-CR: transfer de distribución
      legal_context: distribution
      ownership_changes: true (MWT → Sondel)
      pricing_context: según modelo aplicable
```

---

## F. Retroalimentación reversa (feedback loop)

Cada nodo terminal (donde se venden productos) genera datos que fluyen de vuelta al sistema:

| Nodo terminal | Método | Dato | Frecuencia | Destino |
|--------------|--------|------|-----------|---------|
| FBA-US | SP-API | Ventas por SKU/talla | Diario | ENT_OPS_DEMAND_PLANNING |
| SONDEL-WH-CR | OC-reverse / manual | Velocidad de venta inferida | Por OC | Forecast MWT |
| FRANQ-BR-WH | API / forecast-import / manual | Ventas / forecast local | [PENDIENTE CEO] | Forecast MWT |

Este feedback cierra el loop: ventas en nodos terminales → forecast global → decisión de siguiente orden a fábrica → nuevo expediente → nuevos transfers.

Ref → ENT_OPS_DEMAND_PLANNING para modelo de forecast por fase.

---

## Z. Pendientes

| ID | Pendiente | Desbloquea | Quién decide |
|----|-----------|-----------|-------------|
| Z1 | Umbral de monto para aprobación CEO en transfers | D transiciones | CEO |
| Z2 | Transfer pricing para distribuidores | pricing_context rules | CEO [CEO-ONLY] |
| Z3 | Formato de reporte de Sondel (API, CSV, manual) | E2 completo | CEO + Sondel |
| Z4 | Formato de reporte franquicia BR | F feedback | CEO + Franquiciado |
| Z5 | ¿Consignment aplica para algún caso actual? | legal_context: consignment | CEO |

---

Stamp: DRAFT — Pendiente aprobación CEO
Origen: Sesión de diseño conceptual bodegas/nodos/transfers — 2026-02-26
