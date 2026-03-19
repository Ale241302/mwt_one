# RESUMEN SPRINT 11 — MWT ONE
**Fecha de cierre:** 19 de marzo de 2026
**Estado general:** ✅ COMPLETADO
**Rama base:** `main` (trabajo integrado directamente)

---

## S11-01 — Eliminar ARCHIVADO del backend
**Estado:** ✅ DONE
**Rama:** `feat/sprint11-cleanup`
**Agente:** AG-02 API Builder

### Qué se hizo
- Se eliminó el estado `ARCHIVADO` del enum `ExpedienteStatus` en `backend/apps/expedientes/enums.py`.
- Se crearon las migraciones `0010` y `0011` para migrar registros existentes a `CERRADO`.
- Backend arranca sin errores. Tests passing.

### Archivos modificados
- `backend/apps/expedientes/enums.py`
- `backend/apps/expedientes/migrations/0010_*.py` _(nueva)_
- `backend/apps/expedientes/migrations/0011_*.py` _(nueva)_

### Criterio de aceptación cumplido
```
grep -rn ARCHIVADO backend/ --include=*.py | grep -v migrations → 0 resultados ✅
```

---

## S11-02 — Eliminar estados legacy repo-wide
**Estado:** ✅ DONE
**Rama:** `feat/sprint11-cleanup`
**Agente:** AG-03 Frontend
**Depende de:** S11-01

### Qué se hizo
- Kill-list completa: `ARCHIVADO`, `EVALUACION_PREVIA`, `FORMALIZACION`, `QC`, `ENTREGA` eliminados de frontend, backend, fixtures, mocks, tests y seed data.
- Se adoptó `STATE_BADGE_CLASSES` de `constants/states.ts` para todos los mapeos de colores, eliminando strings legacy.

### Archivos modificados
- Múltiples fixtures y seed data en `backend/`
- Componentes y páginas en `frontend/src/`
- Mocks y tests existentes limpiados

### Criterio de aceptación cumplido
```
Kill-list grep repo-wide → 0 resultados (excluyendo migrations y LOTE) ✅
STATE_BADGE_CLASSES de states.ts como fuente de verdad ✅
```

---

## S11-03 — Centralizar 28 strings de estado en states.ts
**Estado:** ✅ DONE
**Rama:** `feat/sprint11-cleanup`
**Agente:** AG-03 Frontend
**Depende de:** S11-05

### Qué se hizo
- Se centralizaron los 28 strings de estado en `frontend/src/constants/states.ts`.
- Grep de los 8 estados fuera de `constants/states` → 0 resultados.
- Grep de arrays derivados fuera de `constants/states` → solo imports, no definiciones.
- Se migraron arrays locales en `PipelineActionsPanel`, `CancelExpedienteModal`, `RegisterCostDrawer`, `StateBadge`, `ExpedienteTimeline`.

### Archivos modificados
- `frontend/src/constants/states.ts` _(exports: `TERMINAL_STATES`, `CANCELLABLE_STATES`, `COST_PHASES`, `TIMELINE_STEPS`, `TIMELINE_STATES_CANONICAL`)_
- `frontend/src/components/expediente/PipelineActionsPanel.tsx`
- `frontend/src/components/expediente/CancelExpedienteModal.tsx`
- `frontend/src/components/expediente/RegisterCostDrawer.tsx`
- `frontend/src/components/expediente/StateBadge.tsx`
- `frontend/src/components/expediente/ExpedienteTimeline.tsx`

### Criterio de aceptación cumplido
```
Grep 8 estados fuera de constants/states → 0 resultados ✅
Arrays derivados solo en constants/states.ts ✅
```

---

## S11-04 — Eliminar rutas duplicadas (~1,300 LOC)
**Estado:** ✅ DONE
**Rama:** `feat/sprint11-cleanup`
**Agente:** AG-03 Frontend
**Depende de:** S11-02

### Qué se hizo
- Se verificaron `layout.tsx` y `middleware.ts` para determinar el route tree activo: `[lang]/(mwt)/(dashboard)/`.
- Se eliminó la carpeta legacy de dashboard (ruta plana `/dashboard/`).
- Los 5 pares de rutas consolidados: `expedientes`, `brands`, `clientes`, `nodos`, `pipeline`.
- ~1,300 líneas eliminadas.

