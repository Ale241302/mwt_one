# PROMPT_ANTIGRAVITY_SPRINT19 — Frontend Expedientes + Tallas + Pricing Visual
## Para: Claude Code (Antigravity) — AG-02 Frontend
## Sprint: 19 · Fecha: 2026-03-27 · LOTE: v1.4 (aprobado 9.7/10, 5 rondas ChatGPT)

---

## TU ROL

Eres AG-02 Frontend Builder para el proyecto MWT.ONE.
Implementas los items de Sprint 19 en código Next.js/React/TypeScript.
El CEO (Alejandro) te da contexto y aprueba. Vos escribís código, no tomás decisiones de negocio.

Sprint 19 es 100% frontend. Consume endpoints creados en Sprint 18. NO crear ni modificar backend — si algo no existe, STOP y avisar.

---

## CONTEXTO DEL PROYECTO

- **Stack:** Next.js 14 (App Router) + TypeScript + Tailwind CSS + react-hook-form + CSS variables (design tokens)
- **Repo:** `Ale241302/mwt_one`, branch `main`, directorio `frontend/`
- **Objetivo:** Frontend completo de expedientes: formulario creación extendido, vista detalle por estado con edición inline, modales merge/split, pagos, y opcionalmente tab tallas en Brand Console.
- **Prerequisito:** Sprint 18 DONE (todos los endpoints backend funcionales).

### State machine FROZEN (inmutable — NO inventar estados):
REGISTRO → PI_SOLICITADA → CONFIRMADO → PRODUCCION → PREPARACION → DESPACHO → TRANSITO → EN_DESTINO → CERRADO. También CANCELADO (terminal).

---

## HARD RULES — NUNCA VIOLAR

1. **State machine es FROZEN.** Los estados y transiciones vienen de ENT_OPS_STATE_MACHINE v1.2.2. No inventar estados ni transiciones.

2. **No inventar datos.** Si necesitas un valor de negocio, preguntá al CEO. Marcar como `// TODO: CEO_INPUT_REQUIRED`.

3. **No modificar backend.** Si un endpoint no existe o retorna error, STOP. Documentar y avisar.

4. **0 colores hardcodeados.** Todo color usa CSS variables de design tokens. Nunca `#XXXXXX`, `rgb()`, `rgba()` directo en código. Solo `var(--color-*)`.

5. **Tabla canónica es la referencia.** Cada estado tiene su endpoint PATCH definido en la tabla canónica del LOTE. No adivinar endpoints.

6. **Conventional Commits.** `feat:`, `fix:`, `refactor:`, `test:`.

7. **operado_por nunca muestra ambos conjuntos.** CLIENTE → campos `*_client`. MWT → campos `*_mwt`. null → banner. Lógica en un helper centralizado.

8. **Merge solo en REGISTRO/PI_SOLICITADA/CONFIRMADO.** Estado machine FROZEN. No permitir merge en otros estados.

9. **credit_released es read-only en frontend.** Lo recalcula el backend. Frontend solo muestra y refresca.

10. **Signed URLs son efímeras.** No cachear URLs de documentos. Pedirlas fresh cada vez.

---

## ANTES DE ESCRIBIR UNA SOLA LÍNEA — GATE OBLIGATORIO

Correr el gate completo de S19-00 (21 checks). Si alguno de los checks 1-7, 11, 13, 14-18, 21 falla → STOP.

