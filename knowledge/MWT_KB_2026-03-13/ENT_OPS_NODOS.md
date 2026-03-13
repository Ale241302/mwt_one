# ENT_OPS_NODOS — Red de Nodos Operativos
status: DRAFT
visibility: [INTERNAL]
domain: Operaciones (IDX_OPS)
version: 1.0

---

## A. Concepto

Nodo = punto permanente en la red operativa donde el producto puede estar, transitar o venderse. Es una entidad estructural — existe independientemente de cualquier expediente, transfer o automatización.

Un nodo NO es un artefacto. No es algo que "ocurre" en un flujo. Es infraestructura operativa del negocio.

### A1. Propiedad

Todo nodo pertenece a una LegalEntity que lo administra. Ref → ENT_PLAT_LEGAL_ENTITY.

```
LegalEntity (1) ──administra──▶ Node (N)
```

La LegalEntity que administra el nodo es responsable de:
- Ejecutar los artefactos obligatorios asignados al nodo (recepción, reporte, etc.)
- Mantener actualizada la información de inventario
- Operar los conectores asociados al nodo
- Cumplir los SLA definidos

### A2. Relaciones

```
Node ←──pertenece a── LegalEntity
Node ←──origen/destino── Transfer
Node ←──ancla de contexto── Automation
Node ←──ancla de contexto── Connector
Node ←──destino final── Expediente (cuando el producto llega)
```

---

## B. Modelo

```
Node {
  node_id: string                  # FBA-US, FISCAL-CR, OWN-WH-CR, SONDEL-WH-CR, etc.
  name: string                     # Nombre legible
  type: enum                       # warehouse | fiscal | marketplace | distributor | 3pl
  
  # Propiedad
  legal_entity: ref → LegalEntity  # Quién lo administra
  operator: ref → LegalEntity | null  # Quién opera físicamente (si ≠ legal_entity)
  
  # Ubicación
  country: ref → ENT_MERCADO_{X}
  city: string | null
  
  # Capacidades
  capabilities: enum[]             # [receive, store, prepare, dispatch, report_sales, report_inventory]
  
  # Datos e integración
  ssot: enum                       # postgresql | sp-api | wms-externo | manual | inferred
  inventory_visible_to_mwt: boolean
  sales_visible_to_mwt: boolean
  sales_method: enum               # api | oc-reverse | forecast-import | manual | none
  
  # Artefactos obligatorios
  required_artifacts: ref[]        # Artefactos que este nodo debe ejecutar → ARTIFACT_REGISTRY
  
  # Operación
  sla: Object | null               # Tiempos comprometidos
  cost_rules: ref → Policy | null  # Reglas de costo (almacenaje, handling, etc.)
  
  # Estado
  status: enum                     # active | planned | inactive
}
```

Nota sobre operator vs legal_entity: FBA-US es el caso donde MWT es legal_entity (dueño del inventario) pero Amazon es operator (administra operaciones físicas). Si operator es null, legal_entity opera directamente.

---

## C. Nodos conocidos

### C1. Nodos activos

| node_id | name | type | legal_entity | operator | country | status |
|---------|------|------|-------------|----------|---------|--------|
| FBA-US | Amazon FBA USA | marketplace | MWT-CR | AMAZON-US | US | ACTIVE |

### C2. Nodos planificados

| node_id | name | type | legal_entity | operator | country | status |
|---------|------|------|-------------|----------|---------|--------|
| FISCAL-CR | Almacén fiscal CR | fiscal | MWT-CR | [PENDIENTE CEO] | CR | PLANNED |
| OWN-WH-CR | Bodega MWT CR | warehouse | MWT-CR | MWT-CR | CR | PLANNED |
| SONDEL-WH-CR | Bodega Sondel CR | [PENDIENTE CEO] | [PENDIENTE CEO] | [PENDIENTE CEO] | CR | PLANNED |
| FRANQ-BR-WH | Bodega franquicia BR | distributor | [PENDIENTE CEO] | [PENDIENTE CEO] | BR | PLANNED |

### C3. Nodos externos (sin acceso al sistema, solo referencia)

| node_id | name | type | legal_entity | country | nota |
|---------|------|------|-------------|---------|------|
| FACTORY-CN | Fábrica China (RW) | factory | FACTORY-CN | CN | Origen producto Rana Walk |
| FACTORY-BR-MARLUVAS | Marluvas SA fábrica | factory | MARLUVAS-BR | BR | Origen producto Marluvas |

---

