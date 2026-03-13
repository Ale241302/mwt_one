# ENT_OPS_EXPEDIENTE — Expedientes de Importación
status: DRAFT
visibility: [INTERNAL]
domain: Operaciones (IDX_OPS)
version: 1.0

---

## A. Concepto

Expediente = contenedor modular que agrupa todos los documentos, hitos, costos y eventos de una operación de importación/exportación. Se construye con artefactos (ref → ENT_PLAT_ARTEFACTOS). Cada expediente pertenece a una marca y un modo de operación.

## B. Campos base de todo expediente

| Campo | Tipo | Descripción |
|-------|------|-------------|
| expediente_id | auto | Identificador único |
| brand | enum | marluvas / tecmater / ranawalk |
| mode | enum | COMISION / FULL | 
| client_id | ref | Cliente que origina la operación |
| created_at | datetime | Fecha apertura |
| status | enum | Estado actual (ref → sección D) |
| freight_mode | enum | prepaid / postpaid |
| transport_mode | enum | aereo / maritimo |
| dispatch_mode | enum | mwt / client |
| price_basis | enum | fob / en_plaza / costo_margen |

mode = COMISION solo aplica Marluvas (ref → ENT_COMERCIAL_MODELOS.C).

## C. Fases operativas (Marluvas — flujo completo)

### C1. Fase 1 — Orden
- Cliente envía OC → CEO evalúa delta → decide B o C.
- Sistema genera Proforma con consecutivo. [PENDIENTE — BIZ-01: formato consecutivo]
- Si inventario parcial: divide proforma AA/AB.
- Proforma por correo a Marluvas. Futuro: automático vía Salesforce o sistema.
- Artefactos: OC Cliente, Proforma MWT, Decisión B/C [CEO-ONLY].

### C2. Fase 2 — Confirmación fábrica
- Marluvas indexa pedido, devuelve registro SAP (ID interno).
- Control vía mail con número proforma como referencia.
- Marluvas informa fecha probable fabricación a COMEX.
- Sistema registra e informa cliente fecha probable embarque.
- Artefactos: Confirmación SAP (ID, fecha fabricación).

### C3. Fase 3 — Logística
- Coordinar espacio barco/avión (puede saturarse en temporada alta).
- AWB (aéreo) o BL (marítimo) con datos: carrier, origen, destino, tracking, itinerario (si escalas).
- Modo flete: prepaid o postpaid.
- Iteración documental: verificar documentación completa + cotización envío + modo.
- Artefactos: AWB/BL, Cotización flete.

### C4. Fase 4 — Aprobación y despacho
- Correo a cliente con documentación + cotización flete + modo para aprobación.
- Variante: cliente usa su despachante (MWT entrega carga en punto acordado) vs MWT gestiona despacho completo.
- Establece fecha probable llegada basada en itinerarios.
- Registra todo en base histórica.
- Artefactos: Aprobación despacho, Documentación aduanal (si dispatch_mode = mwt).

### C5. Fase 5 — Inteligencia operativa
- Data histórica cruza: tiempos por ruta, tiempos fabricación por familia producto, costos por modo transporte.
- Sistema sugiere modo óptimo (marítimo vs aéreo) basado en: volumen pedido, urgencia, costo comparativo, historial ruta.
- Existe punto óptimo donde costo aéreo vs marítimo se cruza según volumen y urgencia.
- Artefactos: Base histórica (no es artefacto de expediente, es sistema transversal).

## D. Estados por marca

### D1. Marluvas (7 estados)
```
Registro → Producción → Preparación → Despacho → Tránsito → En destino → Histórico
```

### D2. Tecmater (4 estados)
```
Orden → Preparación → Despacho → Tránsito
```
Producto listo en stock fábrica. Sin fase producción ni SAP.

### D3. Rana Walk (bifurcación)
```
Orden → Fabricación (CN) → Despacho → Tránsito CR → [Bifurcación]
  ├── Nacionalización CR → Almacén local
  └── Almacén fiscal → Reexportación (USA / Brasil / otro)
```

## E. Condiciones de transición (Marluvas)

| Transición | Requiere |
|-----------|----------|
| Registro → Producción | OC Cliente + Proforma MWT + Confirmación SAP |
| Producción → Preparación | Fecha fabricación cumplida |
| Preparación → Despacho | AWB/BL + cotización flete aprobada + aprobación despacho + docs aduanales (si dispatch_mode=mwt) |
| Despacho → Tránsito | Confirmación embarque carrier |
| Tránsito → En destino | Tracking confirma llegada |
| En destino → Histórico | Entrega confirmada + factura emitida + cobro registrado |

## F. Elementos rastreados por expediente

### F1. Documentos
OC cliente, Proforma MWT (consecutivo AA/AB), registro SAP Marluvas, AWB/BL (tracking, itinerario), cotización flete, aprobación cliente, factura MWT, nota compensación [CEO-ONLY].

### F2. Fechas (hitos)
OC recibida, proforma enviada, confirmación SAP, probable fabricación, probable embarque, probable llegada, real de cada hito.

### F3. Datos envío
Carrier, origen, destino, tracking, itinerario completo, modo aéreo/marítimo, flete prepaid/postpaid, consolidación sí/no.

### F4. Base histórica (para forecast)
Duración real por fase, costo real por modo/ruta, tiempos por carrier, volumen vs costo → curva punto óptimo.

## G. Automatizaciones identificadas

| Automatización | Prioridad | Complejidad |
|---------------|-----------|-------------|
| Consecutivo proforma auto-generado | Alta | Baja |
| Mail a Marluvas automático | Alta | Media |
| Trigger fecha fabricación post-SAP | Media | Baja |
| Notificación cliente fecha embarque | Alta | Baja |
| Workflow aprobación en sistema | Alta | Media |
| Event sourcing automático por cambio estado | Alta | Alta |
| Análisis ruta óptima con sugerencia automática | Media | Alta |

## H. Regla MOQ en expediente

Pedido en múltiplos caja master del SKU. Warning (no bloqueo) si cantidad no calza. CEO puede aprobar excepción (caja incompleta). Registrado en expediente para trazabilidad.
Ref → catálogo por marca para MOQ y grade de tallas por SKU.

---

Stamp: DRAFT — Pendiente aprobación CEO