```bash
export TOKEN="tu-jwt-token"

# Tests backend
python manage.py test

# PATCH genérico REGISTRO
curl -s -o /dev/null -w "registro: %{http_code}\n" -X PATCH \
  http://localhost:8000/api/expedientes/1/ \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" -d '{}'

# PATCH por estado dedicados
for STATE in confirmado produccion preparacion despacho transito; do
  CODE=$(curl -s -o /dev/null -w "%{http_code}" -X PATCH \
    http://localhost:8000/api/expedientes/1/${STATE}/ \
    -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" -d '{}')
  echo "${STATE}: ${CODE}"  # 200 o 409, NO 404/500
done

# FactoryOrder + Pagos list
curl -s -o /dev/null -w "factory-orders-list: %{http_code}\n" \
  http://localhost:8000/api/expedientes/1/factory-orders/ -H "Authorization: Bearer $TOKEN"
curl -s -o /dev/null -w "pagos-list: %{http_code}\n" \
  http://localhost:8000/api/expedientes/1/pagos/ -H "Authorization: Bearer $TOKEN"

# Merge con payload completo
curl -s -o /dev/null -w "merge: %{http_code}\n" -X POST \
  http://localhost:8000/api/expedientes/1/merge/ \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"target_expediente_id": 999, "master_id": 1}'

# Bundle validación estructural
curl -s http://localhost:8000/api/expedientes/1/ -H "Authorization: Bearer $TOKEN" \
  | python3 -c "
import sys, json
data = json.load(sys.stdin)
required = ['product_lines', 'factory_orders', 'pagos', 'credit_released']
missing = [k for k in required if k not in data]
if missing:
    print(f'FAIL — missing keys: {missing}')
    sys.exit(1)
print('OK — all 4 keys present')
"

# BrandSKU + ProductMaster
curl -s -o /dev/null -w "brand-skus: %{http_code}\n" \
  http://localhost:8000/api/catalog/brand-skus/ -H "Authorization: Bearer $TOKEN"
curl -s -o /dev/null -w "product-masters-search: %{http_code}\n" \
  "http://localhost:8000/api/catalog/product-masters/?search=test" -H "Authorization: Bearer $TOKEN"

# Búsqueda contrato completo
curl -s -o /dev/null -w "search-full: %{http_code}\n" \
  "http://localhost:8000/api/expedientes/?search=EXP&brand=1&client=1&status__in=REGISTRO,PI_SOLICITADA,CONFIRMADO" \
  -H "Authorization: Bearer $TOKEN"

# Frontend limpio
cd frontend && npm run lint && npm run typecheck

# Write-paths
curl -s -o /dev/null -w "factory-order-create: %{http_code}\n" -X POST \
  http://localhost:8000/api/expedientes/1/factory-orders/ \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"supplier_name": "test-gate"}'

curl -s -o /dev/null -w "separate-products: %{http_code}\n" -X POST \
  http://localhost:8000/api/expedientes/1/separate-products/ \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"product_line_ids": [999]}'
```

Si todo pasa → empezar. Si sizing checks (8-10, 19-20) fallan → S19-13 es SKIP.

---

## TABLA CANÓNICA — REFERENCIA ÚNICA DE ENDPOINTS

| Estado | Endpoint PATCH | Campos | Nota |
|--------|----------------|--------|------|
| REGISTRO | `/api/expedientes/{id}/` | ref_number, purchase_order_number, client, operado_por, credit_days, credit_limit, order_value, url_orden_compra | PATCH genérico viewset |
| PI_SOLICITADA | — | — | Solo lectura |
| CONFIRMADO | `/api/expedientes/{id}/confirmado/` | product_lines, currency, incoterms, notes | operado_por required |
| PRODUCCION | `/api/expedientes/{id}/produccion/` | factory_orders (nested), production_status, quality_notes | Campos `*_client`/`*_mwt` dentro de factory_orders |
| PREPARACION | `/api/expedientes/{id}/preparacion/` | product_lines (modified), estimated_production_date | Docs URLs en factory_orders nested |
| DESPACHO | `/api/expedientes/{id}/despacho/` | shipping_date, tracking_url, dispatch_notes, weight_kg, packages_count | Campos expediente directos. url_packing_list/url_bl en factory_orders (condicional operado_por) |
| TRANSITO | `/api/expedientes/{id}/transito/` | intermediate_airport_or_port, transit_arrival_date, url_packing_list_detallado | tracking_url read-only (carry-forward) |
| EN_DESTINO | — | — | Solo lectura |
| CERRADO | — | — | Terminal |
| CANCELADO | — | — | Terminal |

---

## ORDEN DE EJECUCIÓN (4 fases, secuencial)

### Fase 1 — Formulario creación (S19-01 + S19-02)

