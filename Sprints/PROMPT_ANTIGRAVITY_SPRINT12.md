# MWT ONE — Sprint 12 · Antigravity Execution Prompt

## STOP — Read this first

Sprint 12 is primarily a REFACTORING sprint. You are splitting monolithic files into modules, consolidating duplicated patterns, and adding CI/CD. The codebase must behave EXACTLY the same after refactoring — same inputs, same outputs, same API contracts.

Sprint 11 cleaned up state machine debt. Sprint 12 restructures the architecture for scale. If Sprint 11 left carry-over items (Portal B2B, Products), those are P0 in this sprint.

---

## HARD RULES (violation = rejected sprint)

### RULE 1: Tests are the safety net — they must NOT change
```
BEFORE refactoring any file:
  pytest backend/apps/expedientes/tests/ → capture passing count

AFTER refactoring:
  pytest backend/apps/expedientes/tests/ → same count, same results

❌ WRONG: Modifying a test to make it pass after refactor
❌ WRONG: Deleting a test that "doesn't apply anymore"
❌ WRONG: Skipping tests with @pytest.mark.skip

✅ RIGHT: Same tests, same results, zero modifications
```

### RULE 2: API contracts are FROZEN — same URLs, same shapes
```
The 22 command endpoints DO NOT change their:
- URL path
- HTTP method
- Request body shape
- Response body shape

CommandDispatchView is INTERNAL consolidation only.

❌ WRONG: Creating /api/expedientes/{id}/commands/{command_name}/ as a new public URL
❌ WRONG: Changing response shape from { detail: "..." } to { data: { detail: "..." } }
❌ WRONG: Adding required fields to any existing endpoint

✅ RIGHT: Same URLs, internally routed through CommandDispatchView
✅ RIGHT: Error envelope is ADDITIVE — original shape preserved in "errors" field
```

### RULE 3: services/__init__.py must re-export EVERYTHING
```
After splitting services.py into modules:

❌ WRONG: from apps.expedientes.services.create import create_expediente  (direct module import)
❌ WRONG: Missing any of the 22 command symbols in __init__.py
❌ WRONG: services.py still exists alongside services/ directory

✅ RIGHT: from apps.expedientes.services import create_expediente  (works via __init__.py)
✅ RIGHT: All 22 symbols listed in __init__.py
✅ RIGHT: services.py deleted, replaced by services/ directory
```

### RULE 4: No file in services/ exceeds 300 lines
```
❌ WRONG: services/commands_registro.py at 350 lines
✅ RIGHT: Split further if approaching 300
```

### RULE 5: Pagination is opt-in, not global
```
❌ WRONG: Setting DEFAULT_PAGINATION_CLASS in settings (breaks flat-list endpoints)
❌ WRONG: All endpoints suddenly returning { count, next, previous, results }

✅ RIGHT: Only allowlisted views use StandardPagination:
  - ExpedienteListView
  - TransferListView
  - LiquidationListView
✅ RIGHT: brands, clientes, nodos keep returning flat arrays
```

### RULE 6: Phase 2 features BLOCKED until Phase 0 refactor is DONE
```
DO NOT start S12-08 through S12-12 until ALL of S12-01 through S12-06 are complete
AND all state machine tests pass unchanged.

Exception: S12-07 (CI/CD) can run in parallel with Phase 0.
```

---

## Project context

**Stack:** Next.js 14 App Router, TypeScript, Tailwind CSS, Django REST Framework, PostgreSQL, JWT auth
**Repo:** https://github.com/Ale241302/mwt_one
**Design system:** frontend/src/app/globals.css (CSS variables, utility classes)
**Reusable components:** FormModal.tsx, ConfirmDialog.tsx in frontend/src/components/ui/
**State constants:** frontend/src/constants/states.ts (single source, cleaned in Sprint 11)

---

## PHASE 0 — Backend refactoring (mandatory, do first)

### Task 1: Split services.py into modules (S12-01)

Source: `backend/apps/expedientes/services.py` (1,371 lines)

Create directory structure:
```
backend/apps/expedientes/services/
├── __init__.py              ← re-exports ALL 22 symbols
├── create.py                ← C1 CreateExpediente
├── commands_registro.py     ← C2, C3, C4, C5
├── commands_produccion.py   ← C6
├── commands_preparacion.py  ← C7, C8, C9, C10
├── commands_transito.py     ← C11, C12
├── commands_destino.py      ← C13, C14, C22
├── financial.py             ← C15, C21
├── exceptions.py            ← C16, C17, C18
└── corrections.py           ← C19, C20
```