## D. Capacidades por nodo

| node_id | receive | store | prepare | dispatch | report_sales | report_inventory |
|---------|---------|-------|---------|----------|-------------|-----------------|
| FBA-US | ✅ | ✅ | ✅ (Amazon) | ✅ (Amazon) | ✅ (SP-API) | ✅ (SP-API) |
| FISCAL-CR | ✅ | ✅ | ❌ | ✅ | ❌ | ✅ |
| OWN-WH-CR | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ |
| SONDEL-WH-CR | ✅ | ✅ | [PENDIENTE] | ✅ | [PENDIENTE] | [PENDIENTE] |
| FRANQ-BR-WH | ✅ | ✅ | [PENDIENTE] | ✅ | [PENDIENTE] | [PENDIENTE] |

---

## E. Profundidad operativa del nodo (qué se ve desde el dashboard)

El nodo es entidad estructural, pero tiene profundidad operativa. Desde el dashboard de su LegalEntity, cada nodo muestra:

### E1. Data sources (anclados al nodo, viven en capa de conectores)
Ejemplo FBA-US:
- SP-API (inventario, ventas, fees, orders)
- Advertising API (PPC campaigns, spend, ACoS)
- Helium 10 Cerebro, Magnet, Profits, Inventory Management
- [futuro: Jungle Scout, AMZScout]

Los data sources NO pertenecen al nodo. Se anclan al nodo como contexto. Ref → Connectors en ENT_PLAT_MODULOS.

### E2. Estrategia activa (policies aplicables al nodo)
Ejemplo FBA-US:
- PPC strategy → ref PLB_ADS
- Pricing strategy → ref ENT_COMERCIAL_PRICING.A
- Inventory strategy → ref ENT_OPS_INVENTARIO
- Demand planning → ref ENT_OPS_DEMAND_PLANNING

Las policies NO pertenecen al nodo. Se aplican al nodo. El nodo no contiene lógica de negocio.

### E3. Automatizaciones activas (ancladas al nodo, viven en capa de orquestación)
Ejemplo FBA-US:
- Inventory sync via SP-API (n8n, cada 4h)
- Alerta stock < 21d (n8n, event-driven)
- PPC daily report (n8n, scheduled)
- Restock calculation semanal (Windmill)

Las automatizaciones NO pertenecen al nodo. Se anclan al nodo como context_anchor. Ref → ENT_PLAT_AUTOMATIONS.

### E4. Acciones disponibles (desde el dashboard)
- Crear transfer desde/hacia este nodo
- Ver inventario por SKU/talla con semáforo
- Ver ventas (si sales_visible)
- Gestionar automatizaciones ancladas
- Ver artefactos obligatorios y su estado

Regla de diseño: el nodo es el punto donde converge la información, no donde vive. Las capas de conectores, policies y automatizaciones son independientes — el dashboard las agrega visualmente en el contexto del nodo.

---

## F. Regla de decisión para nodos futuros

```
SI: existe un punto físico o lógico donde el producto puede estar
Y: tiene identidad persistente (no es temporal)
Y: tiene un operador responsable (LegalEntity)
ENTONCES: es un nodo → modelar en ENT_OPS_NODOS

SI: es un punto temporal de tránsito sin identidad propia
ENTONCES: NO es un nodo → es parte de un Transfer (en tránsito)
```

---

## Z. Pendientes

| ID | Pendiente | Desbloquea | Quién decide |
|----|-----------|-----------|-------------|
| Z1 | ¿Almacén fiscal CR existe hoy o es futuro? ¿Tiene API? | FISCAL-CR completo | CEO |
| Z2 | ¿Bodega MWT CR es propia o alquilada? ¿Operación propia o 3PL? | OWN-WH-CR completo | CEO |
| Z3 | ¿Sondel es distribuidor, 3PL, o ambos? ¿Entidad legal separada? | SONDEL-WH-CR completo | CEO |
| Z4 | ¿Franquiciado BR existe o es concepto? ¿Entidad legal? | FRANQ-BR-WH completo | CEO |
| Z5 | Artefactos obligatorios por tipo de nodo | required_artifacts | Architect + CEO |
| Z6 | SLA por nodo (tiempos de recepción, despacho, reporte) | sla field | CEO |
| Z7 | Cost rules por nodo (almacenaje, handling) | cost_rules field | CEO |

---

Stamp: DRAFT — Pendiente aprobación CEO
Origen: Sesión de diseño conceptual bodegas/nodos/transfers — 2026-02-26
