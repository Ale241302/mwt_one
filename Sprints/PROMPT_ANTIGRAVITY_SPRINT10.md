# MWT ONE — Sprint 10 · Antigravity Execution Prompt

## STOP — Read this first

You are implementing a sprint for an existing codebase. The codebase already has:
- A state machine with 8 canonical states (FROZEN — do NOT modify or recreate)
- A design system in globals.css with CSS variables and utility classes
- Reusable components: FormModal.tsx, ConfirmDialog.tsx
- A constants file: states.ts with all state definitions

**Your job is to USE these existing assets, not replace them.**

---

## HARD RULES (violation = rejected sprint)

### RULE 1: NO parallel state machine
```
❌ WRONG: const TIMELINE_STATES = ["REGISTRO", "PRODUCCION", ...]
❌ WRONG: const STATES = { DESTINO: "...", FACTURADO: "..." }
❌ WRONG: type ArtifactType = "OC" | "PROFORMA" | "BL"

✅ RIGHT: import { CANONICAL_STATES, STATE_LABELS, STATE_BADGE_CLASSES, PIPELINE_STATES } from "@/constants/states"
```
The 8 canonical states are: REGISTRO, PRODUCCION, PREPARACION, DESPACHO, TRANSITO, EN_DESTINO, CERRADO, CANCELADO. These are defined in `frontend/src/constants/states.ts`. Import them. Never redefine them.

### RULE 2: NO custom modals
```
❌ WRONG: Creating ArtifactFormDrawer, InvoiceModal, RegisterCostDrawer
❌ WRONG: Building modal shell with overlay + container from scratch

✅ RIGHT: import FormModal from "@/components/ui/FormModal"
✅ RIGHT: import ConfirmDialog from "@/components/ui/ConfirmDialog"
```
FormModal already handles: Escape key, focus management, aria-modal, aria-labelledby, overlay click-to-close.

### RULE 3: NO hex colors in TSX
```
❌ WRONG: style={{ color: "#DC2626" }}
❌ WRONG: className="bg-[#F1F5F9] text-[#475569]"

✅ RIGHT: style={{ color: "var(--critical)" }}
✅ RIGHT: className="badge badge-critical"
```
All colors are CSS variables in globals.css. Use the design system classes: .badge-*, .btn-*, .card, .timeline-dot-*, etc.

### RULE 4: NO frontend gate logic
```
❌ WRONG: Computing which artifacts are required for advance in the React component
✅ RIGHT: Reading required_to_advance from the API response and rendering it
```

### RULE 5: Restore Sprint 7, don't reinvent
Sprint 7 already built artifact forms for ART-01, 02, 05, 06, 07, 08, 09. Find them in the codebase and wrap them in FormModal. Don't rebuild from scratch.

---

## Project context

**Stack:** Next.js 14 App Router, TypeScript, Tailwind CSS, Django REST Framework, PostgreSQL, JWT auth
**Repo:** https://github.com/Ale241302/mwt_one
**Route structure:** `frontend/src/app/[lang]/(mwt)/(dashboard)/...`
**URL pattern:** `/{lang}/dashboard/...`

**Existing components to reuse:**
- `frontend/src/components/ui/FormModal.tsx` — modal shell
- `frontend/src/components/ui/ConfirmDialog.tsx` — destructive action confirmation
- `frontend/src/constants/states.ts` — CANONICAL_STATES, STATE_LABELS, STATE_BADGE_CLASSES, PIPELINE_STATES
- `frontend/src/app/globals.css` — full design system

---

## Tasks — execute in order

### PHASE 0: CRUD carry-over (do this first)

**Task 1: Users Edit + Delete**
- File: `frontend/src/app/[lang]/(mwt)/(dashboard)/usuarios/page.tsx`
- Add Edit (FormModal) + Delete (ConfirmDialog) — same pattern as nodos/page.tsx
- Backend endpoints: PUT/DELETE `/api/admin/users/{id}/` — create if missing
- Guard: don't allow deleting last admin

**Task 2: Transfers Edit + Delete**
- File: `frontend/src/app/[lang]/(mwt)/(dashboard)/transfers/page.tsx`
- Add Edit (FormModal) + Delete (ConfirmDialog)
- Backend endpoints: PUT/DELETE `/api/transfers/{id}/` — create if missing

### PHASE 1: Workflow (core — most important)

**Task 3: Expediente detail with accordion** (REWRITE)
- File: `frontend/src/app/[lang]/(mwt)/(dashboard)/expedientes/[id]/page.tsx`

Build this page top to bottom:

**3A. Header:** Ref (.mono) + badge state (STATE_BADGE_CLASSES) + BLOQUEADO badge if is_blocked. If CANCELADO: show .badge-critical "CANCELADO" as lateral badge.

**3B. Metadata row:** Client, Brand, Mode (B/C/FULL), Freight, Transport, Dispatch

