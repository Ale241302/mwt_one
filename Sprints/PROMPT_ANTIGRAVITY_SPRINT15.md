# PROMPT_ANTIGRAVITY_SPRINT15 — Frontend UX Polish
## Para: Claude Code (Antigravity) — AG-03 Frontend + AG-02 Backend (gate)
## Sprint: 15 · Auditoría: R4 9.6/10 · Fecha: 2026-03-23

---

## TU ROL

Eres AG-03 Frontend Builder para el proyecto MWT.ONE.
Implementas los items de Sprint 15 en código Next.js/TypeScript/CSS.
El CEO (Alejandro) te da contexto y aprueba. Vos escribís código, no tomás decisiones de negocio.
Para S15-00 (gate de prerequisitos) sos AG-02 Backend.

---

## CONTEXTO DEL PROYECTO

- **Stack:** Next.js 14+ (App Router) + TypeScript + Tailwind + DRF APIs + PostgreSQL
- **Repo:** mwt.one, branch `main`
- **Sprint 15 objetivo:** Interfaces que aprovechan las APIs de Sprint 14.
  Shipment Detail CEO refactor, Brand Console extensión (+2 tabs),
  Credit & Aging CEO view, Portal B2B upgrade.
- **Prerequisito:** Sprint 14 DONE v2.0 desplegado en staging (verificar con S15-00)
- **Sprint 15 es 100% frontend.** 0 modelos Django nuevos. 0 migrations.
  Excepción: si un write endpoint necesario no existe, AG-02 lo implementa
  sin models nuevos (serializer + view sobre modelos S14 existentes).

---

## HARD RULES — NUNCA VIOLAR

1. **ENT_OPS_STATE_MACHINE es FROZEN.** Los 8 estados canónicos son:
   REGISTRO, PRODUCCION, PREPARACION, DESPACHO, TRANSITO, EN_DESTINO, CERRADO, CANCELADO.
   No inventar estados. No agregar "Facturado", "En aduana", "Procesando".
   CANCELADO es un estado terminal lateral — badge rojo en header, NUNCA en el timeline lineal.

2. **0 hex hardcodeados en componentes.**
   Todo color via CSS variables. Los rgba() van en tokens CSS (`globals.css` o archivo de tokens),
   no inline en componentes TSX.
   Tokens nuevos requeridos por S15:
   ```css
   --surface-glass-bg:            rgba(255, 255, 255, 0.08);
   --surface-glass-border:        rgba(255, 255, 255, 0.15);
   --surface-overlay-navy:        rgba(1, 58, 87, 0.72);
   --timeline-pulse-shadow-start: rgba(1, 58, 87, 0.20);
   --timeline-pulse-shadow-end:   rgba(1, 58, 87, 0.00);
   ```
   Agregalos al archivo de tokens al inicio de S15-01. Luego usarlos como `var(--token)`.

3. **0 montos en JetBrains Mono.**
   Montos financieros: `font-variant-numeric: tabular-nums` con Plus Jakarta Sans (body font).
   Mono solo para: refs de expediente (EXP-xxx), SKUs, UUIDs, timestamps técnicos.

4. **No tocar Brand Console S14 tabs 1–4 ni Client Console S14 tabs 1–7.**
   Si se rompen, es un bug de este sprint. Smoke testear después de cada cambio.

5. **Datos CEO-ONLY nunca en el portal.**
   Los campos `fob_unit`, `margin_pct`, `commission_pct`, `landed_cost`, `dai_amount`
   no aparecen en NINGÚN response de `/api/portal/...`. Eso es responsabilidad del backend.
   El toggle INTERNA/VISTA CLIENTE del CEO es UX, no seguridad.

6. **Toggle INTERNA/VISTA CLIENTE: solo role=CEO.**
   ```tsx
   {currentUser.role === 'CEO' && <ViewToggle />}
   ```
   Implementación CSS: `[data-view-mode="client"] .ceo-only-field { display: none; }`
   No eliminar del DOM — solo ocultar.