Verify:
```bash
# All 22 symbols accessible via package import
python -c "from apps.expedientes.services import create_expediente, register_oc, create_proforma, decide_mode_bc, register_sap, confirm_production, register_shipment, register_freight, register_customs, approve_dispatch, confirm_departed, confirm_arrived, issue_invoice, close_expediente, register_cost, cancel_expediente, block_expediente, unblock_expediente, supersede_artifact, void_artifact, register_payment, issue_commission; print('ALL 22 OK')"

# No file exceeds 300 lines
find backend/apps/expedientes/services/ -name "*.py" -exec wc -l {} + | sort -n

# Old monolith deleted
ls backend/apps/expedientes/services.py 2>/dev/null && echo "DELETE THIS" || echo "OK - gone"

# Tests pass unchanged
pytest backend/apps/expedientes/tests/ -v
```

### Task 2: Consolidate services_sprint5.py (S12-02)

Source: `backend/apps/expedientes/services_sprint5.py` (312 lines)

1. **FIRST:** Inventory all functions in services_sprint5.py
2. Map each function → target module in services/
3. Move functions to correct modules
4. Update imports throughout codebase
5. Delete services_sprint5.py

Verify:
```bash
ls backend/apps/expedientes/services_sprint5.py 2>/dev/null && echo "DELETE THIS" || echo "OK - gone"

# No broken imports
grep -rn "services_sprint5" backend/ --include="*.py" | grep -v __pycache__ | grep -v migrations
# → 0
```

### Task 3: Consolidate command views (S12-03)

Source: `backend/apps/expedientes/views.py` (753 lines, 18+ APIView classes)

Create CommandDispatchView:
```python
class CommandDispatchView(APIView):
    COMMANDS = {
        "register-oc": services.register_oc,
        "create-proforma": services.create_proforma,
        # ... all 22 commands
    }
    
    def post(self, request, expediente_id, command_name):
        handler = self.COMMANDS.get(command_name)
        if not handler:
            return Response({"detail": "Unknown command"}, status=404)
        return handler(request, expediente_id)
```

**CRITICAL:** Do NOT create new URL paths. The existing URLs stay. Internally they route through the dispatch.

Verify:
```bash
# views.py reduced
wc -l backend/apps/expedientes/views.py
# Should be ~200 lines (was 753)

# All 22 command URLs still respond
# Run existing API tests
pytest backend/apps/expedientes/tests/ -v

# No new paths created
grep -rn "urlpatterns" backend/apps/expedientes/urls.py
```

### Task 4: API documentation with drf-spectacular (S12-04)

```bash
pip install drf-spectacular
```

Add to settings, configure URLs for `/api/schema/` and `/api/docs/`.
Annotate main serializers with `@extend_schema`.

Verify: visit `/api/docs/` → Swagger UI shows all endpoints.

### Task 5: Standardize pagination + error responses (S12-05)

**(A) Pagination — opt-in only:**
```python
# backend/core/pagination.py
class StandardPagination(PageNumberPagination):
    page_size = 25
    page_size_query_param = 'page_size'
    max_page_size = 100
```

Allowlist (ONLY these views get pagination):
- ExpedienteListView
- TransferListView
- LiquidationListView

ALL other endpoints keep returning flat arrays.

**(B) Error responses — additive envelope:**
```python
# backend/core/exception_handler.py
def custom_exception_handler(exc, context):
    response = default_exception_handler(exc, context)
    if response:
        original = response.data
        response.data = {
            "error": True,
            "code": response.status_code,
            "detail": original.get("detail") if isinstance(original, dict) and "detail" in original else str(original),
            "errors": original,  # PRESERVE original DRF shape
        }
    return response
```

The `errors` field keeps the original shape. Frontend existing code reads `errors` the same way.

Verify:
```bash
# Pagination only on allowlisted endpoints
curl /api/expedientes/ | python -c "import sys,json; d=json.load(sys.stdin); assert 'results' in d"
curl /api/brands/ | python -c "import sys,json; d=json.load(sys.stdin); assert isinstance(d, list)"  # still flat

# Error envelope
curl -X POST /api/expedientes/999/commands/register-oc/ -H "Authorization: Bearer ..." | python -c "import sys,json; d=json.load(sys.stdin); assert 'error' in d and 'errors' in d"
```

### Task 6: Low-effort backlog cleanup (S12-06)

**(A)** Add `db_index=True` to: Expediente.status, .client, .brand, .created_at → create migration

**(B)** Move `fix_tests*.py` and `generate_brands_fixtures.py` to `backend/scripts/`

**(C)** Replace console.log/error/warn with logger:
```typescript
// frontend/src/lib/logger.ts
const isDev = process.env.NODE_ENV === "development";
export const logger = {
  error: (...args: unknown[]) => isDev && console.error(...args),
  warn: (...args: unknown[]) => isDev && console.warn(...args),
};
```

