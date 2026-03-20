# Sprint 12 — Guía de implementación para Alejandro

## Qué es esto
Refactorización backend (services.py monolítico → módulos), CI/CD, hooks frontend, y módulos nuevos (Inventario, WhatsApp). Incluye carry-over de Sprint 11 si Portal B2B o Productos no se completaron.

## Estructura del sprint

| Fase | Items | Prioridad | Estimado |
|------|-------|-----------|----------|
| 0 | S12-01 a S12-06: Refactorización backend + cleanup | P0 obligatorio | 3-4 días |
| 1 | S12-07: CI/CD pipeline | P0 (paralelo a Fase 0) | 1 día |
| 2 | S12-08 a S12-12: Hooks frontend + features | P1-P2 | 4-5 días |
| QA | S12-13: Tests finales | P0 | 1 día |

**REGLA DURA:** No arrancar Fase 2 hasta que S12-01 a S12-06 estén DONE y los tests de state machine pasen sin modificación. S12-07 (CI/CD) puede correr en paralelo con Fase 0.

---

## Fase 0 — Refactorización backend obligatoria

### Bloque 1: Dividir el monolito (S12-01 a S12-03)

**S12-01: Dividir services.py en módulos**
1. Crear directorio `backend/apps/expedientes/services/`
2. Crear `__init__.py` que re-exporte los 22 símbolos
3. Mover funciones según esta asignación:

| Módulo | Commands |
|--------|----------|
| `create.py` | C1 |
| `commands_registro.py` | C2, C3, C4, C5 |
| `commands_produccion.py` | C6 |
| `commands_preparacion.py` | C7, C8, C9, C10 |
| `commands_transito.py` | C11, C12 |
| `commands_destino.py` | C13, C14, C22 |
| `financial.py` | C15, C21 |
| `exceptions.py` | C16, C17, C18 |
| `corrections.py` | C19, C20 |

4. Eliminar `services.py` original
5. Verificar: `pytest backend/apps/expedientes/tests/ -v` → mismos tests, mismos resultados
6. Verificar: ningún archivo supera 300 líneas

**S12-02: Consolidar services_sprint5.py**
1. Inventariar funciones en `services_sprint5.py` (312 líneas)
2. Mover cada función al módulo correcto en `services/`
3. Actualizar imports en todo el proyecto
4. Eliminar `services_sprint5.py`
5. Verificar: `grep -rn "services_sprint5" backend/ --include="*.py" | grep -v __pycache__ | grep -v migrations` → 0

**S12-03: Consolidar command views**
1. Crear `CommandDispatchView` con dict de 22 commands → funciones de services
2. Las URLs existentes NO cambian — solo el código detrás
3. Eliminar las 18+ clases APIView de 3 líneas
4. Verificar: `views.py` baja de 753 a ~200 líneas
5. Verificar: `pytest` → mismos tests pasan

### Bloque 2: API docs + estandarización (S12-04 a S12-05)

**S12-04: API documentation**
1. `pip install drf-spectacular`
2. Configurar en settings + agregar URLs `/api/schema/` y `/api/docs/`
3. Anotar serializers principales con `@extend_schema`
4. Verificar: `/api/docs/` muestra Swagger UI con todos los endpoints

**S12-05: Paginación + error responses**

**(A) Paginación — solo 3 vistas:**
- Crear `backend/core/pagination.py` con `StandardPagination` (page_size=25)
- Aplicar SOLO a: ExpedienteListView, TransferListView, LiquidationListView
- NO definir `DEFAULT_PAGINATION_CLASS` global
- El resto de endpoints (brands, clientes, nodos) siguen devolviendo lista plana

**(B) Error responses — envelope aditivo:**
- Crear `backend/core/exception_handler.py`
- El campo `errors` preserva el shape original de DRF
- Frontend existente sigue leyendo `errors` igual que antes
- Configurar en settings: `REST_FRAMEWORK['EXCEPTION_HANDLER']`

### Bloque 3: Limpieza menor (S12-06)

**(A)** Agregar `db_index=True` a: Expediente.status, .client, .brand, .created_at → crear migración

**(B)** Mover `fix_tests*.py` y `generate_brands_fixtures.py` a `backend/scripts/`

**(C)** Reemplazar console.log/error/warn por logger:
```typescript
// frontend/src/lib/logger.ts
const isDev = process.env.NODE_ENV === "development";
export const logger = {
  error: (...args: unknown[]) => isDev && console.error(...args),
  warn: (...args: unknown[]) => isDev && console.warn(...args),
};
```
Verificar: `grep -rn "console\.\(log\|error\|warn\)" frontend/src/ --include="*.tsx" --include="*.ts" | grep -v node_modules | grep -v logger.ts` → 0

---

## Fase 1 — CI/CD (paralelo a Fase 0)

