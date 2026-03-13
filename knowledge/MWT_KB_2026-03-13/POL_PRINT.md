# POL_PRINT — Especificación de Impresión Obligatoria
status: DRAFT
visibility: [INTERNAL]
domain: Plataforma (IDX_PLATAFORMA)
version: 1.0
classification: POLICY — Constraint obligatorio para todo output HTML imprimible del proyecto.
refs: ENT_COMP_VISUAL, ENT_PLAT_DESIGN_TOKENS, POL_VISIBILIDAD, POL_NUEVO_DOC

---

## A. Alcance

Todo output HTML del proyecto que declare funcionalidad de impresión DEBE incluir el bloque de impresión canónico completo definido en esta policy. No es opcional. No se simplifica. No se omite parcialmente.

Aplica a: proformas (ART-02), facturas (ART-09, ART-10), fichas técnicas, briefs, reportes, y cualquier artefacto o schema que produzca HTML con botón/acción de imprimir.

No aplica a: dashboards interactivos sin función de impresión, componentes webapp sin output físico.

---

## B. CSS @media print — Bloque canónico obligatorio (13 reglas)

Todo output imprimible DEBE incluir estas 13 reglas exactas en su `<style>`. El orden es significativo.

### B1. Forzar colores y backgrounds
```css
*{-webkit-print-color-adjust:exact!important;print-color-adjust:exact!important;color-adjust:exact!important;}
```
Sin esto, los navegadores eliminan backgrounds y colores de marca.

### B2. Ocultar elementos interactivos/webapp
```css
.top{display:none!important;}
.actions{display:none!important;}
.print-actions{display:none!important;}
```
Regla: todo elemento con clase `.actions`, `.print-actions`, o `.top` (topbar navegación) se oculta. Schemas individuales pueden agregar clases adicionales a ocultar (ej. `.bg-draft`, `.bg-ceo`, `.arb` en proformas).

### B3. Solo vista activa, sin padding de topbar
```css
.view{display:none!important;}
.view.active{display:block!important;padding-top:0!important;}
```
Si el documento tiene dual-view o multi-view, solo imprime la vista activa al momento de invocar impresión.

### B4. Márgenes mínimos
```css
@page{margin:6mm 8mm;size:letter;}
```
Letter es el formato base. La orientación (portrait/landscape) se inyecta dinámicamente por JS (ver §C).

### B5. Tipografía documento comercial
```css
body{background:white!important;font-size:11px;}
.dash{max-width:100%;padding:0;}
```

### B6. Tabla — font reducido para portrait
```css
table.ct{font-size:10px;}
table.ct thead th{font-size:8.5px;padding:6px 8px;background:#f1f5f9!important;border-bottom:2px solid #999!important;}
table.ct tbody td{padding:6px 8px;}
table.ct .trow{background:#f1f5f9!important;}
table.ct .trow td{border-top:2px solid #333!important;}
table.ct .ch{font-size:9px;}
table.ct .promo-r{background:#f5f3ff!important;}
```
Si el output no usa promo-r, la regla no causa daño (clases inexistentes se ignoran).

### B7. Cards y secciones — bordes visibles en impresión
```css
.card,.sect,.head{border:1px solid #ccc!important;}
.card-h{border-bottom:1px solid #ccc!important;}
.sect,.card{margin-bottom:10px;}
.head{margin-bottom:12px;}
.notes-card{border:1px solid #ccc!important;margin-bottom:10px;}
```

### B8. Grid — mantener columnas
```css
.tri{grid-template-columns:1fr 1fr 1fr;gap:10px;}
.dual{grid-template-columns:1fr 1fr;gap:10px;}
.tri .card-b{font-size:10px;}
.tri .card-b .sr{padding:4px 0;}
.tri .card-h{padding:8px 14px;}
.tri .card-b{padding:10px 14px;}
```

### B9. Prevenir cortes de contenido
```css
.card,.sect,.head,.notes-card{break-inside:avoid;page-break-inside:avoid;}
table.ct{break-inside:avoid;page-break-inside:avoid;}
table.ct tr{break-inside:avoid;page-break-inside:avoid;}
.pill-group{break-inside:avoid;page-break-inside:avoid;}
```

### B10. Salto de página preferido
```css
.sect:last-of-type{break-before:auto;}
```

