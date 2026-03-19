# MWT ONE — Sprint 11 · Antigravity Execution Prompt

## STOP — Read this first

Sprint 11 is primarily a CLEANUP sprint. You are fixing technical debt in an existing codebase, not building new features (those come in Phase 1, only after cleanup is done).

The codebase has problems from previous sprints where AI agents created parallel implementations without removing old ones. Your job is to REMOVE the old, CENTRALIZE the sources of truth, and VERIFY with grep.

---

## HARD RULES (violation = rejected sprint)

### RULE 1: states.ts is the ONLY source of state definitions
```
CANONICAL FILE: frontend/src/constants/states.ts
DELETE: frontend/src/lib/constants/states.ts

❌ WRONG: const TERMINAL_STATUSES = ["CERRADO", "CANCELADO"] inside a component
❌ WRONG: const PHASES = ["REGISTRO", "PRODUCCION", ...] in RegisterCostDrawer
❌ WRONG: Any state string hardcoded in .tsx or .ts files outside constants/states.ts

✅ RIGHT: import { TERMINAL_STATES, CANCELLABLE_STATES, COST_PHASES } from "@/constants/states"
```

### RULE 2: LEGACY_STATE_DENYLIST — these states DO NOT EXIST
```
KILL LIST (eliminate everywhere — frontend, backend, fixtures, mocks, tests, seed data):
- ARCHIVADO
- EVALUACION_PREVIA
- FORMALIZACION
- QC
- ENTREGA

These are NOT valid states. The only valid states are the 8 in states.ts:
REGISTRO, PRODUCCION, PREPARACION, DESPACHO, TRANSITO, EN_DESTINO, CERRADO, CANCELADO
```

### RULE 3: ONE dashboard route tree — delete the other
```
The codebase has TWO route trees:
- frontend/src/app/[lang]/dashboard/...
- frontend/src/app/[lang]/(mwt)/(dashboard)/...

CHECK FIRST: Look at frontend/src/app/[lang]/layout.tsx and frontend/src/middleware.ts
The active tree is the one referenced by layout/middleware. DELETE THE OTHER.

❌ WRONG: Keeping both
❌ WRONG: Creating new pages in the legacy tree
✅ RIGHT: Delete legacy tree, keep only active tree
```

### RULE 4: Zero hex colors in TSX
```
❌ WRONG: style={{ color: "#DC2626" }}
❌ WRONG: className="bg-[#F1F5F9] text-[#475569]"
❌ WRONG: const colors = { success: "#0E8A6D" }

✅ RIGHT: style={{ color: "var(--critical)" }}
✅ RIGHT: className="badge badge-critical"
✅ RIGHT: Use STATE_BADGE_CLASSES from states.ts for state colors
```

### RULE 5: Phase 1 BLOCKED until Phase 0 is DONE
```
DO NOT start S11-10 (Portal B2B) or S11-11 (Products) until ALL of S11-01 through S11-09 are complete
AND regression tests pass (pipeline, accordion, CRUD).
```

---

## Project context

**Stack:** Next.js 14 App Router, TypeScript, Tailwind CSS, Django REST Framework, PostgreSQL, JWT auth
**Repo:** https://github.com/Ale241302/mwt_one
**Design system:** frontend/src/app/globals.css (CSS variables, utility classes)
**Reusable components:** FormModal.tsx, ConfirmDialog.tsx in frontend/src/components/ui/

---

## PHASE 0 — Cleanup (mandatory, do first)

### Task 1: Remove ARCHIVADO from backend (S11-01)
```bash
# Check if any expediente has this status
python manage.py shell -c "from apps.expedientes.models import Expediente; print(Expediente.objects.filter(status='ARCHIVADO').count())"
```
- If count > 0: create data migration to change status to CERRADO
- Remove ARCHIVADO from `backend/apps/expedientes/enums.py`
- Verify: `grep -rn "ARCHIVADO" backend/ --include="*.py" | grep -v migrations | grep -v __pycache__` → 0 results

### Task 2: Kill legacy states repo-wide (S11-02)
```bash
# Find all occurrences
grep -rn "ARCHIVADO\|EVALUACION_PREVIA\|FORMALIZACION\|\bQC\b\|ENTREGA" frontend/src/ backend/ --include="*.tsx" --include="*.ts" --include="*.py" | grep -v node_modules | grep -v __pycache__ | grep -v migrations
```
Delete every occurrence. Replace state-color mappings with STATE_BADGE_CLASSES from states.ts.

### Task 3: Centralize state strings (S11-03)

