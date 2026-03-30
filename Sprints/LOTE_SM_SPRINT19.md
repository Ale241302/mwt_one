# LOTE_SM_SPRINT19 — Frontend Expedientes + Tallas + Pricing Visual
id: LOTE_SM_SPRINT19
version: 1.4
visibility: [INTERNAL]
domain: Plataforma (IDX_PLATAFORMA)
status: DRAFT — Pendiente aprobación CEO
stamp: DRAFT v1.4 — 2026-03-27
tipo: Lote ruteado (ref → PLB_ORCHESTRATOR §E)
sprint: 19
priority: P0
depends_on: LOTE_SM_SPRINT18 (DONE v4.0 — PRs #45 + #46)
refs: ENT_OPS_STATE_MACHINE (FROZEN v1.2.2), ROADMAP_SPRINTS_17_27 (Sprint 19),
      ROADMAP_CONVERGENCIA_MWTONE (Sprint 19 expandido),
      PROMPT_ANTIGRAVITY_EXPEDIENTES_EXTENDED (Fase 3),
      AGENT_C_UX_FRONTEND (hallazgos tallas UI, pricing tooltip, Recharts),
      ENT_PLAT_DESIGN_TOKENS (tokens CSS), ENT_PLAT_SEGURIDAD,
      ENT_COMERCIAL_PRICING (SSOT pricing), ENT_OPS_TALLAS (SSOT tallas RW),
      ENT_GOB_DECISIONES (DEC-EXP-01 a DEC-EXP-05, DEC-SIZE-01)

changelog:
  - v1.0 (2026-03-27): Compilación inicial desde ROADMAP_CONVERGENCIA Sprint 19 (16 items) + PROMPT_ANTIGRAVITY_EXPEDIENTES_EXTENDED Fase 3.
  - v1.1 (2026-03-27): Fixes auditoría R1 (ChatGPT 8.7/10 — 8 hallazgos). H1: Tabla canónica estado→endpoint unificada, CONFIRMADO con PATCH real (alineado S18), gate corregido. H2: Merge estados literales FROZEN (REGISTRO/PI_SOLICITADA/CONFIRMADO). H3: REGISTRO editable via PATCH genérico viewset. H4: S19-10 movido a Deseable condicionado a snapshot backend. H5: Gate expandido con checks sizing assignments/entries. H6: UrlField degradado graceful sin endpoint regenerar. H7: S19-15 tooltip formato mínimo + desglose condicional. H8: Merge/Split endpoint búsqueda explícito.
  - v1.2 (2026-03-27): Fixes auditoría R2 (ChatGPT 9.2/10 — 5 hallazgos). R2-H1: Gate expandido con write-paths críticos (POST/PATCH/DELETE factory-orders, confirmar pagos, separate-products). R2-H2: Tabla canónica notas ampliadas — campos condicionales nested (factory_orders, docs URLs) explícitos en PRODUCCION/PREPARACION/DESPACHO. R2-H3: Gate checks 19-20 para sizing write-paths (POST assignments, PATCH entries); si fallan, S19-13 completo baja a Deseable. R2-H4: Check 12 búsqueda reescrito con contrato real (search+brand+client+status__in). R2-H5: Tab Tallas movido de Obligatorio a Deseable condicionado.
  - v1.3 (2026-03-27): Fixes auditoría R3 (ChatGPT 9.3/10 — 5 hallazgos). R3-H1: Gate check 6 merge reescrito con payload completo (target_expediente_id + master_id). R3-H2: Gate check 7 bundle reescrito con jq/python has() estructural. R3-H3: DONE criteria binarios restaurados en todos los items (S19-06 a S19-16). R3-H4: Dependencia formal agregada en S19-09 a S19-16. R3-H5 + R2-H2 residual: DESPACHO mapping congelado — campos a nivel expediente vs factory_order explícitos.
  - v1.4 (2026-03-27): Fixes auditoría R4 (ChatGPT 9.4/10 — 3 hallazgos). R4-H1: Endpoint ProductMaster autocomplete explícito (GET /api/catalog/product-masters/?search={q}) + gate check 21. R4-H2: S19-12 grep ampliado a hex 3/6/8 dígitos + rgba() + path fijado con cd frontend. R4-H3: S19-10 cerrado — solo implementar si original_product_lines viene en bundle; sin alternativa history endpoint.

---

## Tabla canónica: estado → endpoint → método → campos

Referencia única para S19-00 (gate), S19-03 (detalle) y criterio DONE. Alineada con S18 LOTE v3.5 y state machine FROZEN v1.2.2.

| Estado FROZEN | Endpoint PATCH | Campos editables | Nota |
|---------------|----------------|------------------|------|
| REGISTRO | PATCH `/api/expedientes/{id}/` (viewset estándar) | ref_number, purchase_order_number, client, operado_por, credit_days, credit_limit, order_value, url_orden_compra | Usa PATCH genérico del viewset |
| PI_SOLICITADA | — (sin PATCH) | — | Proforma se gestiona como artefacto (ART-02) |
| CONFIRMADO | PATCH `/api/expedientes/{id}/confirmado/` | product_lines, currency, incoterms, notes | operado_por required |
| PRODUCCION | PATCH `/api/expedientes/{id}/produccion/` | factory_orders (nested), production_status, quality_notes | Campos condicionales por operado_por viven **dentro del objeto nested `factory_orders`**: campos `*_client` (url_proforma_client, url_orden_compra_client) si CLIENTE, campos `*_mwt` (url_proforma_mwt, tracking_fabrica) si MWT. UI lee operado_por del expediente padre para decidir qué campos mostrar. |
| PREPARACION | PATCH `/api/expedientes/{id}/preparacion/` | product_lines (modified), estimated_production_date | product_lines aquí son las **modificadas** post-producción. Si existe snapshot (`original_product_lines`), S19-10 muestra diff. Docs URLs siguen patrón nested de PRODUCCION dentro de factory_orders. |
| DESPACHO | PATCH `/api/expedientes/{id}/despacho/` | shipping_date, tracking_url, dispatch_notes, weight_kg, packages_count | **Mapping congelado:** `shipping_date`, `tracking_url`, `dispatch_notes`, `weight_kg`, `packages_count` → campos a **nivel expediente** (PATCH directo). `url_packing_list`, `url_bl` → campos a **nivel factory_order** (nested, condicional operado_por: `*_client` si CLIENTE, `*_mwt` si MWT). UI: sección superior con campos expediente + tabla FOs abajo con docs condicionales. |
| TRANSITO | PATCH `/api/expedientes/{id}/transito/` | intermediate_airport_or_port, transit_arrival_date, url_packing_list_detallado | tracking_url carry-forward desde DESPACHO (read-only aquí). |
| EN_DESTINO | — (sin PATCH en S18) | — | Cierre vía command |
| CERRADO | — | — | Terminal, inmutable |
| CANCELADO | — | — | Terminal, inmutable |

---

## FASE 0 — Gate de prerequisitos

### S19-00: Verificación Sprint 18 DONE

```bash
# ── Lectura / existencia ──

# 1. Tests backend verdes
python manage.py test

# 2. PATCH genérico REGISTRO
curl -s -o /dev/null -w "registro: %{http_code}\n" -X PATCH \
  http://localhost:8000/api/expedientes/1/ \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" -d '{}'

# 3. PATCH por estado dedicados (5)
for STATE in confirmado produccion preparacion despacho transito; do
  CODE=$(curl -s -o /dev/null -w "%{http_code}" -X PATCH \
    http://localhost:8000/api/expedientes/1/${STATE}/ \
    -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" -d '{}')
  echo "${STATE}: ${CODE}"  # 200 o 409, NO 404/500
done

# 4-5. FactoryOrder list + Pagos list
curl -s -o /dev/null -w "factory-orders-list: %{http_code}\n" \
  http://localhost:8000/api/expedientes/1/factory-orders/ -H "Authorization: Bearer $TOKEN"
curl -s -o /dev/null -w "pagos-list: %{http_code}\n" \
  http://localhost:8000/api/expedientes/1/pagos/ -H "Authorization: Bearer $TOKEN"

# 6. Merge con payload completo
curl -s -o /dev/null -w "merge: %{http_code}\n" -X POST \
  http://localhost:8000/api/expedientes/1/merge/ \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"target_expediente_id": 999, "master_id": 1}'
# Esperado: 200/400/404 (validación o no encontrado), NO 405/500

# 7. Bundle detalle — validación estructural
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

# 8-9. Motor dimensional + assignments (lectura)
curl -s -o /dev/null -w "sizing-systems: %{http_code}\n" \
  http://localhost:8000/api/sizing/systems/ -H "Authorization: Bearer $TOKEN"
curl -s -o /dev/null -w "sizing-assignments-get: %{http_code}\n" \
  http://localhost:8000/api/sizing/assignments/?brand=1 -H "Authorization: Bearer $TOKEN"

# 10. Entries de un sistema (lectura)
curl -s -o /dev/null -w "sizing-entries-get: %{http_code}\n" \
  http://localhost:8000/api/sizing/systems/1/entries/ -H "Authorization: Bearer $TOKEN"

# 11. BrandSKU
curl -s -o /dev/null -w "brand-skus: %{http_code}\n" \
  http://localhost:8000/api/catalog/brand-skus/ -H "Authorization: Bearer $TOKEN"

# 12. Búsqueda expedientes — contrato real usado por modales merge/split
curl -s -o /dev/null -w "search-full: %{http_code}\n" \
  "http://localhost:8000/api/expedientes/?search=EXP&brand=1&client=1&status__in=REGISTRO,PI_SOLICITADA,CONFIRMADO" \
  -H "Authorization: Bearer $TOKEN"

# 13. Frontend limpio
cd frontend && npm run lint && npm run typecheck

# ── Write-paths críticos ──

# 14. POST FactoryOrder
curl -s -o /dev/null -w "factory-order-create: %{http_code}\n" -X POST \
  http://localhost:8000/api/expedientes/1/factory-orders/ \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"supplier_name": "test-gate"}'
# Esperado: 201 o 400 (validación), NO 404/405/500

# 15. PATCH FactoryOrder
curl -s -o /dev/null -w "factory-order-update: %{http_code}\n" -X PATCH \
  http://localhost:8000/api/expedientes/1/factory-orders/1/ \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"supplier_name": "test-gate-updated"}'
# Esperado: 200 o 404 (si ID 1 no existe), NO 405/500

# 16. DELETE FactoryOrder
curl -s -o /dev/null -w "factory-order-delete: %{http_code}\n" -X DELETE \
  http://localhost:8000/api/expedientes/1/factory-orders/1/ \
  -H "Authorization: Bearer $TOKEN"
# Esperado: 204 o 404, NO 405/500

# 17. PATCH confirmar pago
curl -s -o /dev/null -w "pago-confirmar: %{http_code}\n" -X PATCH \
  http://localhost:8000/api/expedientes/1/pagos/1/confirmar/ \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" -d '{}'
# Esperado: 200 o 404, NO 405/500

# 18. POST separate-products
curl -s -o /dev/null -w "separate-products: %{http_code}\n" -X POST \
  http://localhost:8000/api/expedientes/1/separate-products/ \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"product_line_ids": [999]}'
# Esperado: 200/400, NO 404/405/500

# ── Sizing write-paths ──

# 19. POST sizing assignment
curl -s -o /dev/null -w "sizing-assignment-create: %{http_code}\n" -X POST \
  http://localhost:8000/api/sizing/assignments/ \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"brand": 1, "sizing_system": 1}'
# Esperado: 201 o 400 (duplicado/validación), NO 404/405/500

# 20. PATCH sizing entry
curl -s -o /dev/null -w "sizing-entry-update: %{http_code}\n" -X PATCH \
  http://localhost:8000/api/sizing/systems/1/entries/1/ \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"code": "test-gate"}'
# Esperado: 200 o 404, NO 405/500

# ── Catálogo ──

# 21. ProductMaster autocomplete
curl -s -o /dev/null -w "product-masters-search: %{http_code}\n" \
  "http://localhost:8000/api/catalog/product-masters/?search=test" \
  -H "Authorization: Bearer $TOKEN"
# Esperado: 200, NO 404/500
```

**Decisiones del gate:**
- Checks 1-7, 11, 13 fallan → STOP. Resolver en S18 primero.
- Check 21 falla (ProductMaster search) → STOP. S19-01 no puede funcionar sin autocomplete. Agregar SearchFilter al viewset ProductMaster.
- Checks 14-18 fallan → STOP. Write-paths son prerequisito para CRUD frontend (S19-05, S19-06, S19-07, S19-08). Resolver en S18.
- Checks 8-10 fallan (sizing read) → S19-13 y S19-14 bajan a Deseable. Continuar.
- Checks 19-20 fallan (sizing write) → S19-13 completo baja a Deseable (read-only tab sin edición no tiene valor). S19-14 no se afecta (solo lectura).
- Check 12 falla → agregar SearchFilter + filtros brand/client/status__in al viewset antes de modales.

---

## FASE 1 — Formulario de creación extendido

### S19-01: Formulario `/expedientes/nuevo`

**Dependencia:** S19-00 DONE

3 adiciones al formulario actual:

**1. `purchase_order_number`** — Input text, "N° Orden de Compra", opcional.
**2. `operado_por`** — Select CLIENTE | MWT, default null.
**3. Sección "Líneas de producto"** — tabla dinámica:
  - Botón `+ Agregar producto`
  - Cada fila: ProductMaster (autocomplete via `GET /api/catalog/product-masters/?search={q}`) → BrandSKU (select filtrado, muestra talla) → quantity → unit_price
  - `GET /api/catalog/brand-skus/?product_master={id}` para cargar tallas
  - `GET /api/pricing/resolve/?brand_sku_id={id}&client_id={client_id}` para pre-llenar precio
  - Si no hay BrandSKUs → nota "Sin tallas — configurar en Brand Console > Tallas"
  - Enviar como `product_lines: [{ product_master_id, brand_sku_id, quantity, unit_price }]`

**DONE S19-01 cuando:**
- [ ] Formulario envía purchase_order_number y operado_por en POST C1
- [ ] Tabla dinámica agrega/elimina filas
- [ ] Select BrandSKU filtra por ProductMaster y muestra talla
- [ ] unit_price pre-llena si resolve retorna valor
- [ ] POST sin product_lines sigue funcionando (backward compat)
- [ ] 0 hex hardcodeados

---

### S19-02: Componente `<UrlField />`

**Dependencia:** Ninguna

```typescript
interface UrlFieldProps {
  url: string | null;
  label: string;
  onUpdate: (newUrl: string) => void;
  onDelete: () => void;
  uploadEndpoint?: string;
}
```

3 estados: url existe (link+editar+eliminar), null+upload (botón subir), null (input URL inline).

**Links expirados (degradado graceful):** Botón secundario "¿Link no funciona?" → instrucción "Solicitá link nuevo al admin o editá la URL manualmente". No hay endpoint regenerar en S18 (CEO-20/27 pendientes).

**DONE S19-02 cuando:**
- [ ] 3 estados renderizados correctamente
- [ ] Click link abre nueva pestaña
- [ ] Editar/eliminar invocan callbacks
- [ ] Botón "¿Link no funciona?" con instrucción
- [ ] 0 hex hardcodeados

---

## FASE 2 — Vista detalle por estado

### S19-03: Secciones por estado con edición inline

**Dependencia:** S19-02 DONE

Click en estado del timeline → sección con campos. Edición inline → PATCH. **Usar tabla canónica** del inicio del LOTE como referencia única de endpoints y mapping de campos.

Estados sin PATCH (PI_SOLICITADA, EN_DESTINO, CERRADO, CANCELADO): solo lectura, sin botón editar.

**DONE S19-03 cuando:**
- [ ] Click en estado del timeline abre sección con campos correspondientes
- [ ] Edición inline invoca PATCH al endpoint correcto (tabla canónica)
- [ ] Feedback visual post-PATCH (success/error)
- [ ] Estados sin PATCH renderizan en solo lectura, sin botón editar
- [ ] UrlField usado en todos los campos url_*
- [ ] 0 hex hardcodeados

### S19-04: operado_por condicional

**Dependencia:** S19-03 DONE

Helper centralizado, wrapper component. CLIENTE/MWT/null. Aplicar en PRODUCCION, PREPARACION, DESPACHO.

**DONE S19-04 cuando:**
- [ ] CLIENTE → muestra solo campos `*_client`, oculta `*_mwt`
- [ ] MWT → muestra solo campos `*_mwt`, oculta `*_client`
- [ ] null → banner "Seleccionar operador" sin campos condicionales
- [ ] Nunca muestra ambos conjuntos simultáneamente
- [ ] Cambio de operado_por refresca secciones afectadas
- [ ] Lógica centralizada en un helper/hook reutilizable

### S19-05: Tabla FactoryOrder PRODUCCION

**Dependencia:** S19-03 DONE

Tabla con CRUD completo:
- GET `/api/expedientes/{id}/factory-orders/` → listar
- POST `/api/expedientes/{id}/factory-orders/` → crear
- PATCH `/api/expedientes/{id}/factory-orders/{fo_id}/` → editar
- DELETE `/api/expedientes/{id}/factory-orders/{fo_id}/` → eliminar

UrlField condicional operado_por (campos `*_client` si CLIENTE, `*_mwt` si MWT — viven dentro del objeto FactoryOrder). Label "Fabricante" no "SAP".

**DONE S19-05 cuando:**
- [ ] Tabla lista FactoryOrders del expediente
- [ ] Crear FO funciona (POST → nueva fila)
- [ ] Editar FO funciona (PATCH → fila actualizada)
- [ ] Eliminar FO funciona (DELETE → fila removida + confirmación)
- [ ] URLs con UrlField condicional por operado_por
- [ ] Label columna "Fabricante", no "SAP"
- [ ] 0 hex hardcodeados

### S19-09: Banner merged

**Dependencia:** S19-03 DONE

Si `merged_with` no vacío → banner con refs como links, indicando master. Follower muestra nota redirigiendo.

**DONE S19-09 cuando:**
- [ ] Banner visible si `merged_with` no vacío
- [ ] Refs renderizados como links navegables
- [ ] Master identificado visualmente
- [ ] Follower muestra nota "Este expediente fue fusionado → ver master"
- [ ] No renderiza nada si `merged_with` vacío

### S19-10: Tablas originales vs modificadas PREPARACION — **DESEABLE condicionado**

**Dependencia:** S19-03 DONE + `original_product_lines` presente en bundle

Verificar si el bundle del expediente incluye `original_product_lines` como campo del response. **No** buscar endpoint history alternativo — si el campo no viene en el bundle, SKIP automático sin alternativa. Follow-up para sprint posterior si se implementa history.

**DONE S19-10 cuando:**
- [ ] Verificación: `original_product_lines` existe en response del bundle
- [ ] Si existe: tabla "Original" muestra snapshot, tabla "Modificado" muestra actual, diff visual
- [ ] Si no existe: SKIP documentado, no implementar alternativa

### S19-11: tracking_url clicable DESPACHO/TRANSITO

**Dependencia:** S19-03 DONE

Link azul, nueva pestaña, carry-forward de DESPACHO a TRANSITO (read-only en TRANSITO).

**DONE S19-11 cuando:**
- [ ] tracking_url renderizado como link azul clicable
- [ ] Click abre nueva pestaña
- [ ] En DESPACHO: editable (parte del PATCH)
- [ ] En TRANSITO: read-only (carry-forward)

---

## FASE 3 — Modales

**Endpoint búsqueda compartido (S19-06 y S19-07):**
`GET /api/expedientes/?search={ref}&brand={brand_id}&client={client_id}&status__in=REGISTRO,PI_SOLICITADA,CONFIRMADO`

Gate check 12 valida este contrato completo (4 query params). Si falla, resolver filtros antes de implementar modales.

### S19-06: Modal merge (2 pasos)

**Dependencia:** S19-05 DONE

**Estados elegibles: REGISTRO, PI_SOLICITADA, CONFIRMADO** (state machine FROZEN, S18-10).

Paso 1: buscar por ref con endpoint búsqueda compartido. Paso 2: radio selector master. POST `/api/expedientes/{id}/merge/` con `{ target_expediente_id, master_id }`. Post-merge: recargar + banner S19-09.

**DONE S19-06 cuando:**
- [ ] Modal abre desde botón en detalle expediente
- [ ] Búsqueda filtra por endpoint compartido (4 query params)
- [ ] Solo muestra expedientes en estados elegibles (REGISTRO/PI_SOLICITADA/CONFIRMADO)
- [ ] Radio selector master funciona
- [ ] POST merge envía target_expediente_id + master_id
- [ ] Post-merge: recarga detalle + banner merged visible
- [ ] Error handling (expediente no encontrado, estado inválido)

### S19-07: Modal split

**Dependencia:** S19-05 DONE

Checkboxes product_lines, min 1 max N-1. Destino: crear nuevo o mover a existente (mismo endpoint búsqueda). POST `/api/expedientes/{id}/separate-products/`.

**DONE S19-07 cuando:**
- [ ] Modal abre desde botón en detalle expediente
- [ ] Checkboxes sobre product_lines, mínimo 1 seleccionado, máximo N-1
- [ ] Opción "Crear nuevo expediente" o "Mover a existente" (búsqueda con endpoint compartido)
- [ ] POST separate-products envía product_line_ids + destino
- [ ] Post-split: recarga detalle con product_lines actualizadas
- [ ] Error handling (validación min/max, destino inválido)

### S19-08: Pagos

**Dependencia:** S19-03 DONE

Visible desde DESPACHO en adelante. Lista + modal registro + confirmar.
- POST `/api/expedientes/{id}/pagos/` → crea pago con status PENDING
- PATCH `/api/expedientes/{id}/pagos/{pago_id}/confirmar/` → CONFIRMED + recálculo credit_released

Post-acción: refresh lista + CreditBar + credit_released.

**DONE S19-08 cuando:**
- [ ] Sección pagos visible desde estado DESPACHO en adelante
- [ ] Lista muestra pagos existentes con status (PENDING/CONFIRMED)
- [ ] Modal registro crea pago (POST → PENDING)
- [ ] Botón confirmar cambia status (PATCH confirmar/ → CONFIRMED)
- [ ] Post-acción: lista, CreditBar y credit_released se refrescan
- [ ] 0 hex hardcodeados

---

## FASE 4 — Brand Console + Visual

### S19-12: Barrido hex → CSS variables

**Dependencia:** Ninguna (ejecutable en paralelo)

Grep todos los archivos frontend por hex hardcodeados (#XXXXXX, rgb(), rgba()). Reemplazar por CSS variables de ENT_PLAT_DESIGN_TOKENS. Documentar tokens nuevos si se crean.

**DONE S19-12 cuando:**
- [ ] Barrido ejecutado desde `frontend/`:
  ```bash
  cd frontend
  # Hex 3, 6 u 8 dígitos
  grep -rn --include='*.tsx' --include='*.ts' --include='*.css' \
    -E '#[0-9a-fA-F]{3,8}\b' src/ | grep -v '// token' | grep -v '.svg'
  # rgb/rgba
  grep -rn --include='*.tsx' --include='*.ts' --include='*.css' \
    -E 'rgba?\(' src/ | grep -v '// token' | grep -v '.svg'
  ```
- [ ] Ambos greps retornan 0 resultados (excluyendo SVG assets y líneas marcadas `// token`)
- [ ] Todos los reemplazos usan variables de design tokens
- [ ] Tokens nuevos documentados (si aplica)

### S19-13: Tab Tallas Brand Console — **DESEABLE condicionado a S19-00 checks 8-10 (read) + 19-20 (write)**

**Dependencia:** S19-00 checks 8-10 + 19-20 PASS

Endpoints lectura: `GET /api/sizing/assignments/?brand={id}`, `GET /api/sizing/systems/{id}/entries/`.
Endpoints escritura: `POST /api/sizing/assignments/`, `PATCH /api/sizing/systems/{id}/entries/{entry_id}/`.

Si checks 8-10 fallan → SKIP completo (no hay datos).
Si checks 8-10 pasan pero 19-20 fallan → SKIP completo (tab read-only sin edición no aporta valor ejecutable).
Solo implementar si los 5 checks (8, 9, 10, 19, 20) pasan.

**DONE S19-13 cuando:**
- [ ] Tab "Tallas" visible en Brand Console
- [ ] Lista assignments de la marca actual
- [ ] Crear assignment (POST) funciona
- [ ] Editar entries de un sistema (PATCH) funciona
- [ ] Vista entries muestra code + label
- [ ] 0 hex hardcodeados

### S19-14: Selector tallas enriquecido

**Dependencia:** S19-01 DONE + S19-00 checks 8-10 PASS

BrandSKU en formulario y detalle muestra "{system} — {entry.code}" en lugar de ID crudo. Solo lectura, no necesita write-path.

**DONE S19-14 cuando:**
- [ ] Select BrandSKU muestra formato "{system} — {entry.code}"
- [ ] Formato consistente en formulario creación (S19-01) y detalle (S19-03)

### S19-15: Tooltip pricing

**Dependencia:** S19-01 DONE

Nivel 1 (price + source) garantizado — usa response de `/api/pricing/resolve/`. Nivel 2 (desglose cost/margin/markup) solo si backend lo expone en el mismo response. Verificar shape del response antes de implementar nivel 2.

**DONE S19-15 cuando:**
- [ ] Hover sobre unit_price muestra tooltip con precio + source
- [ ] Si response incluye desglose → tooltip nivel 2 con cost/margin
- [ ] Si response no incluye desglose → tooltip nivel 1, sin error
- [ ] No hardcodear campos de nivel 2 — verificar shape dinámicamente

### S19-16: Instalar Recharts

**Dependencia:** Ninguna

`npm install recharts && npm run build`. Solo instalar dependencia, sin implementar gráficos (Sprint 20+).

**DONE S19-16 cuando:**
- [ ] `recharts` en package.json dependencies
- [ ] `npm run build` verde post-instalación

---

## Criterio Sprint 19 DONE

### Obligatorio (bloquea Sprint 20)
1. Formulario /nuevo con purchase_order, operado_por, product_lines+BrandSKU (S19-01)
2. Componente UrlField reutilizable (S19-02)
3. Detalle por estado con PATCH inline — tabla canónica (S19-03)
4. operado_por condicional CLIENTE/MWT/null (S19-04)
5. FactoryOrder tabla con CRUD completo (S19-05)
6. Modal merge con selector master — estados FROZEN (S19-06)
7. Modal split con validación min/max (S19-07)
8. Pagos registro + confirmación + refresh crédito (S19-08)
9. 0 hex hardcodeados — barrido completo (S19-12)
10. lint + typecheck + build verde

### Deseable (no bloquea Sprint 20)
11. Tab Tallas Brand Console — condicionado a gate checks 8-10 + 19-20 (S19-13)
12. Selector tallas enriquecido — condicionado a gate checks 8-10 (S19-14)
13. Tooltip pricing nivel 1/2 según backend (S19-15)
14. Banner merged (S19-09)
15. Tablas originales vs modificadas — condicionado a snapshot backend (S19-10)
16. tracking_url con link clicable (S19-11)
17. Recharts instalado (S19-16)

---

Stamp: DRAFT v1.4 — Arquitecto (Claude Opus 4.6) — 2026-03-27
