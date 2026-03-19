# LOTE_SM_SPRINT11 — Limpieza Pre-B2B + Portal B2B + Módulo Productos
status: DRAFT — aprobado ChatGPT 9.6/10 R2, pendiente aprobación CEO para freeze
visibility: INTERNAL
domain: Plataforma (IDX_PLATAFORMA)
version: 2.1
sprint: 11
priority: P0
agente_principal: AG-02 Backend + AG-03 Frontend (Alejandro)
depends_on: LOTE_SM_SPRINT10 (en ejecución)
refs: REPORTE_AUDIT_CODEBASE_20260318, ENT_OPS_STATE_MACHINE (FROZEN v1.2.2), ENT_PLAT_SEGURIDAD, ENT_GOB_PENDIENTES

---

## Objetivo Sprint 11

Limpiar deuda técnica detectada por Claude Code (50 observaciones, score 6.3/10) para que el codebase esté sano antes de abrir el canal B2B. Además, si el tiempo lo permite: Portal B2B (portal.mwt.one) y Módulo Productos (PLT-09).

**Estructura:** Fase 0 (limpieza obligatoria) → Fase 1 (features si hay tiempo) → Fase 2 (tests).

**Regla de escape:** Si Fase 0 toma más de lo esperado, Fase 1 (Portal B2B + Productos) se pasa a Sprint 12 completa. La limpieza no se sacrifica por features.

**Gate Fase 1:** No iniciar S11-10 ni S11-11 hasta que S11-01 a S11-09 estén DONE Y regresión mínima verde (pipeline, acordeón, CRUD de Nodos/Brands/Clientes). Sin excepción.

**Precondición:** Sprint 10 DONE — acordeón operativo, security hardening, knowledge funcional.

### Incluido

| # | Feature | Fuente | Prioridad |
|---|---------|--------|-----------|
| 1 | Eliminar ARCHIVADO del backend enum | DT-01 / OBS-001 | P0 |
| 2 | Eliminar estados legacy del frontend | DT-02 / OBS-002 | P0 |
| 3 | Centralizar 28 strings de estado → states.ts | DT-03 / OBS-003 | P0 |
| 4 | Eliminar rutas duplicadas (~1,300 LOC) | DT-04 / OBS-022 | P0 |
| 5 | Eliminar states.ts duplicado | DT-05 / OBS-004 | P0 |
| 6 | Migrar hex hardcodeados a CSS variables | DT-06 / OBS-026 | P1 |
| 7 | Accesibilidad: htmlFor/id + aria-label + drawers | DT-07/08/09 / OBS-028/029/030 | P1 |
| 8 | Tests: state machine completa + CRUD Sprint 9 + Playwright config | DT-10/11/12 / OBS-032/033/034 | P1 |
| 9 | Seguridad: raw SQL audit + serializers explícitos | DT-13/14 / OBS-009/010 | P0 |
| 10 | Portal B2B (portal.mwt.one) — vista cliente | CEO-15/16/20 | P2 (Fase 1) |
| 11 | Módulo Productos (PLT-09) | ENT_GOB_PENDIENTES | P2 (Fase 1) |
| 12 | Tests Sprint 11 | — | P0 |

### Excluido

| Feature | Razón | Cuándo |
|---------|-------|--------|
| PLT-10 Módulo Inventario | Depende de Productos | Sprint 12 |
| CEO-14 WhatsApp Business API | Canal B2B P2 | Sprint 12+ |
| Refactorización services.py 1,371 líneas (DT-15) | Alto esfuerzo, no bloquea B2B | Sprint 12 |
| Command views collapse (DT-16) | Medio esfuerzo, cosmético | Sprint 12 |
| Custom hooks CRUD (DT-17) | Medio esfuerzo | Sprint 12 |
| API documentation drf-spectacular (DT-19) | Medio esfuerzo | Sprint 12 |
| Consolidar modals duplicados (DT-18) | Sprint 10 ya migró a FormModal | Sprint 12 |

---

## Constraints obligatorios