### Estructura final de rutas
```
frontend/src/app/[lang]/
  (mwt)/
    (auth)/
    (dashboard)/
      brands/
      clientes/
      dashboard/
      expedientes/
      nodos/
      pipeline/
      portal/
      productos/
      transfers/
      usuarios/
  (ranawalk)/
```

### Archivos eliminados
- `frontend/src/app/[lang]/dashboard/` _(carpeta legacy completa ~1,300 LOC)_

### Criterio de aceptación cumplido
```
Una sola carpeta de dashboard activa ✅
Todas las rutas navegan correctamente ✅
~1,300 líneas eliminadas ✅
```

---

## S11-05 — Eliminar states.ts duplicado
**Estado:** ✅ DONE
**Rama:** `feat/sprint11-cleanup`
**Agente:** AG-03 Frontend
**Depende de:** S11-02

### Qué se hizo
- Se eliminó `frontend/src/lib/constants/states.ts` (archivo duplicado).
- `frontend/src/lib/constants/` solo conserva `creditBands.ts`.
- Todos los imports redirigidos a `@/constants/states`.

### Archivos eliminados
- `frontend/src/lib/constants/states.ts`

### Criterio de aceptación cumplido
```
grep lib/constants/states → 0 resultados ✅
Solo existe frontend/src/constants/states.ts como canónico ✅
Todos los imports apuntan a @/constants/states ✅
```

---

## S11-06 — Migrar hex hardcodeados a CSS variables
**Estado:** ✅ DONE
**Rama:** `feat/sprint11-cleanup`
**Agente:** AG-03 Frontend
**Depende de:** S11-04, S11-05

### Qué se hizo
- Se migraron todos los colores hex hardcodeados a CSS variables del design system definidas en `globals.css`.
- Archivos migrados: `StateBadge.tsx`, `transfers/page.tsx`, `ExpedienteTimeline.tsx` y las 5 páginas Rana Walk (`bison`, `goliath`, `leopard`, `orbis`, `velox`).

### Archivos modificados
- `frontend/src/components/expediente/StateBadge.tsx`
- `frontend/src/app/[lang]/(mwt)/(dashboard)/transfers/page.tsx`
- `frontend/src/components/expediente/ExpedienteTimeline.tsx`
- `frontend/src/app/[lang]/(ranawalk)/bison/page.tsx`
- `frontend/src/app/[lang]/(ranawalk)/goliath/page.tsx`
- `frontend/src/app/[lang]/(ranawalk)/leopard/page.tsx`
- `frontend/src/app/[lang]/(ranawalk)/orbis/page.tsx`
- `frontend/src/app/[lang]/(ranawalk)/velox/page.tsx`

### Criterio de aceptación cumplido
```
grep '#[0-9A-Fa-f]{6}' frontend/src/app/ frontend/src/components/ --include=*.tsx → 0 resultados ✅
grep 'bg-[#' → 0 resultados ✅
```

---

## S11-07 — Accesibilidad — inputs, botones, drawers
**Estado:** ✅ DONE
**Rama:** `feat/sprint11-cleanup`
**Agente:** AG-03 Frontend
**Depende de:** S11-04

### Qué se hizo
**(A)** 26 inputs sin `id` corregidos: se agregó `id` + `htmlFor` en todos los labels relacionados.
**(B)** 34 botones icon-only sin `aria-label` corregidos.
**(C)** Drawers `ArtifactFormDrawer`, `RegisterCostDrawer`, `RegisterPaymentDrawer`: se agregó `role="dialog"`, `aria-modal="true"` y handler de tecla `Escape`.
**(D)** `eslint-plugin-jsx-a11y` instalado como warning en `.eslintrc`.

### Archivos modificados/creados
- `frontend/src/components/expediente/ArtifactFormDrawer.tsx`
- `frontend/src/components/expediente/RegisterCostDrawer.tsx`
- `frontend/src/components/expediente/RegisterPaymentDrawer.tsx`
- Múltiples componentes de formulario con `id`/`htmlFor` corregidos
- `frontend/.eslintrc.json` _(jsx-a11y añadido)_
- `frontend/package.json` _(eslint-plugin-jsx-a11y añadido)_
- Tests RTL/axe: `FormModal.test.tsx`, `ConfirmDialog.test.tsx`, `ArtifactFormDrawer.test.tsx`