Add these exports to `frontend/src/constants/states.ts`:
```typescript
export const TERMINAL_STATES = ["CERRADO", "CANCELADO"] as const;
export const CANCELLABLE_STATES = ["REGISTRO", "PRODUCCION", "PREPARACION"] as const;
export const COST_PHASES = CANONICAL_STATES.filter(s => !["CERRADO", "CANCELADO"].includes(s));
```

Then replace local arrays in these files:
- `frontend/src/components/expediente/PipelineActionsPanel.tsx` — TERMINAL_STATUSES array
- `frontend/src/components/modals/CancelExpedienteModal.tsx` — CANCELLABLE_STATUSES
- `frontend/src/components/modals/RegisterCostDrawer.tsx` — PHASES array
- `frontend/src/components/ui/StateBadge.tsx` — color mapping per state
- `frontend/src/components/ui/ExpedienteTimeline.tsx` — state filter logic

Verify ALL 8 states:
```bash
grep -rn '"REGISTRO"\|"PRODUCCION"\|"PREPARACION"\|"DESPACHO"\|"TRANSITO"\|"EN_DESTINO"\|"CERRADO"\|"CANCELADO"' frontend/src/ --include="*.tsx" --include="*.ts" | grep -v node_modules | grep -v "constants/states"
```
Result must be 0.

### Task 4: Delete duplicate route tree (S11-04)

1. Read `frontend/src/app/[lang]/layout.tsx` and `frontend/src/middleware.ts`
2. Determine which route tree is active
3. Delete the other one entirely
4. Verify all routes still work

The 5 duplicated pairs:
```
frontend/src/app/[lang]/dashboard/expedientes/page.tsx  vs  frontend/src/app/[lang]/(mwt)/(dashboard)/expedientes/page.tsx
frontend/src/app/[lang]/dashboard/brands/page.tsx       vs  frontend/src/app/[lang]/(mwt)/(dashboard)/brands/page.tsx
frontend/src/app/[lang]/dashboard/clientes/page.tsx     vs  frontend/src/app/[lang]/(mwt)/(dashboard)/clientes/page.tsx
frontend/src/app/[lang]/dashboard/nodos/page.tsx        vs  frontend/src/app/[lang]/(mwt)/(dashboard)/nodos/page.tsx
frontend/src/app/[lang]/dashboard/pipeline/page.tsx     vs  frontend/src/app/[lang]/(mwt)/(dashboard)/pipeline/page.tsx
```

### Task 5: Delete duplicate states.ts (S11-05)
- Keep: `frontend/src/constants/states.ts`
- Delete: `frontend/src/lib/constants/states.ts`
- Redirect ALL imports to `@/constants/states`
- Verify: `grep -rn "lib/constants/states" frontend/src/ --include="*.tsx" --include="*.ts" | grep -v node_modules` → 0

### Task 6: Migrate hex colors to CSS variables (S11-06)

Files to fix:
- `frontend/src/components/ui/StateBadge.tsx` — 8 color pairs → use .badge-* classes from design system
- `frontend/src/app/[lang]/(mwt)/(dashboard)/transfers/page.tsx` — 6 color pairs → badge classes
- `frontend/src/components/ui/ExpedienteTimeline.tsx` — #75CBB3, #013A57 → .timeline-dot-* classes
- Rana Walk product pages (bison, goliath, leopard, orbis, velox) — product brand colors

Verify:
```bash
grep -rn '#[0-9A-Fa-f]\{6\}' frontend/src/app/ frontend/src/components/ --include="*.tsx"
# Must be 0 results

grep -rn 'bg-\[#\|text-\[#\|border-\[#' frontend/src/ --include="*.tsx" | grep -v node_modules
# Must be 0 results
```

### Task 7: Accessibility fixes (S11-07)

**(A)** Add id to all inputs + htmlFor to labels. Focus on:
- `frontend/src/components/modals/ArtifactFormDrawer.tsx`

**(B)** Add aria-label to icon-only buttons (34 found in audit)

**(C)** Add to these drawers: role="dialog", aria-modal="true", Escape handler:
- `frontend/src/components/modals/ArtifactFormDrawer.tsx`
- `frontend/src/components/modals/RegisterCostDrawer.tsx`
- `frontend/src/components/modals/RegisterPaymentDrawer.tsx`

**(D)** Install eslint-plugin-jsx-a11y:
```bash
npm install --save-dev eslint-plugin-jsx-a11y
```
Add to ESLint config as warning level.

### Task 8: Tests (S11-08)