**3C. Timeline:** Use existing CSS classes from globals.css:
- .timeline, .timeline-node
- .timeline-dot-completed (mint + check), .timeline-dot-active (navy + pulse), .timeline-dot-future (dashed)
- .timeline-line-completed, .timeline-line-active, .timeline-line-future
- 7 nodes: REGISTRO → PRODUCCION → PREPARACION → DESPACHO → TRANSITO → EN_DESTINO → CERRADO
- CANCELADO is NOT a timeline node

**3D. Accordion:** One collapsible section per state. Use `<details>`/`<summary>` or button with aria-expanded.
- Completed states: collapsed, green badge "X/X completos"
- Active state (= expediente.status): expanded, shows artifacts + actions
- Future states: collapsed, grey badge "Pendiente"
- CANCELADO: expand last reached state, disable ALL mutative actions, visual-only

**3D1. Artifacts per state** (FROZEN — copy exactly):

| State | Artifacts |
|-------|----------|
| REGISTRO | ART-01 OC, ART-02 Proforma, ART-03 Decisión B/C, ART-04 SAP |
| PRODUCCION | (none) |
| PREPARACION | ART-05 AWB/BL, ART-06 Cotización flete, ART-07 Aprobación, ART-08 Customs (*) |
| DESPACHO | (none) |
| TRANSITO | (none) |
| EN_DESTINO | ART-09 Factura MWT, ART-10 Comisión (**) |

(*) ART-08 only if dispatch_mode=mwt — don't render otherwise
(**) ART-10 only if mode=COMISION — don't render otherwise

**3D2. Artifact status rendering:**
- done: green check, var(--success-bg) background
- pending (next in queue): blue var(--info-bg), "Registrar" button
- blocked: grey lock, "Requiere ART-XX + ART-YY" text

**3D3. Blocking invariants (implement these functions):**
```typescript
function shouldRender(type: string, exp: Expediente): boolean {
  if (type === "ART-08") return exp.dispatch_mode === "mwt";
  if (type === "ART-10") return exp.mode === "COMISION";
  return true;
}

function canRegister(type: string, exp: Expediente, artifacts: Artifact[]): boolean {
  const done = (t: string) => artifacts.some(a => a.artifact_type === t && a.status === "COMPLETED");
  if (type === "ART-07") return done("ART-05") && done("ART-06");
  if (type === "ART-08") return done("ART-05") && done("ART-06");
  if (type === "ART-09") return exp.status === "EN_DESTINO";
  if (type === "ART-10") return exp.status === "EN_DESTINO" && exp.mode === "COMISION";
  return true;
}

function blockReason(type: string, exp: Expediente, artifacts: Artifact[]): string | null {
  const done = (t: string) => artifacts.some(a => a.artifact_type === t && a.status === "COMPLETED");
  if (type === "ART-07" && !(done("ART-05") && done("ART-06"))) return "Requiere ART-05 + ART-06";
  if (type === "ART-08" && !(done("ART-05") && done("ART-06"))) return "Requiere ART-05 + ART-06";
  if (type === "ART-09" && exp.status !== "EN_DESTINO") return "Solo en EN_DESTINO";
  if (type === "ART-10" && exp.mode !== "COMISION") return "Solo modo COMISION";
  return null;
}
```

**3D4. Advance buttons (states without artifacts):**

| Current state | Button label | Endpoint | Condition |
|--------------|-------------|----------|-----------|
| PRODUCCION | "Confirmar producción completa" | POST /api/expedientes/{id}/commands/confirm-production-complete/ | — |
| DESPACHO | "Confirmar salida de carga" | POST /api/expedientes/{id}/commands/confirm-shipment-departed/ | — |
| TRANSITO | "Confirmar llegada a destino" | POST /api/expedientes/{id}/commands/confirm-shipment-arrived/ | — |
| EN_DESTINO | "Cerrar expediente" | POST /api/expedientes/{id}/commands/close-expediente/ | ART-09 COMPLETED |

IMPORTANT: REGISTRO and PREPARACION do NOT have advance buttons. Their transitions happen via the last required artifact command (C5 for REGISTRO, C10 for PREPARACION).

**3E. Gate message:** Read `required_to_advance` from GET /api/ui/expedientes/{id}/.
- If missing = []: show "Listo para avanzar" (green) + advance button (for PRODUCCION/DESPACHO/TRANSITO/EN_DESTINO only)
- If missing has items: show "Para avanzar a [next]: completar [list]" (yellow, .badge-warning bg)
- REGISTRO/PREPARACION: no advance button even when ready — transition via artifact command

**3F. Costs section** (below accordion, fixed):
- Table: type, description, phase, amount (.cell-money), visibility
- Toggle "Vista Interna" / "Vista Cliente"
- Button "+ Registrar Costo" — HIDDEN in CERRADO and CANCELADO
- Endpoint: GET /api/expedientes/{id}/costs/

