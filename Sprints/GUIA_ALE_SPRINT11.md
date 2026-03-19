# Sprint 11 — Guía de implementación para Alejandro

## Qué es esto
Limpieza de deuda técnica pre-B2B (obligatorio) + Portal B2B + Módulo Productos (si hay tiempo).
Auditado 2 rondas por ChatGPT — score 9.6/10. 11 fixes aplicados. LOTE v2.1.

## Estructura del sprint

| Fase | Items | Prioridad | Estimado |
|------|-------|-----------|----------|
| 0 | S11-01 a S11-09: Limpieza (state machine, rutas, design system, a11y, tests, seguridad) | P0 obligatorio | 3-4 días |
| 1 | S11-10 Portal B2B, S11-11 Módulo Productos | P2 si hay tiempo | 3-5 días |
| QA | S11-12 Tests finales | P0 | 1 día |

**REGLA DURA:** No arrancar Fase 1 hasta que S11-01 a S11-09 estén DONE y regresión mínima verde (pipeline, acordeón, CRUD). Sin excepción. Si Fase 0 se extiende, Fase 1 completa se pasa a Sprint 12.

---

## Fase 0 — Limpieza obligatoria

### Bloque 1: State machine (S11-01 a S11-05)

**S11-01: Eliminar ARCHIVADO del backend**
1. Verificar DB: `SELECT count(*) FROM expedientes_expediente WHERE status='ARCHIVADO';`
2. Si hay registros: migrarlos a CERRADO
3. Eliminar ARCHIVADO de `backend/apps/expedientes/enums.py`
4. Verificar: `grep -rn "ARCHIVADO" backend/ --include="*.py" | grep -v migrations | grep -v __pycache__` → 0

**S11-02: Eliminar estados legacy repo-wide**
Kill-list: ARCHIVADO, EVALUACION_PREVIA, FORMALIZACION, QC, ENTREGA
```bash
grep -rn "ARCHIVADO\|EVALUACION_PREVIA\|FORMALIZACION\|\bQC\b\|ENTREGA" frontend/src/ backend/ --include="*.tsx" --include="*.ts" --include="*.py" | grep -v node_modules | grep -v __pycache__ | grep -v migrations
```
Eliminar cada ocurrencia. Usar STATE_BADGE_CLASSES de states.ts para mapeos de colores.

**S11-03: Centralizar 28 strings de estado**
Agregar exports a `frontend/src/constants/states.ts`:
```ts
export const TERMINAL_STATES = ["CERRADO", "CANCELADO"] as const;
export const CANCELLABLE_STATES = ["REGISTRO", "PRODUCCION", "PREPARACION"] as const;
export const COST_PHASES = CANONICAL_STATES.filter(s => !TERMINAL_STATES.includes(s));
```
Archivos a migrar:
- `components/expediente/PipelineActionsPanel.tsx`
- `components/modals/CancelExpedienteModal.tsx`
- `components/modals/RegisterCostDrawer.tsx`
- `components/ui/StateBadge.tsx`
- `components/ui/ExpedienteTimeline.tsx`
- Cualquier otro detectado con grep

Verificar: `grep -rn '"REGISTRO"\|"PRODUCCION"\|"PREPARACION"\|"DESPACHO"\|"TRANSITO"\|"EN_DESTINO"\|"CERRADO"\|"CANCELADO"' frontend/src/ --include="*.tsx" --include="*.ts" | grep -v node_modules | grep -v "constants/states"` → 0

**S11-04: Eliminar rutas duplicadas**
1. VERIFICAR PRIMERO: revisar `frontend/src/app/[lang]/layout.tsx` y `frontend/src/middleware.ts`
2. El route tree activo es el que layout/middleware referencian. El otro es legacy.
3. Eliminar la carpeta legacy completa
4. Pares detectados:
   - `/[lang]/dashboard/expedientes/` vs `/[lang]/(mwt)/(dashboard)/expedientes/`
   - Mismo para: brands, clientes, nodos, pipeline

**S11-05: Eliminar states.ts duplicado**
- Canónico: `frontend/src/constants/states.ts` (obligatorio)
- Eliminar: `frontend/src/lib/constants/states.ts`
- Redirigir todos los imports a `@/constants/states`

### Bloque 2: Design system (S11-06)