### S12-07: Pipeline CI/CD

**CI (.github/workflows/ci.yml):**
- Python 3.11, Node 20
- Services: postgres:16, redis:7-alpine
- Backend: ruff check → bandit (solo HIGH+) → pytest
- Frontend: eslint → build → jest

**Deploy (.github/workflows/deploy.yml):**
- Trigger: push a main después de CI verde
- SSH → git pull → docker-compose up -d → migrate → healthcheck
- Si healthcheck falla: rollback al último commit bueno

**Secretos:** configurar en GitHub Settings > Secrets (SSH_HOST, SSH_USER, SSH_KEY). Nunca en YAML.

---

## Fase 2 — Frontend refactor + features (SOLO si Fase 0 está DONE + tests verdes)

### S12-08: Hooks useFetch / useCRUD
- Crear `frontend/src/hooks/useFetch.ts` y `useCRUD.ts`
- Deben soportar AMBOS formatos: lista plana y paginada DRF (auto-detect)
- Migrar al menos 3 páginas: brands, clientes, nodos
- Crear tests: `frontend/src/hooks/__tests__/useFetch.test.ts`

### S12-09: Consolidar modals/drawers
- Crear `DrawerShell.tsx` (Escape, aria-modal, focus, overlay)
- Crear `useFormSubmit(endpoint)` hook
- Migrar ArtifactFormDrawer, RegisterCostDrawer, RegisterPaymentDrawer
- Reducir código duplicado ≥50%

### S12-10: Carry-over Sprint 11 (si aplica)
**Solo si Portal B2B o Productos no se completaron en Sprint 11.**
- Prioridad P0 — completar antes de features nuevas
- Spec según LOTE_SM_SPRINT11 v2.1

### S12-11: Módulo Inventario
**Requiere:** Módulo Productos DONE (sea de Sprint 11 o carry-over)
- Crear `inventario/page.tsx` en el route tree activo
- CRUD: producto (FK), nodo (FK), cantidad, reservada, lote, fecha ingreso
- Vistas: por nodo y por producto
- Usar useFetch/useCRUD hooks
- FormModal + ConfirmDialog
- Endpoints: GET/POST /api/inventario/, PUT/DELETE /api/inventario/{id}/, GET by-node, GET by-product

### S12-12: WhatsApp Business API (setup inicial)
**Requiere:** Portal B2B DONE + Meta Business verificado por CEO
**Si Meta no está listo → se pasa a Sprint 13**
- Webhook: `POST /api/webhooks/whatsapp/`
- Modelo: WhatsAppMessage (log)
- Celery task: transición de estado → envío
- Consola CEO: tabla de mensajes enviados
- Si template Meta no aprobado: todo funciona en dry-run

---

## Lo que NO debes hacer

1. **NO modificar tests para que pasen** — si un test falla post-refactor, el refactor tiene un bug
2. **NO crear nuevas URLs públicas** — CommandDispatchView es consolidación interna
3. **NO poner paginación global** — solo las 3 vistas del allowlist
4. **NO cambiar el shape de response** — el envelope de errores es aditivo
5. **NO dejar services.py junto con services/** — uno u otro, no ambos
6. **NO hardcodear secretos** en workflows de GitHub Actions

## Tests post-deploy

**Refactorización:**
- [ ] `pytest backend/apps/expedientes/tests/` → todos pasan sin modificar tests
- [ ] `ls backend/apps/expedientes/services.py` → no existe
- [ ] `ls backend/apps/expedientes/services_sprint5.py` → no existe
- [ ] `wc -l backend/apps/expedientes/views.py` → ~200 líneas
- [ ] `/api/docs/` → Swagger UI funcional
- [ ] `services/__init__.py` exporta 22 símbolos

**Estandarización:**
- [ ] GET /api/expedientes/ → `{ count, next, previous, results }` (paginado)
- [ ] GET /api/brands/ → `[{...}]` (lista plana, sin paginar)
- [ ] Error 400 → `{ error, code, detail, errors }` con shape original en `errors`

**CI/CD:**
- [ ] Push a main dispara CI
- [ ] CI falla si lint o tests fallan
- [ ] Deploy tiene healthcheck + rollback

**Cleanup:**
- [ ] `grep console.log frontend/src/` → 0 (fuera de logger.ts)
- [ ] `ls backend/fix_tests*` → 0
- [ ] Índices en DB para status, client, brand, created_at

**Regresión:**
- [ ] Acordeón Sprint 10 funciona
- [ ] Pipeline, CRUD funciona
- [ ] Portal B2B funciona (si aplica de Sprint 11)

---

*Sprint 12 · MWT ONE · LOTE v2.1 · Score auditoría ChatGPT: R1 8.5 → R2 9.3 → R3 pendiente*