### B11. Pills compactos para impresión
```css
.pill{padding:3px 7px;min-width:40px;}
.pill .s{font-size:8px;}
.pill .q{font-size:11px;}
.pill-group .pl{font-size:9px;margin-bottom:4px;}
.pill-group{margin-bottom:10px;}
.pills{gap:4px;}
```
Si el output no usa pills, esta regla no causa daño (clases inexistentes se ignoran).

### B12. Valor neto en letras
```css
.sr .v[style*="font-style:italic"]{font-size:9px!important;}
```

### B13. Links y badges
```css
a{text-decoration:none;color:inherit;}
.badge{border:1px solid currentColor;}
```

---

## C. JavaScript — Orientación dinámica obligatoria

Todo output imprimible con opción portrait/landscape DEBE incluir esta función. El `<style id="print-orientation"></style>` vacío es obligatorio en el HTML.

```javascript
function printView(viewId, orientation) {
  var origTitle = document.title;
  document.title = ' ';

  /* Forzar vista específica */
  document.querySelectorAll('.view').forEach(function(el) { el.classList.remove('active'); });
  document.getElementById(viewId).classList.add('active');

  /* Inyectar orientación + ajustes por modo */
  var style = document.getElementById('print-orientation');
  var css = '@media print { @page { size: letter ' + orientation + '; margin: 6mm 8mm; }';

  if (orientation === 'landscape') {
    css += ' table.ct { font-size: 11px; }';
    css += ' table.ct thead th { font-size: 9px; padding: 8px 10px; }';
    css += ' table.ct tbody td { padding: 7px 10px; }';
    css += ' .tri .card-b { font-size: 11px; }';
    css += ' .tri .card-b .sr { padding: 5px 0; }';
  }
  css += ' }';
  style.textContent = css;

  setTimeout(function() {
    window.print();
    document.title = origTitle;
  }, 100);
}
```

Schemas individuales envuelven esta función con alias semánticos. Ejemplo en proformas:
```javascript
function printMLV(orientation) { printView('v-marluvas', orientation); }
```

Nota single-view: si el output es single-view (sin clases `.view`), usar `window.print()` directo con orientación inyectada vía `<style id="print-orientation">`. printView aplica solo a outputs multi-view.

Nota restore: después de imprimir, la vista queda en la forzada. El usuario puede cambiar manualmente vía tabs. Restauración automática es opcional por schema.

---

## D. Botones de impresión — Formato estándar

Todo output imprimible DEBE ofrecer al menos 2 opciones:

```html
<div class="actions print-actions">
  <button class="btn btn-p" onclick="printView('v-ID', 'portrait')">🖨 Imprimir Carta Vertical</button>
  <button class="btn btn-o" onclick="printView('v-ID', 'landscape')">🖨 Imprimir Carta Horizontal</button>
</div>
```

Los botones se auto-ocultan al imprimir (B2).

---

## E. Validación

Un output HTML imprimible cumple POL_PRINT si:

| # | Check | Criterio |
|---|-------|----------|
| P1 | CSS @media print presente | Las 13 reglas de §B están en el `<style>` |
| P2 | `<style id="print-orientation">` existe | Tag vacío presente en HTML |
| P3 | Función printView (o alias) existe | JS incluye orientación dinámica |
| P4 | Botones portrait + landscape presentes | Ambas opciones disponibles |
| P5 | Elementos interactivos se ocultan | topbar, actions, badges no imprimen |
| P6 | Colores forzados | `-webkit-print-color-adjust:exact` activo |
| P7 | break-inside:avoid | Cards, tablas, pills no se cortan |

Output que falle cualquier check = no cumple POL_PRINT = no puede entregarse como imprimible.

---

## F. Extensiones por schema

Schemas individuales pueden agregar reglas CSS adicionales al bloque @media print para ocultar secciones específicas de su dominio. Las extensiones se insertan DENTRO del mismo bloque `@media print`, inmediatamente después de B2. No son un bloque @media print separado. Ejemplo:

- SCH_PROFORMA_MWT agrega: `.bg-draft,.bg-ceo{display:none!important;}`, `.arb{display:none!important;}`, `.bg-mlv{display:none!important;}`
- Futuro SCH_FACTURA_MWT podría agregar reglas propias

Las extensiones se declaran en el §J (UI hints) de cada schema y se suman al bloque canónico. Nunca reemplazan ni contradicen las 13 reglas base.

---

Stamp: DRAFT — Pendiente aprobación CEO