Migrar hex hardcodeados a CSS variables:
- `components/ui/StateBadge.tsx` → usar .badge-* classes
- `transfers/page.tsx` → STATUS_CONFIG con badge classes
- `components/ui/ExpedienteTimeline.tsx` → .timeline-dot-* classes
- Páginas Rana Walk → CSS variables de producto

Verificar: `grep -rn '#[0-9A-Fa-f]\{6\}' frontend/src/app/ frontend/src/components/ --include="*.tsx"` → 0

### Bloque 3: Accesibilidad (S11-07)

**(A)** Agregar id a inputs + htmlFor a labels (principalmente ArtifactFormDrawer.tsx)
**(B)** Agregar aria-label a botones icon-only
**(C)** Drawers: agregar role="dialog" + aria-modal="true" + Escape handler a:
- `frontend/src/components/modals/ArtifactFormDrawer.tsx`
- `frontend/src/components/modals/RegisterCostDrawer.tsx`
- `frontend/src/components/modals/RegisterPaymentDrawer.tsx`
**(D)** Instalar eslint-plugin-jsx-a11y como warning

### Bloque 4: Tests (S11-08)

**(A)** State machine: expandir `backend/apps/expedientes/tests/test_transitions.py` con test paramétrico [22 commands × estados inválidos]
**(B)** CRUD frontend: crear tests en `__tests__/page.test.tsx` para brands, clientes, nodos
**(C)** Playwright: mover base URL a variable de entorno, no hardcodear consola.mwt.one

### Bloque 5: Seguridad (S11-09)

**(A)** Raw SQL: auditar `backend/apps/knowledge/knowledge_service/routers/ask.py` y `sessions.py`. Verificar parametrización. Grep: `grep -rn 'f".*SELECT\|f".*INSERT\|\.format(.*SELECT' backend/ --include="*.py"`
**(B)** Serializers: reemplazar `fields = "__all__"` por lista explícita en liquidations y transfers serializers

---

## Fase 1 — Features (SOLO si Fase 0 está DONE + regresión verde)

### S11-10: Portal B2B
**Decisiones CEO necesarias primero:**
- CEO-15: ¿Cuáles artefactos son visibles para clientes?
- CEO-16: ¿Cuáles transiciones generan notificación?
- CEO-20: Signed URLs (implementar antes de exponer docs)

**Archivos a crear:**
- Backend: `backend/apps/portal/views.py`, `serializers.py`, `urls.py`
- Frontend: dentro del route tree superviviente: `portal/page.tsx`, `portal/expedientes/page.tsx`, `portal/expedientes/[id]/page.tsx`
- Tests: `backend/apps/portal/tests/test_tenant_isolation.py`

**Seguridad obligatoria:**
- ClientScopedManager: `for_user(user)`, nunca `.all()`
- No distinguir "no existe" de "no tienes acceso" → mismo 404
- Documentos via signed URLs (30min expiry)
- Knowledge /ask/ scoped a PUBLIC + PARTNER_B2B

### S11-11: Módulo Productos
- Crear `productos/page.tsx` dentro del route tree superviviente (S11-04)
- CRUD: nombre, SKU base, brand (FK), categoría, descripción
- Usar FormModal + ConfirmDialog
- Endpoints: GET/POST /api/productos/, PUT/DELETE /api/productos/{id}/
- Actualizar Sidebar con link

---

## Lo que NO debes hacer

1. **NO crear state machine paralela** — importar de states.ts siempre
2. **NO dejar hex hardcodeados** — solo CSS variables
3. **NO crear rutas en la carpeta legacy** — verificar cuál sobrevive primero
4. **NO arrancar Portal B2B sin terminar limpieza**
5. **NO dejar serializers con fields="__all__"**

## Tests post-deploy

**Limpieza:**
- [ ] `grep ARCHIVADO backend/` → 0
- [ ] Kill-list grep → 0
- [ ] Solo 1 carpeta dashboard
- [ ] Solo 1 states.ts
- [ ] 0 hex en TSX
- [ ] 0 SQL injection vectors

**Regresión:**
- [ ] Acordeón Sprint 10 funciona
- [ ] Pipeline funciona
- [ ] CRUD Nodos/Brands/Clientes funciona

**Portal B2B (si se implementó):**
- [ ] Cliente ve solo SUS expedientes
- [ ] Expediente ajeno → 404 (no 403)
- [ ] 0 datos CEO-ONLY en response
- [ ] Signed URL expirada → fallo

---

*Sprint 11 · MWT ONE · LOTE v2.1 · Score auditoría 9.6/10*
