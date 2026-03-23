# LOTE_SM_SPRINT15 — Frontend UX: Stitch Polish + Consolas CEO + Portal B2B
id: LOTE_SM_SPRINT15
version: 1.1
visibility: [INTERNAL]
domain: Plataforma (IDX_PLATAFORMA)
status: DRAFT — Pendiente aprobación CEO
tipo: Lote ruteado (ref → PLB_ORCHESTRATOR §E)
sprint: 15
priority: P1
depends_on: LOTE_SM_SPRINT14 (DONE v2.0)
refs: REPORTE_SESION_STITCH_20260321, ENT_PLAT_DESIGN_TOKENS v1.1,
      ENT_PLAT_FRONTENDS, ENT_OPS_STATE_MACHINE (FROZEN v1.2.2),
      ENT_PLAT_MODULOS, POL_VISIBILIDAD v1.2, ENT_PLAT_SEGURIDAD

---

## Contexto y ajuste post-S14

Sprint 14 entregó más de lo planeado en UI:
- Brand Console: 4 tabs (Overview, Agreements & Policies, Orders, Catalog)
- Client Console: 7 tabs self-service (Dashboard, Catalog, Cart/Checkout,
  Active Orders, History, Financials, Settings)

Lo que S14 NO entregó (scope de S15):
- Brand Console tabs Pricing + Operaciones
- Vista CEO de crédito y aging (distinta del Client Console self-service)
- Detalle expediente CEO refactorizado (UX-02/03/07)
- Portal B2B upgrade login + tracking
- Dashboard Kanban cards + Urgent Actions

## Objetivo

Sprint 100% frontend/UX. 0 modelos Django nuevos. Consume APIs de S14.

4 ejes:
1. Detalle expediente CEO — reloj crédito + toggle interna/cliente + badges artefactos
2. Brand Console extensión — tabs Pricing + Operaciones sobre los 4 de S14
3. Credit & Aging view CEO — vista interna de crédito (distinta de self-service S14)
4. Portal B2B upgrade — login glassmorphism + order tracking client-friendly

Precondición hard: S14 DONE v2.0 desplegado en staging + S15-00 gate pasado.

---

## Convenciones