7. **CreditBar es un componente compartido.**
   Crearlo una vez en `components/ui/CreditBar.tsx`. S15-01 lo crea, S15-03 lo importa.
   No duplicar ni forkear para cada uso.

8. **Estados de i18n en un solo lugar.**
   `lib/i18n/states.ts` se crea en S15-01 y S15-05 lo reutiliza.
   Mismo archivo, no duplicar la tabla de labels.

9. **Routing portal: [lang] segment es fuente de verdad.**
   `localStorage` solo para preferencia del selector de idioma pre-auth.
   Redirects siempre incluyen `/{lang}/portal/...`.

10. **Tests antes de hacer PR.** Si un test de seguridad de S11-10 falla, hay un bug.
    Esos tests no se tocan — los resolvés arreglando el código.

---

## ORDEN DE EJECUCIÓN

```
S15-00 (Gate) ─── AG-02 verifica S14 + write endpoints ─── ANTES DE TODO

S15-01 (Shipment Detail CEO) ─── P0
  │ crea: CreditBar.tsx, states.ts, i18n/states.ts
  │ agrega tokens CSS nuevos
  │
  ├── S15-02 (Brand Console +2 tabs) ─── P1 ─── paralelo
  ├── S15-03 (Credit Aging CEO) ─── P1 ─── reutiliza CreditBar
  ├── S15-04 (Portal Login+Onboarding) ─── P1 ─── paralelo
  │       └── S15-05 (Order Tracking) ─── reutiliza i18n/states.ts
  │
  └── S15-06 (Dashboard Kanban) ─── P2 ─── condicional

S15-07 (Tests) ─── después de todo
```

---

## ITEMS

### S15-00: Gate prerequisitos
**Rol:** AG-02 Backend

Correr los 9 curls de verificación del spec (4 read + 5 write endpoints).
Si algún write endpoint responde 404/405 → implementarlo como AG-02
(serializer + view, sin models nuevos) antes de continuar.
Enviar `"GATE S15 OK — {fecha}"` a AG-03 antes de que arranque.

---

### S15-01: Shipment Detail CEO refactor
**Rol:** AG-03 Frontend
**Archivo principal:** `frontend/src/app/[lang]/dashboard/expedientes/[id]/page.tsx`

**Archivos nuevos:**
```
frontend/src/components/ui/CreditBar.tsx
frontend/src/components/expediente/StateTimeline.tsx (o actualizar el existente)
frontend/src/components/expediente/ArtifactSection.tsx (o actualizar)
frontend/src/components/expediente/CostTable.tsx (o actualizar)
frontend/src/lib/constants/states.ts
frontend/src/lib/i18n/states.ts
```

**CreditBar.tsx — contrato completo:**

```typescript
interface CreditBarProps {
  limit: number
  used: number
  currency?: string         // default 'USD'
  days_elapsed?: number
  days_limit?: number
  size?: 'sm' | 'md' | 'lg'
  showActions?: boolean     // default false
  viewMode?: 'internal' | 'client'
  loading?: boolean
  error?: string | null
  empty?: boolean
}

// Función de riesgo — expediente individual
function getCreditBarRisk(used: number, limit: number): 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL' | 'UNKNOWN' {
  if (limit <= 0) return 'UNKNOWN';
  const pct = (used / limit) * 100;
  if (pct <= 70)  return 'LOW';
  if (pct <= 90)  return 'MEDIUM';
  if (pct <= 100) return 'HIGH';
  return 'CRITICAL';
}

// Estados visuales:
// empty=true → "Sin política de crédito", barra gris, sin números
// error=truthy → "— Sin datos de crédito disponibles", barra gris
// CRITICAL → barra roja + animation: timeline-pulse (usando --timeline-pulse-shadow-*)
// over-limit → barra 100% roja + "Límite superado en $X"
```