Verify:
```bash
# Indexes
grep -rn "db_index" backend/apps/expedientes/models.py
# → at least 4 fields

# Scripts moved
ls backend/fix_tests* backend/generate_* 2>/dev/null
# → 0

# Console cleaned
grep -rn "console\.\(log\|error\|warn\)" frontend/src/ --include="*.tsx" --include="*.ts" | grep -v node_modules | grep -v logger.ts
# → 0
```

---

## PHASE 1 — CI/CD (can run parallel to Phase 0)

### Task 7: CI/CD pipeline (S12-07)

Create `.github/workflows/ci.yml`:
- Python 3.11, Node 20
- Services: postgres:16, redis:7-alpine
- Backend: ruff check → bandit -ll → pytest
- Frontend: eslint → build → jest

Create `.github/workflows/deploy.yml`:
- Trigger: push to main (after CI green)
- SSH → git pull → docker-compose up -d → migrate → healthcheck
- Rollback if healthcheck fails: checkout last known good commit

**NEVER hardcode secrets in YAML.** Use GitHub Actions secrets.

---

## PHASE 2 — Frontend refactor + features (ONLY after Phase 0 DONE + tests green)

### Task 8: Create useFetch / useCRUD hooks (S12-08)

Create `frontend/src/hooks/useFetch.ts` and `useCRUD.ts`.

Must support BOTH formats:
- Flat array: `[{...}, {...}]`
- Paginated DRF: `{ count, next, previous, results: [{...}] }`

Auto-detect format. Migrate brands, clientes, nodos pages.

### Task 9: Consolidate modals/drawers (S12-09)

Create `DrawerShell.tsx` with: Escape handler, aria-modal, focus trap, overlay.
Create `useFormSubmit(endpoint)` hook for the change→submit→toast pattern.
Migrate ArtifactFormDrawer, RegisterCostDrawer, RegisterPaymentDrawer.

### Task 10: Sprint 11 carry-over (S12-10) — ONLY if S11-10/S11-11 not DONE

If Portal B2B or Products were not completed in Sprint 11, they are P0 here.
Spec: per LOTE_SM_SPRINT11 v2.1.

### Task 11: Inventory module (S12-11)

**Requires:** Products module DONE (S11-11 or S12-10).

Create `inventario/page.tsx`. Model:
```python
class InventoryEntry(models.Model):
    product = ForeignKey(Product, PROTECT)
    node = ForeignKey(Node, PROTECT)
    quantity = IntegerField(default=0)
    reserved = IntegerField(default=0)
    lot_number = CharField(max_length=50, blank=True)
    received_at = DateTimeField()
    unique_together = ('product', 'node', 'lot_number')
```

Views: by-node, by-product, CRUD. Use useFetch/useCRUD hooks.

### Task 12: WhatsApp Business API setup (S12-12)

**Requires:** Portal B2B DONE + Meta Business verification completed by CEO.
If Meta prerequisites not ready → skip, pass to Sprint 13.

Webhook: `POST /api/webhooks/whatsapp/`
Model: `WhatsAppMessage` (log)
Celery task: state transition → send notification
CEO console: message log table

---

## Verification checklist (run after ALL tasks)

```bash
# Refactoring integrity
pytest backend/apps/expedientes/tests/ -v
# → ALL tests pass with ZERO modifications to test files

# services.py gone, replaced by services/ directory
ls backend/apps/expedientes/services.py 2>/dev/null && echo "FAIL" || echo "OK"
ls backend/apps/expedientes/services/__init__.py && echo "OK" || echo "FAIL"

# services_sprint5.py gone
ls backend/apps/expedientes/services_sprint5.py 2>/dev/null && echo "FAIL" || echo "OK"

# No broken imports
grep -rn "services_sprint5" backend/ --include="*.py" | grep -v __pycache__ | grep -v migrations
# → 0

# views.py reduced
wc -l backend/apps/expedientes/views.py
# Should be ~200 lines

# API docs working
curl -f http://localhost:8000/api/docs/ > /dev/null && echo "OK" || echo "FAIL"

# Pagination only on allowlist
curl /api/brands/ | python -c "import sys,json; d=json.load(sys.stdin); assert isinstance(d, list), 'Should be flat array'"

# Error envelope
curl -X POST /api/expedientes/999/commands/invalid/ | python -c "import sys,json; d=json.load(sys.stdin); assert 'errors' in d"

# Console cleaned
grep -rn "console\.\(log\|error\|warn\)" frontend/src/ --include="*.tsx" --include="*.ts" | grep -v node_modules | grep -v logger.ts
# → 0

# CI pipeline
# Push to branch → verify GitHub Actions runs

# Scripts moved
ls backend/fix_tests* backend/generate_* 2>/dev/null
# → 0
```