| # | Qué | Tiempo | Notas |
|---|-----|--------|-------|
| 1.1 | Componente `<UrlField />` | 1h | Componente reutilizable. 3 estados: link, upload, inline. Botón "¿Link no funciona?" |
| 1.2 | Formulario `/expedientes/nuevo` extendido | 2-3h | +purchase_order_number, +operado_por select, +tabla dinámica product_lines. ProductMaster autocomplete: `GET /api/catalog/product-masters/?search={q}`. BrandSKU filtrado: `GET /api/catalog/brand-skus/?product_master={id}`. Pre-fill precio: `GET /api/pricing/resolve/?brand_sku_id={id}&client_id={client_id}`. |

### Fase 2 — Vista detalle (S19-03 a S19-05)

| # | Qué | Tiempo | Notas |
|---|-----|--------|-------|
| 2.1 | Secciones por estado con edición inline | 3-4h | Click timeline → sección → PATCH endpoint de tabla canónica. UrlField en todos los url_*. |
| 2.2 | operado_por condicional | 1.5h | Helper/hook centralizado. CLIENTE→`*_client`, MWT→`*_mwt`, null→banner. PRODUCCION/PREPARACION/DESPACHO. |
| 2.3 | Tabla FactoryOrder PRODUCCION | 2h | CRUD completo: GET list, POST create, PATCH update, DELETE con confirmación. UrlField condicional operado_por. Label "Fabricante". |

### Fase 3 — Modales (S19-06 a S19-08)

Endpoint búsqueda compartido: `GET /api/expedientes/?search={ref}&brand={brand_id}&client={client_id}&status__in=REGISTRO,PI_SOLICITADA,CONFIRMADO`

| # | Qué | Tiempo | Notas |
|---|-----|--------|-------|
| 3.1 | Modal merge | 1.5h | 2 pasos: buscar + selector master. POST `/merge/` con `{ target_expediente_id, master_id }`. Solo REGISTRO/PI_SOLICITADA/CONFIRMADO. |
| 3.2 | Modal split | 1.5h | Checkboxes product_lines (min 1, max N-1). POST `/separate-products/`. |
| 3.3 | Pagos | 2h | Visible desde DESPACHO. POST `/pagos/` → PENDING. PATCH `/pagos/{id}/confirmar/` → CONFIRMED. Refresh CreditBar + credit_released. |

### Fase 4 — Visual + Brand Console (S19-12 + deseables)

| # | Qué | Tiempo | Notas |
|---|-----|--------|-------|
| 4.1 | Barrido hex→CSS variables | 1-2h | OBLIGATORIO. grep hex 3/6/8 dígitos + rgb/rgba desde `frontend/src/`. Reemplazar todo por `var(--color-*)`. |
| 4.2 | Tab Tallas Brand Console | 2h | DESEABLE — solo si gate sizing checks pasaron. GET assignments + entries, POST/PATCH. |
| 4.3 | Tooltip pricing | 1h | DESEABLE. Nivel 1 seguro (price+source), nivel 2 si backend lo expone. |
| 4.4 | Instalar Recharts | 5 min | `npm install recharts && npm run build`. Solo instalar. |

---

## CRITERIO DONE — CHECKLIST FINAL

### Obligatorio (bloquea Sprint 20)
- [ ] Formulario /nuevo con purchase_order, operado_por, product_lines+BrandSKU
- [ ] UrlField reutilizable (3 estados + degradado graceful)
- [ ] Detalle por estado con PATCH inline (tabla canónica)
- [ ] operado_por condicional (helper centralizado)
- [ ] FactoryOrder CRUD completo
- [ ] Modal merge (estados FROZEN)
- [ ] Modal split (validación min/max)
- [ ] Pagos registro + confirmación + refresh crédito
- [ ] 0 hex hardcodeados
- [ ] `npm run lint && npm run typecheck && npm run build` verde

### Deseable
- [ ] Tab Tallas Brand Console (si sizing checks pasan)
- [ ] Selector tallas enriquecido "{system} — {entry.code}"
- [ ] Tooltip pricing
- [ ] Banner merged
- [ ] tracking_url clicable
- [ ] Recharts instalado

---

Stamp: Efímero — 2026-03-27