**lib/constants/states.ts:**
```typescript
export const CANONICAL_STATE_ORDER = [
  'REGISTRO', 'PRODUCCION', 'PREPARACION', 'DESPACHO',
  'TRANSITO', 'EN_DESTINO', 'CERRADO',
] as const;
export type CanonicalState = typeof CANONICAL_STATE_ORDER[number] | 'CANCELADO';
// Regla: CANCELADO es terminal. Badge rojo en header. Nunca en el timeline.
```

**lib/i18n/states.ts:**
```typescript
// Labels para Portal B2B — se reutilizan en S15-05
export const STATE_LABELS = {
  es: {
    REGISTRO: 'Pedido recibido',
    PRODUCCION: 'En producción',
    PREPARACION: 'Preparando despacho',
    DESPACHO: 'Despachado',
    TRANSITO: 'En tránsito',
    EN_DESTINO: 'En destino',
    CERRADO: 'Entregado',
    CANCELADO: 'Cancelado',
  },
  en: {
    REGISTRO: 'Order received',
    PRODUCCION: 'In production',
    PREPARACION: 'Preparing shipment',
    DESPACHO: 'Dispatched',
    TRANSITO: 'In transit',
    EN_DESTINO: 'At destination',
    CERRADO: 'Delivered',
    CANCELADO: 'Cancelled',
  },
  pt: {
    REGISTRO: 'Pedido recebido',
    PRODUCCION: 'Em produção',
    PREPARACION: 'Preparando envio',
    DESPACHO: 'Despachado',
    TRANSITO: 'Em trânsito',
    EN_DESTINO: 'No destino',
    CERRADO: 'Entregue',
    CANCELADO: 'Cancelado',
  },
} as const;
// Estado interno (expediente.status) NUNCA cambia. Solo el label de display varía.
```

**Badges de artefactos (source_role):**
```typescript
// Mapeado de artifact_type → badge config
const ARTIFACT_BADGES = {
  'ART-01': { label: 'PREP', role: 'AUTO' },
  'ART-02': { label: 'PROFORMA', role: 'OPS' },
  'ART-03': { label: 'OC', role: 'OPS' },
  'ART-04': { label: 'PI', role: 'FIN' },
  'ART-05': { label: 'PACKING', role: 'OPS' },
  'ART-06': { label: 'BL/AWB', role: 'OPS' },
  'ART-07': { label: 'COSTOS', role: 'FIN' },  // solo interno
  'ART-08': { label: 'CERT', role: 'OPS' },
  'ART-09': { label: 'FACTURA', role: 'FIN' },
  'ART-11': { label: 'CORREC', role: 'FIN' },
  'ART-13': { label: 'VIAB', role: 'AUTO' },
  'ART-14': { label: 'AFORO', role: 'OPS' },
} as const;
// gate: pending(gris) | done(verde) | blocking(rojo)
```

**Campos CEO-ONLY (para toggle C6):**
```typescript
// Llevan clase CSS ceo-only-field
const CEO_ONLY_FIELDS = [
  'snapshot.fob_unit',
  'snapshot.margin_pct',
  'snapshot.commission_pct',
  'snapshot.landed_cost',
  'snapshot.dai_amount',
] as const;
```

**Criterio de done S15-01:**
```
[ ] components/ui/CreditBar.tsx con contrato completo
[ ] CreditBar: 4 rangos de color via tokens (no hex)
[ ] CreditBar: empty/error/over-limit renderizados correctamente
[ ] Toggle INTERNA/CLIENTE solo visible role=CEO
[ ] .ceo-only-field con display:none en modo client (no removeChild)
[ ] lib/constants/states.ts con CANONICAL_STATE_ORDER
[ ] lib/i18n/states.ts con STATE_LABELS (3 idiomas)
[ ] Timeline: 7 estados lineales + CANCELADO como badge lateral
[ ] Pulse animation usando --timeline-pulse-shadow-* tokens
[ ] Tokens --surface-glass-* y --timeline-pulse-* agregados
[ ] 0 hex/rgba inline en TSX, 0 montos en mono
```

---