### C1. State machine FROZEN v1.2.2
8 estados canónicos. ARCHIVADO no es uno de ellos — se elimina en este sprint.

### C2. Importar desde states.ts (un solo archivo)
Después de este sprint, `frontend/src/constants/states.ts` es el ÚNICO archivo de estados. El duplicado en `frontend/src/lib/constants/states.ts` se elimina. Todos los imports apuntan al canónico.

### C3. Cero hex en TSX
Al terminar este sprint, `grep -rn '#[0-9A-Fa-f]{6}' frontend/src/app/ frontend/src/components/ --include="*.tsx"` debe retornar 0 resultados.

### C4. Accesibilidad mínima
Al terminar: 0 inputs sin id, 0 botones icon-only sin aria-label, todos los drawers con aria-modal.

---

## Items

### FASE 0 — Limpieza obligatoria pre-B2B (estimado 3-4 días)

#### Item S11-01: Eliminar ARCHIVADO del backend
- **Agente:** AG-02 Backend
- **Archivo físico:** `backend/apps/expedientes/enums.py`
- **Qué hacer:**
  1. Verificar que ningún expediente en la DB tiene status=ARCHIVADO: `SELECT count(*) FROM expedientes_expediente WHERE status='ARCHIVADO';`
  2. Si hay expedientes con ARCHIVADO: migrarlos a CERRADO con migración de datos.
  3. Eliminar ARCHIVADO del enum ExpedienteStatus.
  4. Verificar que no hay código que referencie ARCHIVADO en backend.
- **Criterio de done:**
  - [ ] `grep -rn "ARCHIVADO" backend/ --include="*.py" | grep -v migrations | grep -v __pycache__` → 0 resultados
  - [ ] Backend arranca sin errores
  - [ ] Tests passing

#### Item S11-02: Eliminar estados legacy del frontend y backend
- **Agente:** AG-03 Frontend + AG-02 Backend
- **LEGACY_STATE_DENYLIST:** ARCHIVADO, EVALUACION_PREVIA, FORMALIZACION, QC, ENTREGA
- **Scope:** Repo completo — frontend, backend, fixtures, mocks, tests, seed data.
- **Archivo principal frontend:** `frontend/src/app/[lang]/(mwt)/(dashboard)/expedientes/page.tsx`
- **Qué hacer:**
  1. Ejecutar kill-list grep repo-wide:
     ```
     grep -rn "ARCHIVADO\|EVALUACION_PREVIA\|FORMALIZACION\|\bQC\b\|ENTREGA" frontend/src/ backend/ --include="*.tsx" --include="*.ts" --include="*.py" | grep -v node_modules | grep -v __pycache__ | grep -v migrations
     ```
  2. Eliminar cada ocurrencia: switch cases, enums, fixtures, mocks, seed data.
  3. Para ARCHIVADO en backend: ya resuelto por S11-01.
  4. Usar STATE_BADGE_CLASSES de states.ts para mapeos de colores.
- **Criterio de done:**
  - [ ] Kill-list grep repo-wide → 0 resultados (excluyendo migrations y este LOTE)

#### Item S11-03: Centralizar strings de estado hardcodeados
- **Agente:** AG-03 Frontend
- **Archivos afectados (6):**
  - `components/expediente/PipelineActionsPanel.tsx` — TERMINAL_STATUSES array
  - `components/modals/CancelExpedienteModal.tsx` — CANCELLABLE_STATUSES
  - `components/modals/RegisterCostDrawer.tsx` — PHASES array
  - `components/ui/StateBadge.tsx` — mapeo colores por estado
  - `components/ui/ExpedienteTimeline.tsx` — filtro por estado
  - Cualquier otro archivo detectado con grep
- **Qué hacer:**
  1. Agregar exports nuevos a `frontend/src/constants/states.ts`:
     ```
     export const TERMINAL_STATES = ["CERRADO", "CANCELADO"] as const;
     export const CANCELLABLE_STATES = ["REGISTRO", "PRODUCCION", "PREPARACION"] as const;
     export const COST_PHASES = CANONICAL_STATES.filter(s => !TERMINAL_STATES.includes(s));
     ```
  2. Reemplazar arrays locales por imports en los 6 archivos.
  3. StateBadge.tsx: usar STATE_BADGE_CLASSES importado, no mapeo local de colores.
