# ENT_COMERCIAL_MODELOS — Modelos de Negocio por Marca
status: DRAFT
visibility: [CEO-ONLY]
domain: Comercial (IDX_COMERCIAL)
version: 1.0

---

## A. Clasificación de marcas

| Marca | Tipo | brand_type | Origen | SKUs |
|-------|------|-----------|--------|------|
| Rana Walk | Línea propia (IP MWT) | own | Fabricación tercero CN según specs MWT | 54 |
| Marluvas | Marca representada | represented | Marluvas SA, Brasil | 565 |
| Tecmater | Marca representada | represented | Tecmater, Brasil | 38 |

Regla: cada marca = universo independiente. No se mezclan en catálogo ni pricing.

## B. Modelos de pricing

### B1. Modelo A — Costo + margen (Rana Walk)
- MWT define precio. No hay tabla externa.
- Costo = FOB China + flete + nacionalización + FBA fees.
- Margen = CEO decide.
- [PENDIENTE — fórmula específica no definida. CEO-ONLY]

### B2. Modelo A simple — EXWork fijo (Tecmater)
- Tecmater publica lista de precios EXWork fijo.
- MWT compra a precio lista + agrega margen.
- Siempre modo FULL (MWT importa y revende).
- Precio al cliente = precio en plaza todo incluido (absorbe fletes, seguros, aduana).
- Cliente nunca ve desglose de costos intermedios.

### B3. Modelo B — Comisión (Marluvas)
- Cliente envía OC con sobreprecio negociado.
- Delta (sobreprecio - precio tabla Marluvas) va a Marluvas como margen adicional.
- MWT negocia producto extra al envío (Marluvas acepta porque margen cubierto).
- MWT cobra comisión sobre monto total OC (incluyendo sobreprecio).
- Fórmula: `Precio_Final = Precio_Base × (1.0183^(100 × Comisión)) × Índice_Pago`
- Ref → ENT_COMERCIAL_PRICING para fórmula detallada y condiciones SAP.
- Cliente recibe extras como valor agregado.
- MWT gana: comisión sobre monto mayor + cliente contento.
- Marluvas gana: vendió más volumen.
- Cliente gana: recibió extras sin negociar.

### B4. Modelo C — Importación directa / FULL (Marluvas)
- Cuando sobreprecio es grande, CEO decide importar directo.
- MWT compra a precio tabla Marluvas FOB.
- MWT importa, nacionaliza, revende a precio OC cliente.
- MWT captura todo el delta como margen propio.
- Más riesgo (inventario, capital, aduana) pero más margen.
- Factura al cliente = vista client siempre (precio negociado).
- Vista internal = FOB + costos acumulados etapa por etapa (flete, seguro, aduana, DAI%, almacenaje).

## C. Decisión B vs C (Marluvas)

- CEO elige por transacción. No es fijo por cliente ni por producto.
- Mismo cliente puede tener transacciones en ambos modelos.
- Criterio: arbitraje del delta (diferencia precio OC vs costo real).
- [PENDIENTE — BIZ-02: ¿umbral numérico o intuición CEO?]
- El cliente nunca sabe qué modo opera.
- Sistema puede sugerir modo óptimo basado en histórico decisiones B vs C con resultados reales.

## D. Facturación por modelo

| Modelo | Quién factura | Vista cliente | Vista internal |
|--------|--------------|---------------|----------------|
| B (Comisión) | Marluvas factura al cliente. MWT factura comisión a Marluvas. | Precio OC | Comisión sobre total OC |
| C (FULL Marluvas) | MWT factura al cliente | Precio negociado | FOB + costos acumulados por etapa |
| A (Tecmater) | MWT factura al cliente | Precio en plaza todo incluido | EXWork + costos intermedios |
| A (Rana Walk) | MWT factura vía Amazon o directo | Precio Amazon/negociado | Costo + margen [PENDIENTE] |

## E. Transporte — variable por transacción

| Variable | Opciones | Quién decide |
|----------|----------|-------------|
| freight_mode | prepaid / postpaid | Por transacción |
| transport_mode | aéreo / marítimo | Por transacción (sistema sugiere basado en histórico) |
| dispatch_mode | MWT gestiona / Cliente gestiona | Cliente decide |
| price_basis | FOB (Marluvas B/C) / En plaza (Tecmater) / Costo+margen (RW) | Por marca |

Prepaid: flete incluido en factura proveedor. Postpaid: flete se paga al retiro. Expediente registra modalidad — afecta timing registro costo y flujo de caja.

---

Stamp: DRAFT — Pendiente aprobación CEO