### S15-02: Brand Console — tabs Pricing + Operations
**Rol:** AG-03 Frontend
**Archivo:** `frontend/src/app/[lang]/dashboard/brand-console/page.tsx` (EXTENDER)

**Tabs finales (no tocar 1-4):**
Tab1:Overview · Tab2:Agreements & Policies · Tab3:Orders · Tab4:Catalog · Tab5:Pricing · Tab6:Operations

**Tab 5 Pricing — endpoints:**
```typescript
// Pricelist activa
GET /api/brands/{id}/pricelists/?active=true
// Items paginados (DRF format)
GET /api/brands/{id}/pricelists/{pricelist_id}/items/?category={cat}&search={q}
// Overrides activos
GET /api/brands/{id}/price-overrides/
// Categorías (no hardcodear)
GET /api/brands/{id}/categories/
// Upload nueva versión
POST /api/brands/{id}/pricelists/   // multipart/form-data
// Historial
GET /api/brands/{id}/pricelists/    // todas las versiones
```

Paginación: detectar formato DRF `{count, next, previous, results}` automáticamente
con el hook `useFetch` de S12-08.

**Tab 6 Operations — payload esperado:**
```typescript
interface WorkflowPolicyResponse {
  brand: string;
  version: string;
  states: Array<{
    state: string;      // uno de CANONICAL_STATE_ORDER
    enabled: boolean;
    commands: Array<{ code: string; label: string; available: boolean; }>;
    exit_states: string[];
    artifact_requirements: Array<{
      artifact_type: string;
      requirement: 'gate' | 'required' | 'optional';
    }>;
  }>;
}
// Columnas de la matriz: extraer commands únicos del payload (no hardcodear)
// Ordenar columnas por code ascendente (C2, C3, C4...)
// Validador: if (state.exit_states.length === 0) → banner warning naranja
```

**Criterio de done S15-02:**
```
[ ] Tabs 1-4 de S14 intactos (smoke test)
[ ] Tab Pricing: pricelist activa + items paginados DRF
[ ] Tab Pricing: filtro categoría desde API
[ ] Tab Pricing: overrides listados
[ ] Tab Pricing: upload modal drag-and-drop funcional
[ ] Tab Operations: matriz estados × commands desde payload
[ ] Tab Operations: banner warning si exit_states vacío
[ ] 0 hex hardcodeados
```

---

### S15-03: Vista CEO crédito y aging
**Rol:** AG-03 Frontend
**Archivo:** `frontend/src/app/[lang]/dashboard/clientes/[id]/credito/page.tsx` (NUEVO)

**Función de riesgo para CLIENTE (distinta a la de expediente):**
```typescript
// Umbrales distintos — cliente = cartera agregada
function getClientRiskLevel(used: number, limit: number) {
  if (limit <= 0) return 'UNKNOWN';
  const pct = (used / limit) * 100;
  if (pct <= 60)  return 'LOW';
  if (pct <= 80)  return 'MEDIUM';
  if (pct <= 100) return 'HIGH';
  return 'CRITICAL';
}
```

**Endpoints:**
```
GET /api/clientes/{id}/credit-exposure/
GET /api/clientes/{id}/expedientes/?exclude_status=CERRADO,CANCELADO
GET /api/clientes/{id}/credit-policy/
POST /api/clientes/{id}/credit-actions/freeze/
PATCH /api/clientes/{id}/credit-policy/
GET /api/audit/config-changes/?entity=client&entity_id={id}
```

**Aging buckets:**
```typescript
const AGING_BUCKETS = [
  { label: '0–30d',  min: 0,  max: 30,  color: 'var(--color-success)' },
  { label: '31–60d', min: 31, max: 60,  color: 'var(--color-warning)' },
  { label: '61–90d', min: 61, max: 90,  color: 'var(--color-alert)' },
  { label: '90+d',   min: 91, max: Infinity, color: 'var(--color-danger)' },
] as const;
// Ordenar tabla: 90+d primero (más crítico arriba)
// Si aging no viene del endpoint → mostrar "N/A" en cada celda, no calcular en frontend
```

