# SCH_PROFORMA_MWT — Schema Proforma MWT (ART-02)
status: DRAFT
visibility: [INTERNAL]
domain: Plataforma (IDX_PLATAFORMA)
version: 1.0
classification: SCHEMA — Plantilla de ensamblaje para artefacto ART-02.
refs: POL_ARTIFACT_CONTRACT, ARTIFACT_REGISTRY, ENT_PLAT_ARTEFACTOS.B, ENT_PLAT_EVENTOS.B

---

## A. Identidad

| Campo | Valor |
|-------|-------|
| artifact_type_id | ART-02 |
| name | Proforma MWT |
| version | 1.0.0 |
| category | document |
| applies_to | [expediente] |
| description | Documento comercial dual-view con precios, líneas producto, tallas y condiciones. |

---

## B. Regla de dualidad

Toda proforma tiene exactamente 2 vistas del mismo dataset:

| Vista | Audience | Contenido |
|-------|----------|-----------|
| CEO | internal | Superset — precios Marluvas, comisión %, delta, arbitraje, cadena determinista |
| Marluvas | client | Solo precios cliente, líneas, tallas, condiciones, observaciones |

CEO es superset. No existen campos en Marluvas que no estén en CEO. La vista se controla por tab en webapp. Al imprimir, solo se imprime vista Marluvas.

---

## C. Estructura — Vista CEO

### C1. Header
brand, consecutivo, referencia, expediente_id, po_cliente, modelo (B/C), cliente, contacto, país, fecha.
Badges: BORRADOR (draft), CEO-ONLY · INTERNAL.

### C2. Condiciones de compra · Marluvas (card izquierda)
lista_precios, comision_pactada, condicion_pago, medio_pago, pares_calzado, pares_plantillas, total_unidades, total_compra.

### C3. Condiciones de venta · Cliente (card derecha)
po_cliente, fecha_po, credito, total_po, delta (total_po − total_compra).

### C4. Tabla de líneas — Precios paralelos + Comisión

| Col | Vista |
|-----|-------|
| #, código, producto, ncm, color, qty | ambas |
| precio_marluvas, subtotal_marluvas, comision_pct, delta_ud | CEO only |
| precio_cliente, subtotal_cliente | ambas |

Fila total con sumas. Fila nota opcional (`.ch`) bajo líneas promo. Líneas promo: clase `.promo-r`.

### C5. Tallas BRA (pills)
Por línea: label (código · referencia · N pares), pills[] con { talla_bra, qty }. Font monospace.

### C6. Comisiones — Proyección de ingreso (CEO only)
base_comision, tasa_comision, comision_bruta. Cadena determinista: aviso embarque → + crédito factura → cobro Marluvas → comisión MWT (10-15 mes siguiente).

### C7. Arbitraje CEO-ONLY
Por línea: producto, formula (qty × delta_ud), resultado. Total sobreprecio en barra navy.

### C8. Observaciones
Texto libre.

### C9. Actions (webapp only, no print)
Enviar a Marluvas, Duplicar, Editar, PDF Marluvas, Descartar.

---

## D. Estructura — Vista Marluvas

### D1. Header
brand + consecutivo. Emisor: Muito Work Limitada 3-102-751710 · Representante Regional Marluvas.

### D2. Cards tri-column
Card 1 (Cliente): cliente, contacto, país, teléfono, email.
Card 2 (Condiciones): forma de pago, plazo, moneda, valor neto en letras.
Card 3 (Datos proforma): consecutivo, PO, fecha, incoterm, pares, total.

### D3. Tabla de líneas (simplificada)
#, Código, Referencia + descripción, NCM, Color, Cantidad, Precio $, Total. Sin columnas internas.

### D4. Observaciones
Texto simplificado.

### D5. Tallas BRA (pills)
Mismo formato que C5.

### D6. Actions print
Imprimir Carta Vertical, Imprimir Carta Horizontal.

---

## E. Input schema

```
{
  expediente_id: ref → Expediente,
  po_cliente: string,
  cliente: ref → ENT_PLAT_LEGAL_ENTITY.C,
  modelo: enum [B, C],
  lineas: [{
    codigo: string,
    referencia: string,
    descripcion: string,
    ncm: string,
    color: string,
    qty: int,
    precio_marluvas: decimal,
    precio_cliente: decimal,
    comision_pct: decimal,
    tipo: enum [calzado, plantilla, accesorio],
    promo: boolean,
    promo_tag: string | null
  }],
  tallas: [{
    codigo: string,
    pills: [{ talla_bra: string, qty: int }]
  }],
  condiciones: {
    lista_precios: string,
    comision_pactada: decimal,
    condicion_pago: string,
    medio_pago: string,
    credito_dias: int,
    incoterm: string
  },
  observaciones: string
}
```

## F. Output schema

```
{
  consecutivo: string,
  referencia: string,
  brand: string,
  mode: enum [B, C],
  lineas: [{ codigo, referencia, qty, precio_cliente, subtotal_cliente }],
  montos: { total_compra, total_cliente, delta, comision_bruta },
  total_unidades: int,
  fecha: date
}
```

Evento: `proforma.created` con payload = output completo.
Evento condicional: `proforma.split` si divide AA/AB.

---

## G. Validation rules

| Regla | Condición | Acción |
|-------|-----------|--------|
| V1 | sum(lineas[].qty) ≠ total_unidades | Error: totales no cuadran |
| V2 | sum(tallas[].pills[].qty) ≠ linea.qty | Error: tallas no cuadran |
| V3 | precio_cliente < precio_marluvas en modo B | Warning: venta bajo costo |
| V4 | comision_pactada null y modelo = B | Bloqueo: comisión requerida |
| V5 | consecutivo = null o XXXX | Estado máximo = draft |

---

## H. State model

```
draft → submitted → approved → completed → void
```

requires_approval: true — CEO aprueba antes de enviar.

---

## I. Permisos

| Rol | create | view | edit | approve | complete |
|-----|--------|------|------|---------|----------|
| CEO | ✅ | ✅ full | ✅ | ✅ | ✅ |
| Sistema/IA | ✅ draft | ✅ full | ✅ draft | ❌ | ❌ |
| Cliente B2B | ❌ | ✅ vista Marluvas | ❌ | ❌ | ❌ |

---

## J. UI hints

### J1. Webapp
layout: dual-view tabs (CEO | Marluvas). Topbar fixed navy. CSS custom properties. Plus Jakarta Sans + JetBrains Mono. Responsive: tri → single at 900px.

### J2. Print
Solo vista Marluvas. Letter portrait/landscape. Margins 6mm 8mm. Oculta: topbar, badges, actions, arbitraje, CEO-ONLY. print-color-adjust exact. break-inside avoid en cards, tables, pills.

---

## K. Requires

ENT_PLAT_LEGAL_ENTITY.C, ENT_COMERCIAL_PRICING, ENT_COMERCIAL_MODELOS, ART-01 (OC Cliente), ART-03 (Decisión B/C)

## L. Policies

POL_VISIBILIDAD (dual view), POL_DETERMINISMO (dato único), POL_INMUTABILIDAD (completed = no edit), POL_NUNCA_TRADUCIR (códigos, NCM), POL_VACIO (sin dato = [PENDIENTE — NO INVENTAR])

---

## M. Lifecycle

| Campo | Valor |
|-------|-------|
| definition_status | draft |
| created_by | IA + CEO |
| approved_by | [PENDIENTE — CEO] |
| superseded_by | — |

---

Stamp: DRAFT — Pendiente aprobación CEO