- **Criterio de done:**
  - [ ] Grep all 8 states outside states.ts: `grep -rn '"REGISTRO"\|"PRODUCCION"\|"PREPARACION"\|"DESPACHO"\|"TRANSITO"\|"EN_DESTINO"\|"CERRADO"\|"CANCELADO"' frontend/src/ --include="*.tsx" --include="*.ts" | grep -v node_modules | grep -v "constants/states"` → 0 resultados
  - [ ] Grep derived arrays outside states.ts: `grep -rn "TERMINAL_STAT\|CANCELLABLE_STAT\|COST_PHASE\|PIPELINE_STATE" frontend/src/ --include="*.tsx" --include="*.ts" | grep -v node_modules | grep -v "constants/states"` → solo imports, no definiciones locales

#### Item S11-04: Eliminar rutas duplicadas
- **Agente:** AG-03 Frontend
- **Qué hacer:**
  1. **VERIFICAR PRIMERO:** ¿Cuál route group está activo? Revisar `frontend/src/app/[lang]/layout.tsx` y `frontend/src/middleware.ts` para determinar si la app usa `/[lang]/dashboard/` o `/[lang]/(mwt)/(dashboard)/`.
  2. La ruta activa es la que el layout y middleware referencian. La otra es legacy.
  3. Eliminar la carpeta legacy completa.
  4. Verificar que la consola sigue funcionando en todas las rutas.
- **5 pares duplicados detectados (paths exactos):**
  - `frontend/src/app/[lang]/dashboard/expedientes/page.tsx` (321 líneas) vs `frontend/src/app/[lang]/(mwt)/(dashboard)/expedientes/page.tsx` (182 líneas)
  - `frontend/src/app/[lang]/dashboard/brands/page.tsx` vs `frontend/src/app/[lang]/(mwt)/(dashboard)/brands/page.tsx`
  - `frontend/src/app/[lang]/dashboard/clientes/page.tsx` vs `frontend/src/app/[lang]/(mwt)/(dashboard)/clientes/page.tsx`
  - `frontend/src/app/[lang]/dashboard/nodos/page.tsx` (313 líneas) vs `frontend/src/app/[lang]/(mwt)/(dashboard)/nodos/page.tsx` (313 líneas)
  - `frontend/src/app/[lang]/dashboard/pipeline/page.tsx` (315 líneas) vs `frontend/src/app/[lang]/(mwt)/(dashboard)/pipeline/page.tsx` (315 líneas)
- **Decisión de cuál eliminar:** verificar `frontend/src/app/[lang]/layout.tsx` y `frontend/src/middleware.ts`. El route tree activo es el que el middleware y layout referencian.
- **Criterio de done:**
  - [ ] Solo existe UNA carpeta de dashboard (no dos)
  - [ ] Todas las rutas navegan correctamente post-limpieza
  - [ ] ~1,300 líneas eliminadas

#### Item S11-05: Eliminar states.ts duplicado
- **Agente:** AG-03 Frontend
- **Qué hacer:**
  1. El archivo canónico es `frontend/src/constants/states.ts` (definido por C2).
  2. Redirigir TODOS los imports que apunten a `frontend/src/lib/constants/states.ts` hacia el canónico.
  3. Eliminar `frontend/src/lib/constants/states.ts`.
- **Criterio de done:**
  - [ ] Solo existe `frontend/src/constants/states.ts`
  - [ ] `grep -rn "lib/constants/states" frontend/src/ --include="*.tsx" --include="*.ts" | grep -v node_modules` → 0 resultados
  - [ ] Todos los imports apuntan a `@/constants/states`