**Criterio de done S15-03:**
```
[ ] <CreditBar> importado desde S15-01 (no duplicado)
[ ] riskLevel con función getClientRiskLevel (umbrales cliente)
[ ] Aging table: 4 buckets, ordenado 90+d primero, totales en footer
[ ] Empty state si no hay expedientes activos
[ ] Acciones CEO visibles solo role=CEO
[ ] ConfirmDialog en "Congelar crédito"
```

---

### S15-04: Portal B2B Login + Onboarding
**Rol:** AG-03 Frontend

**Login — tokens exactos (no inline):**
```css
/* Usar variables declaradas en S15-01 */
.portal-bg {
  background-image: url('/assets/portal-bg-placeholder.jpg');
  filter: blur(8px);
}
.portal-overlay {
  background: var(--surface-overlay-navy);
}
.glass-card {
  background: var(--surface-glass-bg);
  backdrop-filter: blur(20px);
  border: 1px solid var(--surface-glass-border);
  border-radius: var(--radius-lg);
}
```

**Selector idioma:**
```typescript
// Orden: [lang] segment → localStorage → navigator.language → 'es'
// Al seleccionar idioma en login: router.push(`/${locale}/portal/login`)
// Persistir en localStorage('portal_locale') para pre-fill del selector
// localStorage NO gobierna el routing — [lang] de la URL lo hace
```

**Errores inline:**
```tsx
{error && <p role="alert" aria-live="polite" className="...">{error}</p>}
```

**Onboarding routing:**
```typescript
// Trigger: GET /api/portal/me/ → expedientes_count === 0
// Redirect: router.push(`/${lang}/portal/onboarding`)  // con lang activo
// Paso 3 completo: router.push(`/${lang}/portal/dashboard`)
```

**Criterio de done S15-04:**
```
[ ] Selector idioma visible pre-auth, persiste entre visitas
[ ] Glassmorphism con var(--surface-glass-*) — 0 rgba inline
[ ] Contraste >= 4.5:1 verificado
[ ] Errores inline role="alert"
[ ] Wizard en /{lang}/portal/onboarding, skip en pasos 2 y 3
[ ] Redirect final con [lang] correcto
[ ] Tests negativos S11-10 sin regresión
```

---

### S15-05: Portal B2B Order Tracking
**Rol:** AG-03 Frontend

**Componente StateTimelinePortal:**
```typescript
// REUTILIZAR STATE_LABELS de lib/i18n/states.ts (creado en S15-01)
// NO crear una nueva tabla de labels

import { STATE_LABELS } from '@/lib/i18n/states';

// Uso:
const label = STATE_LABELS[currentLocale]?.[expediente.status] ?? expediente.status;
// expediente.status (interno) NUNCA cambia — solo el label de display
```

**Documentos — regla de render:**
```typescript
// El backend /api/portal/expedientes/{id}/artifacts/ ya filtra PARTNER_B2B
// Solo renderizar lo que devuelve la API
// Si ART-06 o ART-08 no están en el array → no aparecen (decisión del backend)
// NO mostrar badge "Pendiente autorización" — ese estado no existe en el contrato
artifacts.map(artifact => (
  <ArtifactRow
    key={artifact.id}
    type={artifact.artifact_type}
    name={artifact.name}
    date={artifact.created_at}
    signedUrl={artifact.signed_url}  // 30min expiry
  />
))
```

**Criterio de done S15-05:**
```
[ ] Labels i18n desde STATE_LABELS (reutilizado, no duplicado)
[ ] Estado interno intacto (solo display cambia)
[ ] Documentos filtrados por la API (frontend no filtra)
[ ] Signed URLs abren en nueva pestaña
[ ] TEST: /api/portal/expedientes/{id}/ no incluye fob_unit/margin_pct/
    commission_pct/landed_cost/dai_amount
[ ] TEST: cross-tenant → 404
[ ] TEST: signed URL expirada → 403/410
```

---