### Criterio de aceptación cumplido
```
0 inputs sin id ✅
0 botones icon-only sin aria-label ✅
Todos los drawers con aria-modal ✅
Tests RTL/axe passing ✅
```

---

## S11-08 — Tests — state machine + CRUD + Playwright
**Estado:** ✅ DONE
**Rama:** `feat/sprint11-cleanup`
**Agente:** AG-02 API Builder
**Depende de:** S11-01 a S11-07

### Qué se hizo
**(A)** Test paramétrico state machine en `test_transitions.py`: 22 commands × estados inválidos, cobertura de C13 (falla si status ≠ EN_DESTINO) y C16 (falla en CERRADO/CANCELADO).
**(B)** Tests CRUD frontend: `brands/page.test.tsx`, `clientes/page.test.tsx`, `nodos/page.test.tsx`.
**(C)** Playwright: base URL movida a variable de entorno `PLAYWRIGHT_BASE_URL`.

### Archivos modificados/creados
- `backend/apps/expedientes/tests/test_transitions.py` _(+78 líneas, cobertura paramétrica)_
- `backend/conftest.py` _(actualizado)_
- `backend/factories.py` _(actualizado)_
- `frontend/tests/brands/page.test.tsx` _(nuevo)_
- `frontend/tests/clientes/page.test.tsx` _(nuevo)_
- `frontend/tests/nodos/page.test.tsx` _(nuevo)_
- `frontend/playwright.config.ts` _(base URL → env var)_

### Criterio de aceptación cumplido
```
test_transitions.py cubre 22 commands × estados inválidos ✅
C13 falla si status ≠ EN_DESTINO ✅
C16 falla en CERRADO/CANCELADO ✅
Playwright usa env var para base URL ✅
```

---

## S11-09 — Seguridad — raw SQL audit + serializers explícitos
**Estado:** ✅ DONE
**Rama:** `feat/sprint11-security`
**Agente:** AG-02 API Builder
**Depende de:** S11-01

### Qué se hizo
**(A)** Auditoría de `ask.py` y `sessions.py`: 0 SQL dinámico no parametrizado. Test de inyección negativo (`'; DROP TABLE --`) implementado y passing.
**(B)** `fields='__all__'` reemplazado por lista explícita en `liquidations/serializers.py` y `transfers/serializers.py`.

### Archivos modificados
- `backend/apps/knowledge/ask.py`
- `backend/apps/sessions/sessions.py`
- `backend/apps/liquidations/serializers.py`
- `backend/apps/transfers/serializers.py`
- `backend/apps/expedientes/tests/test_security.py` _(nuevo, test inyección)_

### Criterio de aceptación cumplido
```
Grep SQL dinámico → 0 resultados ✅
Test inyección ('; DROP TABLE --) passing ✅
grep 'fields.*all' → 0 resultados ✅
```

---

## S11-10 — Portal B2B (portal.mwt.one) — vista cliente
**Estado:** ✅ DONE
**Rama:** `feat/sprint11-portal-b2b`
**Agente:** AG-03 Frontend
**Depende de:** S11-01 a S11-09 + Decisiones CEO-15, CEO-16, CEO-20

### Qué se hizo
- Login JWT para roles `CLIENT_*` implementado.
- Vista "Mis expedientes" con `ClientScopedManager` — cliente ve solo SUS expedientes.
- Vista detalle con timeline + artefactos.
- Knowledge `/ask/` scoped a `PUBLIC+PARTNER_B2B`.
- Signed URLs con 30min de expiración para documentos.
- Tests negativos de tenant isolation passing (0 datos CEO-ONLY expuestos).

### Archivos creados/modificados
**Backend:**
- `backend/apps/portal/apps.py`
- `backend/apps/portal/views.py`
- `backend/apps/portal/serializers.py`
- `backend/apps/portal/tests.py`
- `backend/apps/portal/urls.py`

**Frontend:**
- `frontend/src/app/[lang]/(mwt)/(dashboard)/portal/page.tsx`
- `frontend/src/app/[lang]/(mwt)/(dashboard)/portal/[id]/page.tsx`