### C1. 0 hex hardcodeados
Todo color via CSS variables (ENT_PLAT_DESIGN_TOKENS v1.1).
Tokens base: --brand-primary (#013A57), --brand-accent (#75CBB3), --brand-ice (#A8D8EA).
Estados semánticos: --color-success, --color-warning, --color-alert, --color-danger.

Tokens nuevos requeridos por S15 (agregar a ENT_PLAT_DESIGN_TOKENS v1.2 en este sprint):

```css
/* Portal login glassmorphism */
--surface-glass-bg:       rgba(255, 255, 255, 0.08);
--surface-glass-bg-hover: rgba(255, 255, 255, 0.12);
--surface-glass-border:   rgba(255, 255, 255, 0.15);
--surface-overlay-navy:   rgba(1, 58, 87, 0.72);   /* var(--brand-primary) al 72% */

/* Timeline pulse (hito activo) */
--timeline-pulse-shadow-start: rgba(1, 58, 87, 0.20);
--timeline-pulse-shadow-end:   rgba(1, 58, 87, 0.00);
```

Regla: si un rgba() aparece en código frontend, es un bug — debe ser var(--token).
Excepción acotada: NO existe. Los rgba() de glassmorphism y pulse van en tokens.
AG-03 no hardcodea rgba en componentes — los valores viven en tokens CSS globales.

### C2. Montos en Plus Jakarta Sans tabular-nums
Montos financieros NUNCA en fuente mono.
IDs, SKUs, refs expediente, UUIDs: JetBrains Mono. Ref ENT_PLAT_DESIGN_TOKENS.B2.

### C3. Copy de dominio desde KB
Nombres de tecnología desde ENT_TECH. Productos sin sufijos inventados.
Ref REPORTE_SESION_STITCH_20260321.E.

### C4. Escala real de operación
~7 expedientes activos, ~$150K. Dato ausente: // TODO: [PENDIENTE - NO INVENTAR]

### C5. CANONICAL_STATE_ORDER

```typescript
// frontend/src/lib/constants/states.ts
export const CANONICAL_STATE_ORDER = [
  'REGISTRO', 'PRODUCCION', 'PREPARACION', 'DESPACHO',
  'TRANSITO', 'EN_DESTINO', 'CERRADO',
] as const;
export type CanonicalState = typeof CANONICAL_STATE_ORDER[number] | 'CANCELADO';
// CANCELADO: estado terminal lateral. Badge rojo en header. NUNCA en timeline.
```

Fuente: ENT_OPS_STATE_MACHINE FROZEN v1.2.2. No agregar estados.

### C6. Matriz visibilidad CEO-ONLY — Detalle Expediente

| Campo             | Tier       | Vista INTERNA | Vista CLIENTE | Key payload API      |
|-------------------|------------|---------------|---------------|----------------------|
| FOB unitario      | CEO-ONLY   | visible        | OCULTO        | snapshot.fob_unit    |
| Margen %          | CEO-ONLY   | visible        | OCULTO        | snapshot.margin_pct  |
| Comision %        | CEO-ONLY   | visible        | OCULTO        | snapshot.commission_pct |
| Costo landed      | CEO-ONLY   | visible        | OCULTO        | snapshot.landed_cost |
| DAI / aranceles   | CEO-ONLY   | visible        | OCULTO        | snapshot.dai_amount  |
| Precio acordado   | PARTNER_B2B| visible        | visible       | snapshot.agreed_price|
| Total OC          | PARTNER_B2B| visible        | visible       | oc_total             |
| Estado            | PARTNER_B2B| visible        | visible       | status               |
| Artefactos PB2B   | PARTNER_B2B| visible        | visible       | artifacts[].visibility|
| ETA / ETD         | PARTNER_B2B| visible        | visible       | logistics.eta        |

Implementación: clase CSS .ceo-only-field con display:none cuando
data-view-mode="client" en el contenedor. NO eliminar del DOM.
El endpoint /api/portal/expedientes/{id}/ NUNCA incluye keys CEO-ONLY
(responsabilidad backend S14, no del toggle CSS).

### C7. Componente CreditBar — contrato de props

```typescript
interface CreditBarProps {
  limit: number;              // limite credito USD
  used: number;               // open + in_transit + invoiced_unpaid + reserved
  currency?: string;          // default 'USD'
  days_elapsed?: number;
  days_limit?: number;
  size?: 'sm' | 'md' | 'lg'; // default 'md'
  showActions?: boolean;      // default false
  viewMode?: 'internal' | 'client'; // default 'internal'
  loading?: boolean;
  error?: string | null;
  empty?: boolean;            // sin CreditPolicy activa
}

// Rangos de color (expediente individual):
function getCreditBarRisk(used: number, limit: number): RiskLevel {
  if (limit <= 0) return 'UNKNOWN';
  const pct = (used / limit) * 100;
  if (pct <= 70)  return 'LOW';      // --color-success
  if (pct <= 90)  return 'MEDIUM';   // --color-warning
  if (pct <= 100) return 'HIGH';     // --color-alert
  return 'CRITICAL';                  // --color-danger + pulse
}
// over-limit: barra 100% roja + "Limite superado en $X"
// empty: texto "Sin politica de credito", barra gris
```

Reutilizacion: S15-01 (Shipment Detail) y S15-03 (Credit Aging CEO).
Mismo componente, sin forks visuales.

### C8. Labels i18n — estados en Portal B2B

Namespace: portal.order.states.* en public/locales/{es,en,pt}/portal.json

| canonical_state | es_label           | en_label         | pt_label         |
|-----------------|--------------------|------------------|------------------|
| REGISTRO        | Pedido recibido    | Order received   | Pedido recebido  |
| PRODUCCION      | En produccion      | In production    | Em producao      |
| PREPARACION     | Preparando despacho| Preparing shipmt | Preparando envio |
| DESPACHO        | Despachado         | Dispatched       | Despachado       |
| TRANSITO        | En transito        | In transit       | Em transito      |
| EN_DESTINO      | En destino         | At destination   | No destino       |
| CERRADO         | Entregado          | Delivered        | Entregue         |
| CANCELADO       | Cancelado          | Cancelled        | Cancelado        |

Labels son solo display. expediente.status (canonico) nunca cambia.

### C9. Formula riskLevel — Credit Aging por cliente

```typescript
// Umbrales distintos a C7 (cliente = cartera, no expediente individual)
// Alineados con ENT_GOB_KPI.B1 umbrales credito
function getClientRiskLevel(used: number, limit: number): RiskLevel {
  if (limit <= 0) return 'UNKNOWN';
  const pct = (used / limit) * 100;
  if (pct <= 60)  return 'LOW';
  if (pct <= 80)  return 'MEDIUM';
  if (pct <= 100) return 'HIGH';
  return 'CRITICAL';
}
// limit=0 o CreditPolicy ausente -> badge "Sin politica" (gris). No inventar.
// Si CEO define umbrales formales en ENT_GOB_KPI -> reemplazar esta funcion.
```

### C10. Aging buckets

| Bucket        | Rango     | Color semántico    |
|---------------|-----------|--------------------|
| Corriente     | 0-30 dias | --color-success    |
| Vencido 31-60d| 31-60     | --color-warning    |
| Vencido 61-90d| 61-90     | --color-alert      |
| Vencido 90+d  | >90       | --color-danger     |

Calculo: dias desde expediente.credit_clock_start
(fallback: expediente.created_at si credit_clock_start es null).
Solo estados activos (excluir CERRADO y CANCELADO).
Orden en tabla: 90+d primero.

### C11. Artefactos — taxonomia de badges

| artifact_type | badge_label    | generated_by_role | visibility  |
|--------------|----------------|-------------------|-------------|
| ART-01       | Ficha tecnica  | AUTO              | INTERNAL    |
| ART-02       | Proforma       | OPS               | PARTNER_B2B |
| ART-03       | Decision B/C   | AUTO              | INTERNAL    |
| ART-04       | OC Confirmada  | OPS               | PARTNER_B2B |
| ART-06       | Packing List   | OPS               | PARTNER_B2B |
| ART-08       | BL / AWB       | OPS               | PARTNER_B2B |
| ART-09       | Factura MWT    | FIN               | PARTNER_B2B |
| ART-11       | Liquidacion    | FIN               | INTERNAL    |
| ART-13       | Nota viabilidad| AUTO              | INTERNAL    |
| ART-14       | F4 Baseline    | FIN               | INTERNAL    |

generated_by_role: AUTO=sistema, OPS=operaciones, FIN=modulo financiero.
Gate: pending(gris) / done(verde) / blocking(rojo).
Portal B2B: solo visibility=PARTNER_B2B.

### C12. Portal B2B Login — spec verificable

| Elemento      | Spec verificable                        | Valor exacto                                    |
|---------------|-----------------------------------------|-------------------------------------------------|
| Fondo         | Imagen blur + overlay Navy              | filter:blur(8px) + var(--surface-overlay-navy)  |
| Card          | Glassmorphism                           | bg:var(--surface-glass-bg) + blur(20px) + border:var(--surface-glass-border) |
| Contraste     | WCAG AA minimo                          | >=4.5:1 sobre overlay                           |
| Selector idioma| Pre-auth, persistente                  | Header antes de credenciales, localStorage      |
| Focus         | Visible y accesible                     | outline:2px solid var(--brand-accent)           |
| Tab order     | Logico                                  | idioma -> email -> password -> submit           |
| Errores       | Inline, no toast                        | Bajo el campo, role="alert"                     |

---

## Items

### FASE 0 — Gate prerequisitos

#### S15-00: Verificacion de S14 desplegado
Agente: AG-02 Backend

```bash
# Snapshot comercial en expediente
curl -H "Authorization: Bearer $CEO_TOKEN" /api/expedientes/{id}/ \
  | jq '.snapshot | keys'
# Esperado: ["fob_unit","margin_pct","commission_pct","landed_cost",
#            "credit_policy","agreed_price","dai_amount"]

# Brand con pricelist + workflow policy
curl -H "Authorization: Bearer $CEO_TOKEN" /api/brands/{id}/ \
  | jq '{pricelist:.pricelist_active.id, policy:.workflow_policy.id}'
# Esperado: ambos no-null

# CreditExposure del cliente
curl -H "Authorization: Bearer $CEO_TOKEN" /api/clientes/{id}/ \
  | jq '.credit_exposure'
# Esperado: {open,in_transit,invoiced_unpaid,reserved,total,limit}

# Portal catalog sin CEO-ONLY
curl -H "Authorization: Bearer $CLIENT_TOKEN" /api/portal/catalog/ \
  | jq 'map(keys) | flatten | unique'
# NOT includes: fob_unit, margin_pct, commission_pct, landed_cost

# ── WRITE ENDPOINTS requeridos por S15 ──────────────────────────────
# Pricelist upload (S15-02 Tab Pricing)
curl -X POST -H "Authorization: Bearer $CEO_TOKEN" \
  -F "file=@/tmp/test.csv" /api/brands/{id}/pricelists/
# Esperado: 201 o 400 (endpoint existe, no 404 ni 405)

# Freeze credito (S15-03 Seccion D)
curl -X POST -H "Authorization: Bearer $CEO_TOKEN" \
  /api/clientes/{id}/credit-actions/freeze/ -d '{}'
# Esperado: 200/201 o 400 (endpoint existe, no 404 ni 405)

# Ajustar limite de credito (S15-03 Seccion D)
curl -X PATCH -H "Authorization: Bearer $CEO_TOKEN" \
  /api/clientes/{id}/credit-policy/ \
  -H "Content-Type: application/json" \
  -d '{"limit": 50000, "reason": "test"}'
# Esperado: 200 o 400 (endpoint existe, no 404 ni 405)

# Guardar contacto del portal (S15-04 Paso 2)
curl -X POST -H "Authorization: Bearer $CLIENT_TOKEN" \
  /api/portal/contacts/ \
  -H "Content-Type: application/json" \
  -d '{"name":"test","email":"t@t.com","phone":"","role":""}'
# Esperado: 201 o 400 (endpoint existe, no 404)

# Guardar preferencias del portal (S15-04 Paso 3)
curl -X PATCH -H "Authorization: Bearer $CLIENT_TOKEN" \
  /api/portal/me/preferences/ \
  -H "Content-Type: application/json" \
  -d '{"locale":"es","notifications_email":true}'
# Esperado: 200 o 400 (endpoint existe, no 404)
```

Si algun write endpoint falla con 404/405:
- AG-02 lo implementa ANTES de que AG-03 conecte esa feature
- AG-03 puede avanzar en items que no dependen del endpoint faltante
- Item bloqueado: documentar en comentario del PR como "pendiente endpoint"
  y excluir del criterio de DONE de ese item hasta desbloquearse

Criterio de done:
- [ ] 4 read endpoints con estructura esperada
- [ ] 5 write endpoints responden 2xx o 4xx (no 404/405)
- [ ] Brand Console S14: 4 tabs funcionales (smoke test)
- [ ] Client Console S14: 7 tabs funcionales (smoke test)
- [ ] Signed URLs con expiry en URL, 403/410 al expirar
- [ ] AG-03 recibe go-ahead escrito de AG-02

---

### FASE 1 — Detalle expediente CEO (P0)

#### S15-01: Shipment Detail CEO refactor
Agente: AG-03 Frontend
Dependencia: S15-00 DONE
Ruta: /{lang}/dashboard/expedientes/[id]/page.tsx
Ref visual: Stitch ceo_detail_exp_ee54d6ea_marluvas/screen.png (9/10)

Archivos impactados:
- expedientes/[id]/page.tsx — reescritura
- components/ui/CreditBar.tsx — NUEVO
- components/expediente/StateTimeline.tsx — actualizar con C5
- components/expediente/ArtifactSection.tsx — actualizar con C11
- components/expediente/CostTable.tsx — agregar toggle C6
- lib/constants/states.ts — agregar CANONICAL_STATE_ORDER

Bloque A — Header:
- Ref en JetBrains Mono
- Badge marca: color token (no hex)
- Badge estado: color semantico de CANONICAL_STATE_ORDER
- CANCELADO: badge rojo en header, NUNCA en timeline
- Subtitle: {subsidiary.name} · {expediente.created_at}

Bloque B — CreditBar:
- <CreditBar size="md"> con props de C7
- Fuente: snapshot.credit_policy del endpoint
- Si snapshot.credit_policy ausente: <CreditBar empty />

Bloque C — Toggle INTERNA / VISTA CLIENTE:
- Visible SOLO si currentUser.role === 'CEO'
- Implementacion:
  <div data-view-mode={viewMode}> {/* 'internal' | 'client' */}
  [data-view-mode="client"] .ceo-only-field { display: none; }
- Default: 'internal'
- Tooltip: "Vista Interna — incluye datos confidenciales CEO"
- Campos segun C6 exactamente

Bloque D — Artefactos:
- Badge generated_by_role (AUTO/OPS/FIN) segun C11
- Gate icon: pending(gris) / done(verde) / blocking(rojo)

Bloque E — Timeline:
- CANONICAL_STATE_ORDER de C5 (7 estados lineales)
- CANCELADO: badge rojo lateral, NUNCA en la linea
- Hito activo: punto solido --brand-primary + fecha + pulse animation
  @keyframes timeline-pulse {
    0%  { box-shadow: 0 0 0 0 var(--timeline-pulse-shadow-start); }
    70% { box-shadow: 0 0 0 6px var(--timeline-pulse-shadow-end); }
  }
- Hitos futuros: punto hueco gris

Criterio de done:
- [ ] CreditBar.tsx con contrato completo C7 (loading/empty/error/over-limit)
- [ ] CreditBar con 4 rangos de color correctos
- [ ] Toggle visible SOLO role=CEO (test: no-CEO no ve toggle)
- [ ] Modo VISTA CLIENTE: campos C6 con display:none (no removidos del DOM)
- [ ] curl /api/portal/expedientes/{id}/ no incluye keys CEO-ONLY
- [ ] Badges AUTO/OPS/FIN segun C11
- [ ] Timeline usa CANONICAL_STATE_ORDER; CANCELADO como badge lateral
- [ ] Pulse animation en hito activo
- [ ] 0 hex hardcodeados, 0 montos en mono, 0 estados fuera de C5

---

### FASE 2 — Brand Console extension (P1)

#### S15-02: Brand Console — tabs Pricing + Operations
Agente: AG-03 Frontend
Dependencia: S15-00 DONE
Archivo: dashboard/brand-console/page.tsx — EXTENDER (no tocar tabs 1-4)

Tab order final:
Tab1:Overview · Tab2:Agreements & Policies · Tab3:Orders · Tab4:Catalog
· Tab5:Pricing · Tab6:Operations

Tab 5 — Pricing:
- Header badge: "Pricing · {count}"
- Pricelist activa: GET /api/brands/{id}/pricelists/?active=true
  Campos: nombre, version, valid_from/to, status badge
- Tabla PricelistItems (paginacion DRF {count,next,previous,results}):
  SKU(mono) · nombre · precio base(tabular-nums)
  Filtro categoria: GET /api/brands/{id}/categories/ (no hardcodear)
- Overrides activos: GET /api/brands/{id}/price-overrides/
  Columnas: subsidiaria · SKU o "todos" · tipo · valor · valido hasta
- Upload pricelist: boton → <PricelistUploadModal> drag-and-drop
  POST /api/brands/{id}/pricelists/
- Historial: GET /api/brands/{id}/pricelists/ (todas las versiones, read-only)

Tab 6 — Operations:
- Fuente: GET /api/brands/{id}/workflow-policy/
  Shape esperado del payload:
  ```json
  {
    "brand": "uuid",
    "version": "1.0",
    "states": [
      {
        "state": "REGISTRO",
        "enabled": true,
        "commands": [
          { "code": "C2", "label": "Registrar OC", "available": true },
          { "code": "C3", "label": "Registrar PI", "available": true }
        ],
        "exit_states": ["PRODUCCION"],
        "artifact_requirements": [
          { "artifact_type": "ART-01", "requirement": "gate" },
          { "artifact_type": "ART-02", "requirement": "required" }
        ]
      }
      // ... 7 estados más
    ]
  }
  ```
  Si el endpoint devuelve un shape diferente → AG-02 actualiza la spec
  antes de que AG-03 construya la UI (no improvisar el mapping).

- Matriz visual: filas = CANONICAL_STATE_ORDER (C5, 7 estados lineales + CANCELADO)
  columnas = todos los commands únicos de policy.states[].commands[]
  (no hardcodear C1-C22 — extraer del payload)
  Celda: ✓ si available=true · — si available=false · ⚠ si conditional
  Orden de columnas: por code (C2, C3, C4… C22) ascendente
- ArtifactRequirements por estado: badge gate/required/optional por artifact_type
- Validador: si state.exit_states es vacío → banner warning naranja:
  "Estado {state} sin transicion configurada"
- Read-only MVP

Criterio de done:
- [ ] Tabs 1-4 de S14 intactos (smoke test S15-00)
- [ ] Tab Pricing: pricelist activa con items paginados DRF
- [ ] Tab Pricing: filtro categoria desde API (no hardcodeado)
- [ ] Tab Pricing: overrides con columnas correctas
- [ ] Tab Pricing: upload modal drag-and-drop funcional
- [ ] Tab Pricing: historial read-only
- [ ] Tab Operations: matriz CANONICAL_STATE_ORDER x commands
- [ ] Tab Operations: ArtifactRequirements listados
- [ ] Tab Operations: banner validador si estado sin salida
- [ ] 0 hex hardcodeados

---

### FASE 3 — Credit & Aging view CEO (P1)

#### S15-03: Vista CEO de credito y aging
Agente: AG-03 Frontend
Dependencia: S15-01 DONE (CreditBar.tsx disponible)
Ruta: /{lang}/dashboard/clientes/[id]/credito/page.tsx — NUEVA pagina
Ref visual: Stitch credit_aging_refined_v2/screen.png (9.5/10)
Visibilidad: INTERNAL/CEO. Esta pagina NO existe en el portal B2B.

Archivos impactados:
- clientes/[id]/credito/page.tsx — NUEVO
- components/ui/CreditBar.tsx — import directo (no duplicar)
- Agregar link "Credito" en nav del detalle de cliente existente

Seccion A — Exposicion de credito:
- <CreditBar size="lg" showActions={true} viewMode="internal">
- GET /api/clientes/{id}/credit-exposure/
  Esperado: {open, in_transit, invoiced_unpaid, reserved, total, limit, currency}
- Desglose textual:
    Abierto              ${open}
    En transito          ${in_transit}
    Facturado sin cobrar  ${invoiced_unpaid}
    Reservado            ${reserved}
    ─────────────────────────────
    Total utilizado      ${total}
    Limite de credito    ${limit}
- riskLevel badge: formula C9 (cliente != expediente)
- Si limit=0 o endpoint falla: badge "Sin politica" (gris)

Seccion B — Aging table:
- GET /api/clientes/{id}/expedientes/?exclude_status=CERRADO,CANCELADO
- Buckets segun C10, ordenar: 90+d primero
- Columnas: ref(mono) · subsidiaria · monto(tabular-nums) · bucket · dias
- Footer: total por bucket
- Link en ref → /{lang}/dashboard/expedientes/{id} (S15-01)
- Empty state si no hay expedientes activos

Seccion C — Politica activa:
- GET /api/clientes/{id}/credit-policy/
- Campos: limite · plazo dias · scope · valid_from/to
- Link historial: ConfigChangeLog inline

Seccion D — Acciones CEO (solo role=CEO):
- "Congelar credito": ConfirmDialog → POST /api/clientes/{id}/credit-actions/freeze/
- "Ajustar limite": <CreditLimitDrawer> (nuevo_limite + razon) →
  PATCH /api/clientes/{id}/credit-policy/
- "Ver historial": expand ConfigChangeLog inline

Criterio de done:
- [ ] <CreditBar> importado de S15-01 (no duplicado, import directo)
- [ ] riskLevel con formula C9 y badge 4 niveles
- [ ] Aging table: 4 buckets C10, ordenada critico primero, totales en footer
- [ ] Empty state correcto
- [ ] Acciones CEO visibles solo role=CEO
- [ ] ConfirmDialog en "Congelar credito"

---

### FASE 4 — Portal B2B upgrade (P1)

#### S15-04: Login + Onboarding upgrade
Agente: AG-03 Frontend
Dependencia: S15-00 DONE; Portal B2B S11-10 estable
Ref visual: Stitch #19 (9.5/10) + #20 (8/10)

Archivos impactados:
- app/[lang]/(portal)/login/page.tsx — reescritura visual (tokens exactos C12)
- app/[lang]/(portal)/onboarding/page.tsx — NUEVO
- components/portal/LanguageSelector.tsx — mover a pre-auth

Routing normalizado:
- Todas las rutas portal usan /{lang}/portal/... (Next.js [lang] segment)
- Ruta onboarding: /{lang}/portal/onboarding (mismo patron)
- Locale fuente de verdad: segmento [lang] de la ruta (Next.js middleware)
- localStorage solo para preferencia de idioma del selector pre-auth
  (no es fuente primaria del routing — solo pre-fill del selector)
- Deep links mantienen idioma via [lang] en la URL, no via localStorage
- Redirect final: /{lang}/portal/dashboard (con el lang activo)

Login (tokens exactos de C12):
- Overlay: var(--surface-overlay-navy)
- Card: bg var(--surface-glass-bg) + backdrop-filter:blur(20px) +
  border:1px solid var(--surface-glass-border)
- Contraste >=4.5:1 verificado en DevTools o @axe-core
- Selector idioma pre-auth en header, localStorage como preferencia inicial
- Tab order: idioma → email → password → submit
- Errores inline role="alert"
- Seguridad S11-10 sin modificaciones

Onboarding wizard:
- Trigger: GET /api/portal/me/ → expedientes_count===0
  → redirect /{lang}/portal/onboarding (con lang activo)
- Paso 1: Datos empresa read-only + confirmar (ClientSubsidiary.name, direccion)
- Paso 2: Contactos clave (nombre+email+telefono+rol),
  POST /api/portal/contacts/. Skip disponible.
- Paso 3: Preferencias (idioma pre-filled desde [lang], notificaciones),
  PATCH /api/portal/me/preferences/. Skip disponible.
- Paso 3 completado → redirect /{lang}/portal/dashboard

Criterio de done:
- [ ] Selector idioma visible PRE-AUTH
- [ ] Card glassmorphism con tokens var(--surface-glass-*) de C12 (0 rgba inline)
- [ ] Contraste >=4.5:1 verificado
- [ ] Errores inline role="alert"
- [ ] Wizard 3 pasos en /{lang}/portal/onboarding, skip en pasos 2 y 3
- [ ] Redirect final a /{lang}/portal/dashboard con [lang] correcto
- [ ] localStorage solo como preferencia; routing via [lang] segment
- [ ] Tests negativos S11-10 sin regresion

#### S15-05: Order Tracking upgrade
Agente: AG-03 Frontend
Dependencia: S15-04 DONE
Ref visual: Stitch #17 (9.5/10)

Archivos impactados:
- (portal)/expedientes/[id]/page.tsx — actualizar
- components/portal/StateTimelinePortal.tsx — NUEVO (version portal con C8)
- public/locales/{es,en,pt}/portal.json — agregar portal.order.states.*

Timeline client-friendly:
- Componente <StateTimelinePortal> (distinto de <StateTimeline> consola)
- Labels via t('portal.order.states.{canonical_state}') segun C8
- Estado canonico interno intacto
- CANCELADO: label C8 + badge --color-danger

Documentos:
- GET /api/portal/expedientes/{id}/artifacts/ (backend filtra PARTNER_B2B)
- Columnas: badge tipo C11 · nombre · fecha · descarga
- Signed URL 30min expiry (S11-10 intacto)
- Visibilidad de artefactos: renderizar segun `artifact.visibility` devuelto
  por la API. Si ART-06 o ART-08 no aparecen en el response → no renderizar
  (decision CEO-15 resuelta en backend, no en frontend).
  El frontend NO interpreta CEO-15 directamente — consume lo que devuelve la API.

Criterio de done:
- [ ] Keys i18n ES/EN/PT segun C8 (8 estados)
- [ ] Estado canonico intacto (solo label cambia)
- [ ] Documentos con signed URLs y badges C11
- [ ] TEST: /api/portal/expedientes/{id}/ no incluye fob_unit/margin_pct/
       commission_pct/landed_cost/dai_amount
- [ ] TEST: cross-tenant → 404
- [ ] TEST: signed URL expirada → 403/410

---

### FASE 5 — Dashboard upgrade (P2 — condicional)

#### S15-06: Kanban cards + Urgent Actions
Agente: AG-03 Frontend
Condicional: solo si S15-01 a S15-05 completados.

Archivos:
- components/dashboard/KanbanCard.tsx — actualizar
- components/dashboard/UrgentActions.tsx — NUEVO o actualizar

Endpoints fuente:
- Kanban: GET /api/expedientes/?ordering=status (endpoint existente S14)
  Shape esperado por campo:
  ```json
  {
    "id": "uuid",
    "ref": "EXP-ee54d6ea",
    "status": "TRANSITO",
    "client": { "subsidiary_name": "Sondel CR" },
    "brand": { "color_token": "--brand-marluvas", "short_name": "MLV" },
    "snapshot": { "order_total": 14350.00 },
    "days_in_current_state": 12,
    "completed_gates": 3,
    "total_gates": 5
  }
  ```
  Si `days_in_current_state` no existe en S14 → calcular en frontend:
  `Math.floor((Date.now() - new Date(last_transition_at)) / 86400000)`
  Si `completed_gates`/`total_gates` no existen → ocultar barra hito (no inventar)

- Urgent Actions: GET /api/dashboard/urgent-actions/ (nuevo endpoint S16 o S15 backend)
  Si endpoint no existe (404): mostrar empty state, no crash.
  Shape esperado si existe:
  ```json
  [
    {
      "priority": 1,
      "action": "Aprobar OC pendiente",
      "reason": "3 dias sin aprobacion",
      "expediente_ref": "EXP-ee54d6ea",
      "expediente_id": "uuid"
    }
  ]
  ```

Kanban cards — 7 campos en orden de render:
1. expediente.ref (JetBrains Mono, esquina superior izquierda)
2. expediente.health_indicator (punto de color semantico)
3. expediente.client.subsidiary_name (Plus Jakarta Sans)
4. expediente.oc_total (tabular-nums con simbolo moneda)
5. expediente.brand.badge (color token de la marca)
6. expediente.days_in_current_state ("X dias en {estado_label}")
7. Barra hito: expediente.completed_gates / expediente.total_gates

Urgent Actions — criterios operativos (no inventar):
- status==='REGISTRO' + days_in_current_state>3 + OC pendiente
- Artefacto gate blocking sin resolver en estado actual
- credit_clock_days > 75 (umbral pre-bloqueo ENT_GOB_KPI.B1)
- aging_bucket IN ['61-90d', '90+d']
Empty state: "No hay acciones urgentes" (siempre visible, no ocultar)

Criterio de done:
- [ ] Kanban cards con exactamente 7 campos en orden definido
- [ ] Campos 4 y 7 ocultos si dato ausente (no placeholder, no [PENDIENTE])
- [ ] Urgent Actions: si 404 → empty state "No hay acciones urgentes"
- [ ] Urgent Actions: si 200 → lista numerada desde API (no hardcodeada)
- [ ] 0 datos inventados

---

### QA

#### S15-07: Tests Sprint 15
Archivos esperados:
- frontend/src/components/ui/__tests__/CreditBar.test.tsx
- backend/apps/portal/tests/test_s15_security.py
- frontend/src/components/portal/__tests__/order_tracking.test.tsx

Tests funcionales:
- [ ] CreditBar: 4 rangos (0-70 verde, 71-90 amarillo, 91-100 naranja, >100 rojo)
- [ ] CreditBar: empty -> "Sin politica de credito" (no barra con 0)
- [ ] CreditBar: over-limit -> barra 100% roja + "Limite superado en $X"
- [ ] Toggle INTERNA/CLIENTE: solo visible role=CEO
- [ ] Toggle: modo client -> campos C6 con display:none (no removidos del DOM)
- [ ] Brand Console Tab Pricing: paginacion DRF {count,next,results}
- [ ] Credit Aging: 4 buckets C10, critico primero, totales en footer
- [ ] Portal login: selector idioma visible antes del submit
- [ ] Order tracking: t('portal.order.states.REGISTRO') = "Pedido recibido" (ES)
- [ ] Order tracking: CANCELADO badge --color-danger

Tests seguridad — regresion S11-10:
- [ ] test_cross_tenant_access: cliente A GET /portal/expedientes/{id_B}/ → 404
- [ ] test_same_404_semantics: inexistente y ajeno → mismo 404 body
- [ ] test_signed_url_expiry: URL expirada → 403/410
- [ ] test_ceo_only_not_exposed: response portal sin fob_unit/margin_pct/
       commission_pct/landed_cost/dai_amount
- [ ] test_portal_cannot_access_internal_route: B2B GET /api/expedientes/ → 401/403
- [ ] test_locale_switch_visibility: cambiar idioma no expone campos ocultos
- [ ] test_internal_toggle_not_in_portal: portal no expone campo view_mode

Tests regresion:
- [ ] Brand Console S14: 4 tabs funcionales
- [ ] Client Console S14: 7 tabs funcionales
- [ ] State machine S11: tests sin modificacion
- [ ] Acordeon S10 funciona

Sprint 15 DONE solo si:
  python manage.py test && bandit -ll backend/ &&
  npm run lint && npm run typecheck && npm run test
  + smoke Brand Console S14 + smoke Client Console S14
  + CI green en main

---

## Dependencias internas

```
S15-00 (Gate) ─────────────────────────────── prerequisito duro
     │
     ├── S15-01 (Shipment Detail + CreditBar) ── P0
     │       │ crea <CreditBar> reutilizable
     │       ├── S15-02 (Brand Console +2 tabs) ─ P1 ─┐
     │       ├── S15-03 (Credit Aging CEO) ────────── P1 ─┤ paralelos
     │       ├── S15-04 (Portal Login+Onboarding) ── P1 ─┤
     │       │       └── S15-05 (Order Tracking) ─── P1 ─┘
     │       └── S15-06 (Dashboard) ── condicional P2
     │
     └── S15-07 (Tests) ── despues de todo
```

---

## Excluido explicitamente

| Feature                   | Razon              | Cuando       |
|---------------------------|--------------------|--------------|
| Supplier Console          | Sprint 16          | Post-S15     |
| Backend nuevo             | S15 consume S14    | —            |
| ranawalk.com              | Post-MVP           | RW site      |
| Dark mode                 | Post-MVP           | Stitch #2    |
| Tracking tiempo real      | Post-MVP           | Carrier API  |
| Distributor Portal        | Post-MVP           | UX-08        |
| AI Assistant sidebar      | S16+               | UX-04        |
| Mobile Pipeline Kanban    | S16+               | UX-15        |
| Seed Tecmater WorkflowPolicy| S16              | Datos reales |

---

## Criterio Sprint 15 DONE

### Obligatorio (P0)
1. <CreditBar> con contrato completo C7
2. Shipment Detail CEO: CreditBar + toggle C6 + badges C11
3. Timeline con CANONICAL_STATE_ORDER, CANCELADO badge lateral
4. CI verde: lint + typecheck + unit + security negative tests

### Recomendado (P1)
5. Brand Console tabs Pricing + Operations (S14 tabs 1-4 intactos)
6. Credit & Aging CEO: aging table + riskLevel C9 + acciones CEO
7. Portal login glassmorphism C12 + selector idioma pre-auth
8. Portal Order Tracking: labels i18n C8 + signed URLs

### Deseable (P2)
9. Dashboard Kanban cards — 7 campos exactos
10. Urgent Actions — criterios operativos definidos

---

Stamp: DRAFT v1.2 — Arquitecto (Claude Sonnet 4.6) — 2026-03-23

Changelog:
- v1.0 (2026-03-23): Compilacion inicial. Sprints 12-14 DONE.
- v1.1 (2026-03-23): Fixes auditoria R1 (6.9/10).
  +C5 CANONICAL_STATE_ORDER tipado
  +C6 matriz visibilidad campo x tier
  +C7 contrato CreditBar con props y formulas
  +C8 tabla i18n 8 estados
  +C9 formula riskLevel cliente
  +C10 aging buckets operativos
  +C11 taxonomia artefactos con visibility
  +C12 spec glassmorphism verificable con tokens exactos
  +S15-00 gate con curl verificables
  +archivos impactados por item
  +criterio DONE Sprint 15 como condicion CI explicita
- v1.2 (2026-03-23): Fixes auditoria R2 (9.2/10).
  H1: rgba() → tokens CSS nuevos (--surface-glass-*, --timeline-pulse-*)
      declarados en C1; 0 hex/rgba inline en componentes
  H2: S15-00 + 5 write endpoints verificados (pricelists, freeze, credit-policy,
      contacts, preferences); protocolo de desbloqueo si falta endpoint
  H3: routing /{lang}/portal/onboarding normalizado; localStorage solo preferencia,
      [lang] segment como fuente de verdad del routing
  H4: S15-06 + endpoints fuente Kanban y Urgent Actions con shapes esperados;
      fallback explicit si endpoint 404
  H5: ART-06/ART-08 renderizados segun artifact.visibility de API; CEO-15 es
      decision backend, no logica frontend
  H6: Tab Operations shape completo del payload workflow-policy; columns extraidas
      del payload (no hardcodeadas C1-C22)
