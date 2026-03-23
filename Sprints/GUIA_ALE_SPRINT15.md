# GUÍA ALEJANDRO — Sprint 15: Frontend UX Polish
## Para: Alejandro (AG-03 Frontend + AG-02 Backend) · Fecha: 2026-03-23

---

## Qué es este sprint

Sprint 14 transformó la plataforma de hardcoded-Marluvas a parametrizada-por-marca.
Este sprint aprovecha eso: toma las APIs que Sprint 14 entregó y construye las
interfaces que faltaban. 100% frontend, 0 modelos nuevos, 0 migraciones.

La idea central es simple: **la consola tiene que dejar de parecer un prototipo
y empezar a parecer una herramienta real**. El CEO debería poder mirar un expediente
y entender en 5 segundos qué está pasando, cuánto crédito queda, y qué tiene que hacer.

---

## Antes de empezar — el gate (S15-00)

Antes de escribir una sola línea de frontend, AG-02 verifica que S14 está
desplegado y que los endpoints que necesita este sprint responden correctamente.

**AG-02 corre estos checks:**

```bash
# 1. Snapshot comercial en expediente
curl -H "Authorization: Bearer $CEO_TOKEN" /api/expedientes/{id}/ \
  | jq '.snapshot | keys'
# Esperado: fob_unit, margin_pct, commission_pct, landed_cost, credit_policy, agreed_price, dai_amount

# 2. Brand con pricelist + workflow policy
curl -H "Authorization: Bearer $CEO_TOKEN" /api/brands/{id}/ \
  | jq '{pricelist:.pricelist_active.id, policy:.workflow_policy.id}'
# Esperado: ambos no-null

# 3. CreditExposure del cliente
curl -H "Authorization: Bearer $CEO_TOKEN" /api/clientes/{id}/credit-exposure/ \
  | jq '{total,limit}'
# Esperado: ambos presentes

# 4. Portal catalog limpio
curl -H "Authorization: Bearer $CLIENT_TOKEN" /api/portal/catalog/ \
  | jq 'map(keys) | flatten | unique'
# Verificar: NO incluye fob_unit, margin_pct, commission_pct, landed_cost

# Write endpoints (solo verificar que existen — 2xx o 4xx, no 404):
curl -X POST -H "Authorization: Bearer $CEO_TOKEN" \
  /api/brands/{id}/pricelists/ -F "file=@/tmp/test.csv"
curl -X POST -H "Authorization: Bearer $CEO_TOKEN" \
  /api/clientes/{id}/credit-actions/freeze/ -d '{}'
curl -X PATCH -H "Authorization: Bearer $CEO_TOKEN" \
  /api/clientes/{id}/credit-policy/ -d '{"limit":1,"reason":"test"}'
curl -X POST -H "Authorization: Bearer $CLIENT_TOKEN" \
  /api/portal/contacts/ -d '{"name":"t","email":"t@t.com"}'
curl -X PATCH -H "Authorization: Bearer $CLIENT_TOKEN" \
  /api/portal/me/preferences/ -d '{"locale":"es"}'
```

**Si algún write endpoint falla con 404/405:** AG-02 lo implementa antes de
que AG-03 conecte esa feature. AG-03 puede avanzar en otros items mientras tanto.

**AG-02 le manda a AG-03 un mensaje con:** `"GATE S15 OK — {fecha}"` para arrancar.

---

## Qué vas a implementar (en orden)

### P0 — Lo que no puede faltar para declarar el sprint DONE

#### S15-01: Shipment Detail CEO refactor
**Agente:** AG-03 | **Archivo:** `expedientes/[id]/page.tsx`

Este es el item más importante. La pantalla del detalle de expediente tiene que
transmitir el estado completo de una operación de un vistazo.

**4 cosas nuevas en esta pantalla:**

**1. CreditBar** — componente nuevo en `components/ui/CreditBar.tsx`

```typescript
// Contrato completo — implementar exactamente así
interface CreditBarProps {
  limit: number             // límite de crédito USD
  used: number              // open + in_transit + invoiced_unpaid + reserved
  currency?: string         // default 'USD'
  days_elapsed?: number
  days_limit?: number
  size?: 'sm' | 'md' | 'lg'  // default 'md'
  showActions?: boolean       // default false
  viewMode?: 'internal' | 'client'  // default 'internal'
  loading?: boolean
  error?: string | null
  empty?: boolean           // sin CreditPolicy activa
}
```