#### Item S11-06: Migrar hex hardcodeados a CSS variables
- **Agente:** AG-03 Frontend
- **Archivos afectados (paths exactos):**
  - `frontend/src/components/ui/StateBadge.tsx` — 8 pares de colores hex → usar .badge-* classes
  - `frontend/src/app/[lang]/(mwt)/(dashboard)/transfers/page.tsx` — 6 pares de colores hex → crear STATUS_CONFIG con badge classes
  - `frontend/src/components/ui/ExpedienteTimeline.tsx` — #75CBB3, #013A57 → usar .timeline-dot-* classes
  - `frontend/src/app/[lang]/(mwt)/bison/page.tsx` — colores de marca
  - `frontend/src/app/[lang]/(mwt)/goliath/page.tsx` — colores de marca
  - `frontend/src/app/[lang]/(mwt)/leopard/page.tsx` — colores de marca
  - `frontend/src/app/[lang]/(mwt)/orbis/page.tsx` — colores de marca
  - `frontend/src/app/[lang]/(mwt)/velox/page.tsx` — colores de marca
  - Nota: paths de páginas Rana Walk pueden variar — verificar con `grep -rn '#[0-9A-Fa-f]\{6\}' frontend/src/ --include="*.tsx" | grep -v node_modules`
- **Qué hacer:**
  1. StateBadge: usar clases .badge-* del design system en vez de inline styles con hex.
  2. transfers/page.tsx: crear STATUS_CONFIG con clases badge del design system.
  3. Timeline: usar clases .timeline-dot-* (ya existen en globals.css).
  4. Páginas Rana Walk: agregar CSS variables de producto en globals.css si no existen, o usar las existentes.
- **Criterio de done:**
  - [ ] `grep -rn '#[0-9A-Fa-f]\{6\}' frontend/src/app/ frontend/src/components/ --include="*.tsx"` → 0 resultados
  - [ ] `grep -rn 'bg-\[#\|text-\[#\|border-\[#' frontend/src/ --include="*.tsx" | grep -v node_modules` → 0 resultados

#### Item S11-07: Accesibilidad — inputs, botones, drawers
- **Agente:** AG-03 Frontend
- **Sub-items:**

**(A) 26 inputs sin id** (principalmente ArtifactFormDrawer.tsx)
- Agregar id a cada input + htmlFor al label correspondiente

**(B) 34 botones sin aria-label**
- Agregar aria-label descriptivo a botones que solo muestran ícono

**(C) Drawers sin aria-modal** (paths exactos)
- `frontend/src/components/modals/ArtifactFormDrawer.tsx`
- `frontend/src/components/modals/RegisterCostDrawer.tsx`
- `frontend/src/components/modals/RegisterPaymentDrawer.tsx`
- Agregar role="dialog", aria-modal="true", Escape handler
- O migrar a FormModal si es factible

- **Criterio de done:**
  - [ ] Smoke check (grep, no definitivo): `grep -rn '<input\b' frontend/src/ --include="*.tsx" | grep -v node_modules | grep -v 'id=' | wc -l` → reducido significativamente vs baseline
  - [ ] Smoke check: botones icon-only sin aria-label reducidos vs baseline
  - [ ] eslint-plugin-jsx-a11y instalado y configurado como warning (no blocking en R1, blocking en Sprint 12)
  - [ ] Tests RTL/axe para: FormModal, ConfirmDialog, ArtifactFormDrawer (al menos 1 test de accesibilidad por componente modal)
  - [ ] Drawers con role="dialog" + aria-modal="true" + Escape handler

#### Item S11-08: Tests — state machine + CRUD + Playwright
- **Agente:** AG-02 Backend + AG-03 Frontend
- **Sub-items:**

**(A) Tests state machine (AG-02)**
- Archivo: `backend/apps/expedientes/tests/test_transitions.py`
- Crear test paramétrico: toda la matriz [estado × comando] → resultado esperado (éxito o error)
- Mínimo: verificar que C13 (IssueInvoice) falla si status ≠ EN_DESTINO, que C16 (Cancel) falla en CERRADO/CANCELADO, que C10 falla sin ART-05+06
- **Criterio:** test_transitions.py cubre los 22 commands × estados inválidos