### Criterio de aceptación cumplido
```
Cliente ve solo SUS expedientes ✅
0 datos CEO-ONLY expuestos ✅
Documentos via signed URLs (30min expiry) ✅
Knowledge scoped correctamente ✅
Tests negativos tenant isolation passing ✅
```

---

## S11-11 — Módulo Productos (PLT-09)
**Estado:** ✅ DONE
**Rama:** `feat/sprint11-productos`
**Agente:** AG-03 Frontend
**Depende de:** S11-01 a S11-09 DONE + PLT-04 (Nodos) + PLT-07 (Brands) DONE

### Qué se hizo
- CRUD completo de productos: nombre, SKU base, brand (FK), categoría, descripción.
- Tabla con filtro por brand.
- `FormModal` + `ConfirmDialog` integrados.
- Endpoints `GET/POST /api/productos/` y `PUT/DELETE /api/productos/{id}/`.
- Sidebar actualizado con enlace a Productos.
- 0 hex hardcodeados.

### Archivos creados/modificados
**Backend:**
- `backend/apps/productos/models.py`
- `backend/apps/productos/views.py`
- `backend/apps/productos/serializers.py`
- `backend/apps/productos/urls.py`
- `backend/apps/productos/migrations/0001_initial.py`
- `backend/apps/productos/tests.py`

**Frontend:**
- `frontend/src/app/[lang]/(mwt)/(dashboard)/productos/page.tsx`
- `frontend/src/components/Sidebar.tsx` _(actualizado)_

### Criterio de aceptación cumplido
```
CRUD completo funcional ✅
Filtro por brand ✅
Usa FormModal + ConfirmDialog ✅
Sidebar actualizado ✅
0 hex hardcodeados ✅
```

---

## S11-12 — Tests finales Sprint 11
**Estado:** ✅ DONE
**Rama:** `feat/sprint11-cleanup`
**Agente:** AG-06 QA
**Depende de:** S11-01 a S11-11

### Qué se hizo
- Regresión completa de limpieza: ARCHIVADO, estados legacy, 1 carpeta dashboard, 1 states.ts, 0 hex, 0 SQL injection, 0 serializers `all`.
- State machine paramétrica validada: 22 commands × estados inválidos.
- Portal B2B tests negativos passing.
- Productos CRUD completo.
- Regresión Sprint 9 / Sprint 9.1 / Sprint 10 verde.

### Criterio de aceptación cumplido
```
Todos los checks de limpieza en 0 ✅
Regresión Sprint 9/9.1/10 verde ✅
Tests negativos B2B passing ✅
CRUD Productos completo ✅
```

---

## Tabla resumen ejecutivo

| ID | Tarea | Agente | Estado |
|----|-------|--------|--------|
| S11-01 | Eliminar ARCHIVADO del backend | AG-02 | ✅ DONE |
| S11-02 | Eliminar estados legacy repo-wide | AG-03 | ✅ DONE |
| S11-03 | Centralizar 28 strings en states.ts | AG-03 | ✅ DONE |
| S11-04 | Eliminar rutas duplicadas (~1,300 LOC) | AG-03 | ✅ DONE |
| S11-05 | Eliminar states.ts duplicado | AG-03 | ✅ DONE |
| S11-06 | Migrar hex hardcodeados a CSS variables | AG-03 | ✅ DONE |
| S11-07 | Accesibilidad — inputs, botones, drawers | AG-03 | ✅ DONE |
| S11-08 | Tests — state machine + CRUD + Playwright | AG-02 | ✅ DONE |
| S11-09 | Seguridad — raw SQL audit + serializers | AG-02 | ✅ DONE |
| S11-10 | Portal B2B — vista cliente | AG-03 | ✅ DONE |
| S11-11 | Módulo Productos (PLT-09) | AG-03 | ✅ DONE |
| S11-12 | Tests finales Sprint 11 | AG-06 | ✅ DONE |

**Sprint 11 cerrado exitosamente. 12/12 tareas completadas. ✅**

---

*Documento generado a partir del repositorio [github.com/Ale241302/mwt_one](https://github.com/Ale241302/mwt_one)*