**3G. Ops actions** (inside active state accordion):
- Bloquear/Desbloquear (C17/C18)
- Registrar Costo (C15) — not in CERRADO/CANCELADO
- Registrar Pago (C21)
- Cancelar (C16) — only REGISTRO/PRODUCCION/PREPARACION

**New components to create:**
- `frontend/src/components/expediente/ExpedienteAccordion.tsx`
- `frontend/src/components/expediente/ArtifactRow.tsx`
- `frontend/src/components/expediente/GateMessage.tsx`
- `frontend/src/components/expediente/CostTable.tsx`

---

**Task 4: Artifact modals (10 forms)**

Create `frontend/src/components/expediente/ArtifactModal.tsx` — wrapper that uses FormModal and renders correct form per artifact type.

| Artifact | Fields | Content-Type | Endpoint |
|----------|--------|-------------|----------|
| ART-01 | file (binary), items [{sku, qty, price}] | multipart/form-data | POST /api/expedientes/{id}/commands/register-oc/ |
| ART-02 | lines [{product, qty, price}], total, currency | application/json | POST /api/expedientes/{id}/commands/create-proforma/ |
| ART-03 | mode_decision: "COMISION" \| "FULL" | application/json | POST /api/expedientes/{id}/commands/decide-mode/ |
| ART-04 | sap_id, production_date | application/json | POST /api/expedientes/{id}/commands/register-sap/ |
| ART-05 | type, carrier, origin, dest, tracking, itinerary[] | application/json | POST /api/expedientes/{id}/commands/register-shipment/ |
| ART-06 | amount, currency, freight_mode | application/json | POST /api/expedientes/{id}/commands/register-freight/ |
| ART-07 | approved_by, approved_at | application/json | POST /api/expedientes/{id}/commands/approve-dispatch/ |
| ART-08 | ncm[], dai_percent, permits[] | application/json | POST /api/expedientes/{id}/commands/register-customs/ |
| ART-09 | total_client_view, currency | application/json | POST /api/expedientes/{id}/commands/issue-invoice/ |
| ART-10 | commission_total, currency, beneficiary | application/json | POST /api/expedientes/{id}/commands/issue-commission-invoice/ |

Backend: create C22 endpoint for ART-10 if it doesn't exist.

After submit: close modal → refetch expediente data → show toast success/error.

---

**Task 5: Dashboard improvements**

Backend first: add `by_status` and `next_actions` to GET /api/ui/dashboard/ response.

Frontend (`frontend/src/app/[lang]/(mwt)/(dashboard)/page.tsx`):
- Mini-pipeline bar: 6 segments (PIPELINE_STATES from states.ts), each with STATE_LABELS + count from by_status. Click navigates to pipeline filtered.
- "Próximas acciones": 3 cards from next_actions. Ref (.mono), client, badge, action, "Ir" button.

---

### PHASE 2: Security (parallel)

**Task 6: Security hardening**
- Nginx: `limit_req_zone $binary_remote_addr zone=api_rate:10m rate=20r/m;` + `burst=20 nodelay`
- Django: `DEFAULT_THROTTLE_RATES = { 'user': '120/min', 'anon': '30/min' }`
- Secrets: run `gitleaks detect --source=.` — must be 0 findings
- Redis: `requirepass` in docker-compose. Verify: `redis-cli ping` without auth → NOAUTH
- JWT: ACCESS=15min, REFRESH=7days, ROTATE=True, BLACKLIST_AFTER_ROTATION=True

### PHASE 3: Knowledge

**Task 7: Fix knowledge endpoint**
- Verify mwt-knowledge container running
- Verify proxy URL: http://mwt-knowledge:8001
- Verify Anthropic API key in env
- CREATE EXTENSION IF NOT EXISTS vector;
- Load .md files into pgvector (exclude CEO-ONLY files)
- Verify: /api/knowledge/ask/?q=¿Qué es un expediente? → 200 with coherent answer

---

## Verification checklist (run after all tasks)

- [ ] states.ts is the ONLY source of state definitions (grep for duplicates)
- [ ] FormModal.tsx is used for ALL form modals (no custom drawers)
- [ ] No hex colors in .tsx files: `grep -r "#[0-9A-Fa-f]\{6\}" frontend/src/app/ frontend/src/components/`
- [ ] ART-08 hidden when dispatch_mode=client
- [ ] ART-10 hidden when mode=FULL, visible when mode=COMISION
- [ ] CANCELADO is badge, not timeline node
- [ ] Advance buttons only in PRODUCCION/DESPACHO/TRANSITO/EN_DESTINO
- [ ] C15 button hidden in CERRADO/CANCELADO
- [ ] All inputs have htmlFor/id
- [ ] All icon buttons have aria-label
