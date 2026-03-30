# GUÍA ALEJANDRO — Sprint 19: Frontend Expedientes + Tallas + Pricing
## Para: Alejandro (AG-02 Frontend) · Fecha: 2026-03-27

---

## Qué es este sprint

Sprint 19 es 100% frontend. Todo lo que Sprint 18 construyó en backend (endpoints PATCH por estado, FactoryOrder CRUD, pagos, merge/split, motor de tallas) ahora se conecta con la UI.

Hay 3 cosas grandes:

**A) Formulario de creación extendido.** El formulario `/expedientes/nuevo` actual es básico. Ahora le agregamos: número de orden de compra, selector operado_por (quién opera el expediente: el cliente o MWT), y una tabla dinámica de líneas de producto donde cada fila tiene un producto, una talla (BrandSKU) y un precio que se pre-llena automáticamente.

**B) Vista detalle con edición inline por estado.** Cuando hacés click en un estado del timeline, se abre una sección con los campos de ese estado. Podés editar ahí mismo y guarda con PATCH. Cada estado tiene su endpoint dedicado (tabla canónica en el LOTE). Además: tabla de factory orders con CRUD completo, modales de merge y split, y registro/confirmación de pagos.

**C) Limpieza visual.** Barrido de todos los colores hardcodeados en el código (hex, rgb, rgba) y reemplazo por CSS variables del design system.

---

## Prerequisito

Sprint 18 DONE. Antes de empezar, corré el gate completo (21 checks en el PROMPT_ANTIGRAVITY_SPRINT19). Si algo falla → no arrancar, avisame.

```bash
python manage.py test
cd frontend && npm run lint && npm run typecheck
```

Si eso pasa, corré los curls del gate para verificar que los endpoints existen.

---

## Orden de ejecución (4 fases, no mezclar)

### Fase 1 — Formulario creación (hacer primero)

| # | Qué | Tiempo | Notas |
|---|-----|--------|-------|
| 1.1 | Componente `<UrlField />` | 1h | Componente reutilizable para URLs de documentos. Tiene 3 estados: si hay URL muestra link+editar+eliminar, si no hay URL muestra input para pegar una, y si hay endpoint de upload muestra botón subir. Incluye botón "¿Link no funciona?" con instrucción para el usuario. Lo vas a usar en toda la vista detalle. |
| 1.2 | Formulario `/expedientes/nuevo` | 2-3h | 3 campos nuevos: `purchase_order_number` (texto, opcional), `operado_por` (select CLIENTE/MWT, default null), y la tabla de product_lines. La tabla es lo más complejo: autocomplete de ProductMaster (`GET /api/catalog/product-masters/?search={q}`), select de BrandSKU filtrado (`GET /api/catalog/brand-skus/?product_master={id}`), y pre-fill de precio (`GET /api/pricing/resolve/?brand_sku_id={id}&client_id={client_id}`). Si no hay BrandSKUs para un producto, mostrá nota "Sin tallas — configurar en Brand Console > Tallas". |

**Gate Fase 1:** formulario envía datos correctamente + backward compat (POST sin product_lines sigue funcionando).

### Fase 2 — Vista detalle por estado

| # | Qué | Tiempo | Notas |
|---|-----|--------|-------|
| 2.1 | Secciones por estado | 3-4h | Esta es la pieza central. Click en un estado del timeline → sección con campos editables. Cada estado usa su endpoint PATCH de la tabla canónica (está en el LOTE y en el prompt). Estados sin PATCH (PI_SOLICITADA, EN_DESTINO, CERRADO, CANCELADO) son solo lectura. Usá UrlField para todos los campos url_*. |
| 2.2 | operado_por condicional | 1.5h | **Importante:** creá un helper/hook centralizado. Si operado_por=CLIENTE, mostrá campos `*_client`. Si MWT, mostrá `*_mwt`. Si null, mostrá banner "Seleccionar operador". Nunca mostrés ambos conjuntos. Aplica en PRODUCCION, PREPARACION y DESPACHO. En DESPACHO específicamente: shipping_date, tracking_url, dispatch_notes, weight_kg, packages_count son campos del expediente directo. url_packing_list y url_bl viven dentro de factory_orders y son condicionales por operado_por. |
| 2.3 | Tabla FactoryOrder | 2h | CRUD completo en PRODUCCION. GET list, POST crear, PATCH editar, DELETE eliminar (con confirmación). URLs de documentos con UrlField condicional por operado_por. Label de columna "Fabricante", no "SAP". |