Rangos de color (usar tokens, no hex):
- 0–70% → `var(--color-success)` verde
- 71–90% → `var(--color-warning)` amarillo
- 91–100% → `var(--color-alert)` naranja
- >100% → `var(--color-danger)` rojo + animación pulse

Si `empty`: mostrar texto "Sin política de crédito", barra gris.
Si `error`: mostrar "— Sin datos de crédito disponibles", barra gris.
Si limit=0 → tratar como `empty`.

Fuente de datos: `expediente.snapshot.credit_policy` + `expediente.snapshot.credit_exposure`

**2. Toggle INTERNA / VISTA CLIENTE**

Visible SOLO si `currentUser.role === 'CEO'`.

Implementación: attribute `data-view-mode` en el contenedor principal.

```tsx
<div data-view-mode={viewMode}>  {/* 'internal' | 'client' */}
  ...
</div>
```

CSS:
```css
[data-view-mode="client"] .ceo-only-field {
  display: none;
}
```

Los campos CEO-ONLY (FOB, margen, comisión, landed cost, DAI) llevan clase
`ceo-only-field`. **No eliminarlos del DOM — solo ocultarlos con CSS**.

Importante: el endpoint `/api/portal/expedientes/{id}/` ya NO devuelve esos
campos en el payload (eso es responsabilidad del backend, no del toggle CSS).
El toggle es solo UX para que el CEO vea ambas perspectivas en la misma pantalla.

**3. Badges de artefactos**

Cada artefacto tiene un badge de origen:
- AUTO = generado por el sistema (gris)
- OPS = subido por operaciones (azul)
- FIN = módulo financiero (verde oscuro)

Estado de gate: pending (gris), done (verde), blocking (rojo).

**4. Timeline canónico**

```typescript
// lib/constants/states.ts — crear este archivo
export const CANONICAL_STATE_ORDER = [
  'REGISTRO', 'PRODUCCION', 'PREPARACION', 'DESPACHO',
  'TRANSITO', 'EN_DESTINO', 'CERRADO',
] as const;
export type CanonicalState = typeof CANONICAL_STATE_ORDER[number] | 'CANCELADO';
```

CANCELADO: badge rojo en el header, **nunca en el timeline lineal**.
Hito activo: punto sólido `var(--brand-primary)` + fecha real + pulse animation:

```css
@keyframes timeline-pulse {
  0%  { box-shadow: 0 0 0 0 var(--timeline-pulse-shadow-start); }
  70% { box-shadow: 0 0 0 6px var(--timeline-pulse-shadow-end); }
}
```

**Tokens CSS nuevos que necesitás agregar a `globals.css` (o al archivo de tokens):**
```css
--surface-glass-bg:       rgba(255, 255, 255, 0.08);
--surface-glass-border:   rgba(255, 255, 255, 0.15);
--surface-overlay-navy:   rgba(1, 58, 87, 0.72);
--timeline-pulse-shadow-start: rgba(1, 58, 87, 0.20);
--timeline-pulse-shadow-end:   rgba(1, 58, 87, 0.00);
```

---

### P1 — Hacer el sprint de alta calidad

#### S15-02: Brand Console — tabs Pricing + Operations
**Agente:** AG-03 | **Archivo:** `brand-console/page.tsx` (existente, extender)

Sprint 14 entregó 4 tabs: Overview, Agreements & Policies, Orders, Catalog.
Este item agrega los 2 que faltaron:

**Tab 5 — Pricing:**
- Pricelist activa: `GET /api/brands/{id}/pricelists/?active=true`
- Tabla items con paginación DRF (`{count, next, previous, results}`) — usar `useFetch`
- Filtro categoría: `GET /api/brands/{id}/categories/` (no hardcodear)
- Overrides activos: `GET /api/brands/{id}/price-overrides/`
- Upload nueva versión: modal drag-and-drop → `POST /api/brands/{id}/pricelists/`
- Historial: `GET /api/brands/{id}/pricelists/` (todas las versiones, read-only)

**Tab 6 — Operations:**
- Fuente: `GET /api/brands/{id}/workflow-policy/`
- Shape del payload que vas a recibir:
  ```json
  {
    "brand": "uuid",
    "version": "1.0",
    "states": [
      {
        "state": "REGISTRO",
        "enabled": true,
        "commands": [
          { "code": "C2", "label": "Registrar OC", "available": true }
        ],
        "exit_states": ["PRODUCCION"],
        "artifact_requirements": [
          { "artifact_type": "ART-01", "requirement": "gate" }
        ]
      }
    ]
  }
  ```