**(B) Tests CRUD Sprint 9 (AG-03)**
- Archivos iniciales esperados:
  - `frontend/src/app/[lang]/(mwt)/(dashboard)/brands/__tests__/page.test.tsx`
  - `frontend/src/app/[lang]/(mwt)/(dashboard)/clientes/__tests__/page.test.tsx`
  - `frontend/src/app/[lang]/(mwt)/(dashboard)/nodos/__tests__/page.test.tsx`
- Crear tests unitarios (al menos render + fetch mock por módulo)
- **Criterio:** cada módulo CRUD tiene al menos 1 test de render y 1 test de acción

**(C) Playwright config (AG-03)**
- Mover base URL de `https://consola.mwt.one/` a variable de entorno
- **Criterio:** `grep -rn "consola.mwt.one" frontend/ --include="*.ts" | wc -l` → 0 (usa env var)

#### Item S11-09: Seguridad — raw SQL + serializers
- **Agente:** AG-02 Backend
- **Sub-items:**

**(A) Raw SQL audit**
- Archivos: `backend/apps/knowledge/knowledge_service/routers/ask.py` y `sessions.py`
- Verificar que NO existe SQL dinámico no parametrizado: f-strings, concatenación con +, .format(), templates armados antes de text()
- Grep amplio: `grep -rn 'f".*SELECT\|f".*INSERT\|f".*UPDATE\|\.format(.*SELECT\|+ "SELECT\|+ "INSERT' backend/ --include="*.py" | grep -v migrations | grep -v __pycache__`
- Si hay SQL dinámico: refactorizar a ORM o text() con :bind parameters
- Test: ejecutar query con input malicioso (ej: `'; DROP TABLE --`) y verificar que no ejecuta
- **Criterio:** 0 SQL dinámico no parametrizado. Grep amplio → 0 resultados. Test de inyección negativo passing.

**(B) Serializers explícitos**
- Archivos: `backend/apps/liquidations/serializers.py`, `backend/apps/transfers/serializers.py`
- Reemplazar `fields = "__all__"` por lista explícita de campos
- **Criterio:** `grep -rn 'fields.*"__all__"' backend/ --include="*.py"` → 0 resultados

---

### FASE 1 — Features (si Fase 0 completó a tiempo)

#### Item S11-10: Portal B2B (portal.mwt.one) — vista cliente
- **Agente:** AG-02 Backend + AG-03 Frontend
- **Dependencia:** S10-06 security hardening DONE, S10-07 knowledge DONE
- **Decisiones CEO necesarias antes de implementar:**
  - CEO-15: ¿Cuáles artefactos son visibles para clientes? (propuesta: ART-01, ART-02, ART-05, ART-09)
  - CEO-16: ¿Cuáles transiciones generan notificación al cliente?
  - CEO-20: Signed URLs para documentos (implementar antes de exponer docs a clientes)

**Scope mínimo viable:**
- Login JWT separado para roles CLIENT_*
- Vista "Mis expedientes": lista filtrada por client_id (ClientScopedManager, nunca .all())
- Vista detalle expediente: timeline + artefactos visibles (según CEO-15) + costos vista cliente
- Endpoint knowledge /ask/ accesible para cliente (scoped a docs PUBLIC + PARTNER_B2B)
- Signed URLs para documentos (CEO-20)
- Sin datos CEO-ONLY visibles (nunca márgenes, comisiones, costos internos)

**Archivos iniciales esperados:**
- Backend: `backend/apps/portal/views.py`, `backend/apps/portal/serializers.py`, `backend/apps/portal/urls.py`
- Frontend: crear dentro del route tree superviviente (S11-04): `portal/page.tsx`, `portal/expedientes/page.tsx`, `portal/expedientes/[id]/page.tsx`
- Tests: `backend/apps/portal/tests/test_tenant_isolation.py`

**Seguridad obligatoria:**
- ClientScopedManager en toda query: `for_user(user)`, nunca `.all()`
- No distinguir "no existe" de "no tienes acceso" → mismo 404
- Documentos via signed URLs (30min expiry), nunca links permanentes
- Rate limiting aplicado al portal