**Gate Fase 2:** edición inline funciona en todos los estados con PATCH + operado_por muestra campos correctos.

### Fase 3 — Modales

| # | Qué | Tiempo | Notas |
|---|-----|--------|-------|
| 3.1 | Modal merge | 1.5h | 2 pasos. Paso 1: buscar expediente con `GET /api/expedientes/?search={ref}&brand={brand_id}&client={client_id}&status__in=REGISTRO,PI_SOLICITADA,CONFIRMADO`. Paso 2: selector de quién es el master. POST `/api/expedientes/{id}/merge/` con `{ target_expediente_id, master_id }`. Después de merge: recargar detalle + debería aparecer banner de merged. |
| 3.2 | Modal split | 1.5h | Checkboxes sobre product_lines. Mínimo 1, máximo N-1 (no podés sacar todas). Opción crear nuevo o mover a existente (misma búsqueda del merge). POST `/api/expedientes/{id}/separate-products/`. |
| 3.3 | Pagos | 2h | Visible desde DESPACHO en adelante. Lista de pagos con status. Modal para registrar (POST `/api/expedientes/{id}/pagos/` → PENDING). Botón confirmar (PATCH `/api/expedientes/{id}/pagos/{pago_id}/confirmar/` → CONFIRMED). Después de cada acción: refrescar lista + CreditBar + credit_released. |

**Gate Fase 3:** merge crea banner, split mueve líneas, pago confirma y refresca crédito.

### Fase 4 — Visual + opcionales

| # | Qué | Tiempo | Notas |
|---|-----|--------|-------|
| 4.1 | Barrido hex→CSS variables | 1-2h | **OBLIGATORIO.** Corré desde `frontend/`: `grep -rn --include='*.tsx' --include='*.ts' --include='*.css' -E '#[0-9a-fA-F]{3,8}\b' src/` y `grep -rn --include='*.tsx' --include='*.ts' --include='*.css' -E 'rgba?\(' src/`. Todo lo que salga (que no sea SVG) hay que reemplazar por `var(--color-*)` del design system. |
| 4.2 | Tab Tallas (DESEABLE) | 2h | Solo si los checks de sizing del gate pasaron (8-10 + 19-20). Tab en Brand Console que lista assignments y permite crear/editar entries. Si no pasaron → SKIP. |
| 4.3 | Tooltip pricing (DESEABLE) | 1h | Hover sobre precio muestra tooltip con price+source. Si el backend devuelve desglose (cost/margin) → mostrarlo. Si no → solo nivel 1. Verificar shape del response antes de implementar nivel 2. |
| 4.4 | Recharts (DESEABLE) | 5 min | `npm install recharts && npm run build`. Solo instalar, no implementar gráficos. |

---

## Cosas que pueden fallar y qué hacer

| Problema | Qué hacer |
|----------|-----------|
| Endpoint retorna 404/500 | STOP. Sprint 18 no está completo. Avisame. |
| ProductMaster search no retorna resultados | Verificar que hay datos en la DB. Si no hay → seed primero. |
| BrandSKU vacío para un producto | Es válido — mostrá nota "Sin tallas". |
| pricing/resolve retorna 404 | Pre-fill no disponible. Dejar campo vacío para input manual. No bloquea. |
| Sizing checks fallan | S19-13 (Tab Tallas) se salta entero. No es bloqueante. |
| `original_product_lines` no viene en bundle | S19-10 (diff tablas) se salta. No es bloqueante. |
| Merge retorna error estado inválido | Correcto — solo funciona en REGISTRO/PI_SOLICITADA/CONFIRMADO. Mostrá error al usuario. |

---

## Tiempo estimado total

- Obligatorio (Fases 1-4.1): ~16-19 horas
- Deseables (4.2-4.4): ~3 horas adicionales
- Total con deseables: ~19-22 horas

---

## Checklist final antes de avisar que terminaste

```bash
cd frontend
npm run lint      # 0 errores
npm run typecheck # 0 errores
npm run build     # build exitoso

# Barrido colores — ambos deben dar 0 (excluyendo SVG)
grep -rn --include='*.tsx' --include='*.ts' --include='*.css' \
  -E '#[0-9a-fA-F]{3,8}\b' src/ | grep -v '.svg'
grep -rn --include='*.tsx' --include='*.ts' --include='*.css' \
  -E 'rgba?\(' src/ | grep -v '.svg'
```

Si todo pasa → avisame y revisamos juntos.

---

Stamp: Efímero — 2026-03-27