- Matriz visual: filas = estados de `CANONICAL_STATE_ORDER`, columnas = commands extraídos del payload (no hardcodear C1-C22)
- Validador: si `exit_states` está vacío → banner warning naranja "Estado X sin transición configurada"
- Read-only MVP

**Regla importante:** Los tabs 1–4 de S14 no se tocan. Si algo se rompe en ellos, es un bug de este item.

---

#### S15-03: Vista CEO de crédito y aging
**Agente:** AG-03 | **Archivo:** `clientes/[id]/credito/page.tsx` (NUEVO)

Esta vista es la perspectiva interna CEO del crédito de un cliente.
Es diferente a la Client Console de S14 (que es self-service del cliente).

**Sección A — CreditBar**
- Reutilizar `<CreditBar>` de S15-01, no reimplementar
- `<CreditBar size="lg" showActions={true}>`
- Fuente: `GET /api/clientes/{id}/credit-exposure/`
  ```json
  { "open": 0, "in_transit": 0, "invoiced_unpaid": 0, "reserved": 0, "total": 0, "limit": 0 }
  ```
- riskLevel calculado (cliente, no expediente):
  - < 60% → LOW · 60–80% → MEDIUM · 80–100% → HIGH · >100% → CRITICAL
  - Si limit=0 → badge "Sin política" gris

**Sección B — Aging table**
- `GET /api/clientes/{id}/expedientes/?exclude_status=CERRADO,CANCELADO`
- Días calculados desde `expediente.credit_clock_start` (fallback: `created_at`)
- Buckets: 0–30d (verde) · 31–60d (amarillo) · 61–90d (naranja) · 90+d (rojo)
- Orden: 90+d primero (más crítico arriba)
- Si el endpoint no devuelve el cálculo de aging → mostrar "N/A", no calcular en frontend

**Sección D — Acciones CEO (visible solo role=CEO)**
- "Congelar crédito" → ConfirmDialog → `POST /api/clientes/{id}/credit-actions/freeze/`
- "Ajustar límite" → drawer (nuevo_limite + razón) → `PATCH /api/clientes/{id}/credit-policy/`
- "Ver historial" → modal ConfigChangeLog

---

#### S15-04 + S15-05: Portal B2B upgrade
**Agente:** AG-03

**Login (S15-04):**
Archivos: `app/[lang]/(portal)/login/page.tsx` y `app/[lang]/(portal)/onboarding/page.tsx`

Tokens exactos para el glassmorphism (usar las variables CSS que agregaste en S15-01):
- Overlay fondo: `var(--surface-overlay-navy)` + `filter: blur(8px)`
- Card: `background: var(--surface-glass-bg)` + `backdrop-filter: blur(20px)` + `border: 1px solid var(--surface-glass-border)`
- Contraste mínimo WCAG AA (4.5:1) — verificar en DevTools
- Selector idioma ES/EN/PT: visible antes del login, en el header
  - `localStorage` guarda la preferencia del selector
  - Routing usa `[lang]` segment (Next.js middleware) como fuente de verdad, no localStorage
- Errores inline con `role="alert"` bajo cada campo

Onboarding wizard: trigger cuando `expedientes_count === 0` post-login.
- Ruta: `/{lang}/portal/onboarding` (mismo patrón que el resto del portal)
- 3 pasos: datos empresa → contactos → preferencias
- Pasos 2 y 3 tienen "Skip"
- Redirect final: `/{lang}/portal/dashboard`

**Order Tracking (S15-05):**
Archivo: `app/[lang]/(portal)/expedientes/[id]/page.tsx`

El estado interno (`expediente.status`) no cambia. Solo el label de display:

| Estado | ES | EN | PT |
|--------|----|----|-----|
| REGISTRO | Pedido recibido | Order received | Pedido recebido |
| PRODUCCION | En producción | In production | Em produção |
| PREPARACION | Preparando despacho | Preparing shipment | Preparando envio |
| DESPACHO | Despachado | Dispatched | Despachado |
| TRANSITO | En tránsito | In transit | Em trânsito |
| EN_DESTINO | En destino | At destination | No destino |
| CERRADO | Entregado | Delivered | Entregue |
| CANCELADO | Cancelado | Cancelled | Cancelado |

Reutilizar `lib/i18n/states.ts` que creaste en S15-01.

Documentos: renderizar según `artifact.visibility` que devuelve la API.
Si ART-06 o ART-08 no aparecen en el response → no renderizar (decisión del backend).

---

### P2 — Si hay tiempo