- **Criterio de done:**
  - [ ] Cliente puede loguearse y ver solo SUS expedientes
  - [ ] Timeline + artefactos visibles correctos
  - [ ] 0 datos CEO-ONLY expuestos
  - [ ] Documentos via signed URLs
  - [ ] Knowledge /ask/ scoped a PUBLIC + PARTNER_B2B

#### Item S11-11: Módulo Productos (PLT-09)
- **Agente:** AG-03 Frontend + AG-02 Backend
- **Dependencia:** PLT-04 (Nodos DONE) + PLT-07 (Brands DONE)
- **Archivo físico:** Crear `productos/page.tsx` dentro del route tree superviviente definido por S11-04 (NO hardcodear path antes de S11-04).
- **Ruta URL:** `/{lang}/dashboard/productos`

**Scope:**
- CRUD de productos: nombre, SKU base, brand (FK), categoría, descripción
- Tabla con filtro por brand y búsqueda
- FormModal para crear/editar, ConfirmDialog para eliminar
- Endpoints: GET/POST /api/productos/, PUT/DELETE /api/productos/{id}/

- **Criterio de done:**
  - [ ] CRUD completo funcional
  - [ ] Filtro por brand
  - [ ] Usa FormModal + ConfirmDialog
  - [ ] Sidebar actualizado con link a Productos
  - [ ] Design system aplicado (0 hex hardcodeados)

---

### QA

#### Item S11-12: Tests Sprint 11
- **Dependencia:** Items 1-11
- **Archivos iniciales esperados:**
  - `backend/apps/expedientes/tests/test_transitions_full.py` — state machine paramétrica
  - `backend/apps/portal/tests/test_tenant_isolation.py` — tests negativos B2B (si S11-10 se implementó)
  - `frontend/src/app/[lang]/(mwt)/(dashboard)/brands/__tests__/page.test.tsx` — CRUD brands
  - `frontend/src/app/[lang]/(mwt)/(dashboard)/clientes/__tests__/page.test.tsx` — CRUD clientes
  - `frontend/src/app/[lang]/(mwt)/(dashboard)/nodos/__tests__/page.test.tsx` — CRUD nodos
  - Nota: paths frontend ajustar según route tree superviviente de S11-04

**Limpieza:**
- [ ] ARCHIVADO no existe en backend
- [ ] Estados legacy eliminados del frontend
- [ ] Solo 1 states.ts, solo 1 carpeta dashboard
- [ ] 0 hex hardcodeados en TSX
- [ ] 0 inputs sin id, 0 icon buttons sin aria-label
- [ ] 0 serializers con fields="__all__"
- [ ] 0 SQL injection vectors en knowledge service

**State machine tests:**
- [ ] Test paramétrico cubre 22 commands × estados inválidos
- [ ] C13 falla si status ≠ EN_DESTINO
- [ ] C16 falla en CERRADO/CANCELADO

**Portal B2B (si se implementó):**
- [ ] Cliente solo ve sus expedientes
- [ ] 0 datos CEO-ONLY expuestos (verificar response JSON)
- [ ] Signed URLs expiran después de 30min
- [ ] Knowledge scoped correctamente
- [ ] TEST NEGATIVO: test_cross_tenant_access — cliente A intenta GET /api/ui/expedientes/{id_de_cliente_B}/ → 404 (no 403)
- [ ] TEST NEGATIVO: test_same_404_semantics — expediente inexistente y expediente ajeno retornan el mismo 404 (no distinguir "no existe" de "no tienes acceso")
- [ ] TEST NEGATIVO: test_signed_url_expiry — URL firmada con expiry pasado → 403/410
- [ ] TEST NEGATIVO: test_knowledge_scope_denial — /ask/ con query sobre doc CEO-ONLY → respuesta no incluye contenido CEO-ONLY

**Productos (si se implementó):**
- [ ] CRUD completo
- [ ] Filtro por brand funciona