**(A)** Backend — expand `backend/apps/expedientes/tests/test_transitions.py`:
- Parametric test: all 22 commands × invalid states → expect error
- Minimum: C13 fails if status ≠ EN_DESTINO, C16 fails in CERRADO/CANCELADO, C10 fails without ART-05+06

**(B)** Frontend — create test files:
- `frontend/src/app/[lang]/(mwt)/(dashboard)/brands/__tests__/page.test.tsx`
- `frontend/src/app/[lang]/(mwt)/(dashboard)/clientes/__tests__/page.test.tsx`
- `frontend/src/app/[lang]/(mwt)/(dashboard)/nodos/__tests__/page.test.tsx`
(Adjust paths to match surviving route tree from Task 4)

**(C)** Playwright — replace hardcoded URL:
```bash
grep -rn "consola.mwt.one" frontend/ --include="*.ts"
```
Replace with `process.env.BASE_URL || "http://localhost:3000"`

### Task 9: Security fixes (S11-09)

**(A)** SQL audit in knowledge service:
```bash
grep -rn 'f".*SELECT\|f".*INSERT\|f".*UPDATE\|\.format(.*SELECT\|+ "SELECT' backend/ --include="*.py" | grep -v migrations | grep -v __pycache__
```
Fix any SQL injection vectors: use ORM or text() with :bind parameters.
Test: try query with `'; DROP TABLE --` input → must not execute.

**(B)** Fix serializers:
```bash
grep -rn 'fields.*"__all__"' backend/ --include="*.py"
```
Replace with explicit field lists in:
- `backend/apps/liquidations/serializers.py`
- `backend/apps/transfers/serializers.py`

---

## PHASE 1 — Features (ONLY after Phase 0 is DONE + regression green)

### Task 10: Portal B2B (S11-10)

**REQUIRES CEO decisions first:**
- Which artifacts are visible to clients?
- Which transitions generate notifications?
- Signed URLs before exposing documents

**Create files:**
- `backend/apps/portal/views.py`, `serializers.py`, `urls.py`
- Frontend: `portal/page.tsx`, `portal/expedientes/page.tsx`, `portal/expedientes/[id]/page.tsx` (inside surviving route tree)
- Tests: `backend/apps/portal/tests/test_tenant_isolation.py`

**Security (non-negotiable):**
- ClientScopedManager: `for_user(user)`, NEVER `.all()`
- "Not found" and "no access" return SAME 404
- Documents via signed URLs (30min expiry)
- Knowledge /ask/ scoped to PUBLIC + PARTNER_B2B only

### Task 11: Products module (S11-11)

Create `productos/page.tsx` inside surviving route tree (from Task 4).
- CRUD: name, SKU base, brand (FK), category, description
- Use FormModal + ConfirmDialog
- Endpoints: GET/POST /api/productos/, PUT/DELETE /api/productos/{id}/
- Update Sidebar with link

---

## Verification checklist (run after ALL tasks)

```bash
# State machine clean
grep -rn "ARCHIVADO" backend/ --include="*.py" | grep -v migrations | grep -v __pycache__
# → 0

grep -rn "ARCHIVADO\|EVALUACION_PREVIA\|FORMALIZACION\|\bQC\b\|ENTREGA" frontend/src/ backend/ --include="*.tsx" --include="*.ts" --include="*.py" | grep -v node_modules | grep -v __pycache__ | grep -v migrations
# → 0

grep -rn '"REGISTRO"\|"PRODUCCION"\|"PREPARACION"\|"DESPACHO"\|"TRANSITO"\|"EN_DESTINO"\|"CERRADO"\|"CANCELADO"' frontend/src/ --include="*.tsx" --include="*.ts" | grep -v node_modules | grep -v "constants/states"
# → 0

# Only 1 states.ts
grep -rn "lib/constants/states" frontend/src/ --include="*.tsx" --include="*.ts" | grep -v node_modules
# → 0

# Only 1 dashboard route tree
ls frontend/src/app/\[lang\]/dashboard/ 2>/dev/null && echo "LEGACY EXISTS - DELETE IT"

# Zero hex in TSX
grep -rn '#[0-9A-Fa-f]\{6\}' frontend/src/app/ frontend/src/components/ --include="*.tsx"
# → 0

# Zero fields="__all__"
grep -rn 'fields.*"__all__"' backend/ --include="*.py" | grep -v __pycache__
# → 0

# Playwright not pointing to production
grep -rn "consola.mwt.one" frontend/ --include="*.ts"
# → 0
```