#### S15-06: Dashboard Kanban cards + Urgent Actions
**Agente:** AG-03 | Condicional: solo si S15-01 a S15-05 completados.

**Kanban cards — 7 campos exactos en este orden:**

| # | Campo | Key del payload | Fallback |
|---|-------|----------------|---------|
| 1 | ref | `expediente.ref` | siempre presente |
| 2 | health indicator | derivado de `expediente.status` + tokens C5 | — |
| 3 | subsidiaria | `expediente.client.subsidiary_name` | "—" |
| 4 | monto | `expediente.snapshot.order_total` | ocultar campo |
| 5 | badge marca | `brand.short_name` + `brand.color_token` | badge gris |
| 6 | días en estado | `expediente.days_in_current_state` | calcular desde `last_transition_at` |
| 7 | hito progreso | `completed_gates / total_gates` | ocultar barra |

Nota: `health_indicator` no viene de la API. Se deriva del `status` usando los
mismos tokens semánticos del timeline.

**Urgent Actions:**
- Fuente: `GET /api/dashboard/urgent-actions/`
- Si 404 → mostrar empty state "No hay acciones urgentes". No crash.
- Si 200 → lista numerada desde API

---

## Lo que NO tenés que hacer

- ❌ Crear modelos Django, migrations, ni nuevas apps
- ❌ Modificar ENT_OPS_STATE_MACHINE (FROZEN)
- ❌ Inventar estados de expediente (solo los 8 canónicos)
- ❌ Poner rgba() o hex hardcodeados en componentes (usar tokens CSS)
- ❌ Poner montos en JetBrains Mono (solo IDs, SKUs, refs técnicas)
- ❌ Exponer campos CEO-ONLY en el portal (fob_unit, margin_pct, commission_pct, landed_cost, dai_amount)
- ❌ Modificar Brand Console tabs 1–4 ni Client Console tabs 1–7 de S14

---

## Tests obligatorios (S15-07)

```
# Funcionales
[ ] CreditBar: 4 rangos de color correctos
[ ] CreditBar: empty → "Sin política de crédito" (sin barra)
[ ] CreditBar: over-limit → barra 100% roja + mensaje
[ ] Toggle INTERNA/CLIENTE: solo visible role=CEO
[ ] Toggle: modo client → .ceo-only-field tiene display:none
[ ] Portal login: selector idioma visible antes de submit
[ ] Order tracking: label "Pedido recibido" en ES para estado REGISTRO

# Seguridad — regresión S11-10 (no romper nada)
[ ] test_cross_tenant_access: cliente A GET expediente B → 404 (no 403)
[ ] test_same_404_semantics: inexistente y ajeno → mismo 404
[ ] test_signed_url_expiry: URL expirada → 403/410
[ ] test_ceo_only_not_exposed: /api/portal/expedientes/{id}/ response JSON
    no incluye: fob_unit, margin_pct, commission_pct, landed_cost, dai_amount
[ ] test_portal_cannot_access_internal_route: /api/expedientes/ desde portal → 401/403
[ ] test_locale_switch_visibility: cambiar idioma no altera visibilidad de campos

# Regresión
[ ] Brand Console S14: 4 tabs funcionales
[ ] Client Console S14: 7 tabs funcionales
[ ] State machine: tests existentes sin modificación
[ ] CI verde en main
```

---

## Sprint DONE cuando

```
python manage.py test ✅
bandit -ll backend/ ✅
npm run lint ✅
npm run typecheck ✅
npm run test ✅
smoke Brand Console S14 (4 tabs) ✅
smoke Client Console S14 (7 tabs) ✅
CI verde en main ✅
```

---

## Reporte de ejecución (mandame esto al terminar)

```markdown
## Resultado Sprint 15
- **Agente:** AG-03 Alejandro (+ AG-02 para gate)
- **Lote:** LOTE_SM_SPRINT15 v1.3
- **Status:** DONE / PARTIAL / BLOCKED
- **Items completados:** [lista S15-00 a S15-07]
- **Items no completados:** [con razón]
- **Archivos creados:** [lista]
- **Archivos modificados:** [lista]
- **Archivos NO tocados (S14 intactos):** confirmar Brand Console y Client Console
- **Tokens CSS agregados:** confirmar --surface-glass-* y --timeline-pulse-*
- **Tests ejecutados:** [resumen — cantidad passing/failing]
- **Decisiones asumidas:** [cualquier cosa que decidiste sin spec explícita]
- **Blockers encontrados:** [o "ninguno"]
- **Write endpoints que faltaban y tuviste que implementar:** [o "todos existían"]
```