**Regresión:**
- [ ] Acordeón Sprint 10 funciona
- [ ] Pipeline, Nodos, Brands, Clientes CRUD funciona
- [ ] Security: rate limiting, Redis password, JWT lifetimes

---

## Dependencias internas

```
S11-01 (ARCHIVADO BE) ──┐
S11-02 (Legacy FE) ──────┤
S11-03 (States central.) ┤── Fase 0 bloque 1 (state machine)
S11-04 (Rutas dup.) ──────┤   S11-03 depende de S11-05
S11-05 (states.ts dup.) ──┤

S11-06 (Hex → CSS vars) ─┤── Fase 0 bloque 2 (design system)
S11-07 (A11y) ────────────┤

S11-08 (Tests) ───────────┤── Fase 0 bloque 3 (calidad)
S11-09 (SQL + serializers)┤

S11-10 (Portal B2B) ──────┤── Fase 1 (si hay tiempo)
S11-11 (Productos) ────────┤   independientes entre sí

S11-12 (Tests finales) ────┤── después de todo
```

---

## Criterio Sprint 11 DONE

### Obligatorio (Fase 0)
1. ARCHIVADO eliminado del backend
2. 0 estados legacy en frontend
3. 0 strings de estado hardcodeados fuera de states.ts
4. Solo 1 carpeta dashboard, solo 1 states.ts
5. 0 hex hardcodeados en TSX
6. 0 inputs sin id, 0 icon buttons sin aria-label
7. Tests state machine cubren 22 commands × estados inválidos
8. 0 serializers con fields="__all__", 0 SQL injection vectors
9. Sin regresiones Sprint 9/9.1/10

### Opcional (Fase 1 — si hay tiempo)
10. Portal B2B: cliente ve sus expedientes, 0 datos CEO-ONLY expuestos
11. Módulo Productos: CRUD completo con filtro por brand

---

## Matriz de trazabilidad DT → OBS → Item

| DT ID | OBS Claude Code | Item Sprint 11 | Archivo principal | Grep de verificación |
|-------|----------------|-----------------|-------------------|---------------------|
| DT-01 | OBS-001 | S11-01 | backend/apps/expedientes/enums.py | `grep -rn ARCHIVADO backend/` |
| DT-02 | OBS-002 | S11-02 | expedientes/page.tsx + repo-wide | Kill-list grep LEGACY_STATE_DENYLIST |
| DT-03 | OBS-003 | S11-03 | 6 archivos listados | Grep 8 estados + arrays derivados |
| DT-04 | OBS-022 | S11-04 | 5 pares de rutas listados | Solo 1 carpeta dashboard |
| DT-05 | OBS-004 | S11-05 | frontend/src/lib/constants/states.ts | `grep lib/constants/states` |
| DT-06 | OBS-026 | S11-06 | 8+ archivos listados | `grep '#[0-9A-Fa-f]{6}'` en TSX |
| DT-07 | OBS-028 | S11-07a | ArtifactFormDrawer.tsx + others | Smoke grep + eslint-plugin-jsx-a11y |
| DT-08 | OBS-029 | S11-07b | 34 botones repo-wide | Smoke grep + eslint |
| DT-09 | OBS-030 | S11-07c | 3 drawers listados | role="dialog" + aria-modal |
| DT-10 | OBS-032 | S11-08a | test_transitions.py | 22 commands × estados inválidos |
| DT-11 | OBS-033 | S11-08b | tests CRUD frontend | Al menos 1 test por módulo |
| DT-12 | OBS-034 | S11-08c | playwright config | `grep consola.mwt.one` → 0 |
| DT-13 | OBS-009 | S11-09a | ask.py, sessions.py | Grep SQL dinámico + test inyección |
| DT-14 | OBS-010 | S11-09b | liquidations/serializers.py, transfers/serializers.py | `grep "__all__"` → 0 |

---

## Retrospectiva
(Completar al cerrar el sprint)

---

Stamp: DRAFT v2.1 — Arquitecto (Claude Opus) 2026-03-18. Auditoría ChatGPT: R1 8.7 → R2 9.6 (aprobado). 11 fixes acumulados.