### S15-06: Dashboard Kanban + Urgent Actions (P2 — condicional)
**Rol:** AG-03 Frontend
**Condicional:** Solo si S15-01 a S15-05 completados.

**Kanban card — mapeo payload→render 1:1:**
```typescript
// Fuente: GET /api/expedientes/?ordering=status
// Shape del payload esperado:
interface ExpedienteCardPayload {
  id: string;
  ref: string;                    // campo 1 — JetBrains Mono
  status: CanonicalState;         // campo 2 — derivar health indicator (no viene de API)
  last_transition_at: string;
  client: { subsidiary_name: string; };  // campo 3
  brand: { short_name: string; color_token: string; };  // campo 5 — badge construido en el componente
  snapshot: { order_total: number; } | null;  // campo 4 — si null, ocultar
  days_in_current_state?: number;  // campo 6 — si ausente, calcular
  completed_gates?: number;        // campo 7 — si ausente, ocultar barra
  total_gates?: number;
}

// campo 2: health_indicator NO es un campo del payload
// Se deriva de status usando tokens semánticos:
const HEALTH_COLORS: Record<CanonicalState, string> = {
  REGISTRO: 'var(--state-registro)',
  PRODUCCION: 'var(--state-produccion)',
  // ... etc
};

// campo 4: usar snapshot.order_total, nunca oc_total (no existe)
// campo 5: badge = <span style={{background: brand.color_token}}>{brand.short_name}</span>
// campo 6: si days_in_current_state ausente:
const days = payload.days_in_current_state
  ?? Math.floor((Date.now() - new Date(payload.last_transition_at).getTime()) / 86_400_000);
```

**Urgent Actions:**
```typescript
// GET /api/dashboard/urgent-actions/
// Si 404: mostrar empty state, no crash
// Si 200:
interface UrgentAction {
  priority: number;
  action: string;
  reason: string;
  expediente_ref: string;   // JetBrains Mono en el render
  expediente_id: string;
}
// Empty state: "No hay acciones urgentes"
```

---

### S15-07: Tests
**Archivos:**
```
frontend/src/components/ui/__tests__/CreditBar.test.tsx
backend/apps/portal/tests/test_s15_security.py
frontend/src/components/portal/__tests__/order_tracking.test.tsx
```

**Tests de seguridad — backend — S11-10 regresión:**
```python
# test_s15_security.py
def test_cross_tenant_access(self):
    # Cliente A no puede ver expediente de Cliente B → 404 (no 403)
    
def test_same_404_semantics(self):
    # Expediente inexistente y expediente de otro cliente → mismo 404 body
    
def test_signed_url_expiry(self):
    # URL con expiry pasado → 403/410
    
def test_ceo_only_not_exposed(self):
    # /api/portal/expedientes/{id}/ response
    # NOT in response: fob_unit, margin_pct, commission_pct, landed_cost, dai_amount
    
def test_portal_cannot_access_internal_route(self):
    # Token de portal → GET /api/expedientes/ → 401/403
    
def test_locale_switch_visibility(self):
    # Cambiar locale no altera visibilidad de campos en response
```

**Sprint DONE solo si:**
```bash
python manage.py test && bandit -ll backend/ &&
npm run lint && npm run typecheck && npm run test &&
# smoke Brand Console S14 tabs 1-4 funcionales &&
# smoke Client Console S14 tabs 1-7 funcionales &&
# CI verde en main
```

---

## PREGUNTAS PARA EL CEO (no inventar respuestas)

Si necesitás alguno de estos datos:
- Colores de token por marca (ej: `--brand-marluvas`) → CEO los define
- Umbrales definitivos de riskLevel por cartera → CEO los valida contra ENT_GOB_KPI
- Decisión CEO-15 (ART-06/ART-08 visibles en portal) → backend actualiza el filtro
- Endpoint `/api/dashboard/urgent-actions/` no existe → mencionar, no implementar en S15

**Marcar como `// TODO: CEO_INPUT_REQUIRED` y seguir con el resto.**
