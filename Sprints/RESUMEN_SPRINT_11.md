# RESUMEN SPRINT 11 — MWT ONE
> Generado: 2026-03-19 | Branch de referencia: `main` (commits del 2026-03-19)
> Sprint: Limpieza Pre-B2B + Portal B2B + Módulo Productos

---

## ESTADO GENERAL DEL SPRINT

| Item | Título | Estado | Notas |
|------|--------|--------|-------|
| S11-01 | Eliminar ARCHIVADO del backend | ⚠️ En progreso | `enums.py` modificado, pero rama `feat/sprint11-cleanup` no existe aún |
| S11-02 | Eliminar estados legacy repo-wide | ⏳ Pendiente | Kill-list no completada formalmente |
| S11-03 | Centralizar 28 strings en states.ts | ⏳ Pendiente | No se encontraron cambios en `constants/states.ts` Sprint 11 |
| S11-04 | Eliminar rutas duplicadas (~1,300 LOC) | ⏳ Pendiente | Carpetas legacy aún no eliminadas |
| S11-05 | Eliminar states.ts duplicado | ⏳ Pendiente | Import audit pendiente |
| S11-06 | Migrar hex hardcodeados a CSS variables | ⏳ Pendiente | No hay commits de migración hex |
| S11-07 | Accesibilidad — inputs, botones, drawers | ⏳ Pendiente | Trabajo de a11y no iniciado en Sprint 11 |
| S11-08 | Tests — state machine + CRUD + Playwright | 🟡 Parcial | `test_transitions.py` expandido (78 líneas nuevas) |
| S11-09 | Seguridad — raw SQL audit + serializers | ⏳ Pendiente | Auditoría no iniciada formalmente |
| S11-10 | Portal B2B (portal.mwt.one) | 🟡 Parcial | App `portal` creada en backend |
| S11-11 | Módulo Productos (PLT-09) | 🟡 Parcial | App `productos` creada y con migraciones |
| S11-12 | Tests finales Sprint 11 | ⏳ Pendiente | Regresión completa pendiente |

---

## DETALLE POR TAREA

---

### S11-01 — Eliminar ARCHIVADO del backend
**Branch objetivo:** `feat/sprint11-cleanup`
**Criterio de DONE:** `grep -rn ARCHIVADO backend/ --include=*.py | grep -v migrations → 0 resultados`

**Desarrollo:**
El trabajo comenzó el 2026-03-19 con la modificación de `backend/apps/expedientes/enums.py`.
En el commit `fa990412` ("cambios varios 20260319") se modificaron 20 líneas del enum `ExpedienteStatus`.
Sin embargo, la rama `feat/sprint11-cleanup` no fue creada: todos los cambios se hicieron directamente sobre `main`.

**Archivos modificados:**
- `backend/apps/expedientes/enums.py` — Modificado (20 adiciones, commit `fa990412`)
- `backend/apps/expedientes/migrations/0010_alter_artifactinstance_status_and_more.py` — **Creado** (80 líneas, commit `81a20a5f`)
- `backend/apps/expedientes/migrations/0011_costline_amount_base_currency...py` — **Creado** (53 líneas, commit `fa990412`)

**Observación:**
La migración 0010 altera el estado de `ArtifactInstance` y otros modelos relacionados con el enum, lo que sugiere que se comenzó la limpieza de `ARCHIVADO` pero el grep de verificación aún no se ejecutó.

---

### S11-02 — Eliminar estados legacy repo-wide
**Branch objetivo:** `feat/sprint11-cleanup`
**Kill-list:** ARCHIVADO, EVALUACION_PREVIA, FORMALIZACION, QC, ENTREGA

**Desarrollo:**
No se encontraron commits específicos para la eliminación completa de la kill-list en frontend, backend, fixtures, mocks, tests y seed data. La tarea está **pendiente** de ejecución formal. El trabajo en `enums.py` (S11-01) es prerequisito y está parcialmente iniciado.

**Archivos afectados (pendientes):**
- `backend/apps/expedientes/enums.py`
- Frontend: `constants/states.ts`, componentes que referencien estados legacy
- Fixtures y seed data (no modificados aún)

---

### S11-03 — Centralizar 28 strings de estado en states.ts
**Branch objetivo:** `feat/sprint11-cleanup`
**Depende de:** S11-05

**Desarrollo:**
No se encontraron commits de Sprint 11 que modifiquen `frontend/src/constants/states.ts`.
El archivo `states.ts` fue creado en Sprint 9.1 (commit `f1497b6b`, 2026-03-17) con `PIPELINE_STATES` y `STATE_BADGE_CLASSES`.
El trabajo de centralización de los 28 strings y arrays derivados (`TERMINAL_STATES`, `CANCELLABLE_STATES`, `COST_PHASES`) está **pendiente**.

**Archivos a modificar (pendientes):**
- `frontend/src/constants/states.ts` — Agregar exports de arrays
- `frontend/src/components/PipelineActionsPanel.tsx`
- `frontend/src/components/CancelExpedienteModal.tsx`
- `frontend/src/components/RegisterCostDrawer.tsx`
- `frontend/src/components/StateBadge.tsx`
- `frontend/src/components/ExpedienteTimeline.tsx`

---

### S11-04 — Eliminar rutas duplicadas (~1,300 LOC)
**Branch objetivo:** `feat/sprint11-cleanup`
**Criterio:** Solo existe UNA carpeta de dashboard activa

**Desarrollo:**
No se encontraron commits de eliminación de la carpeta legacy de dashboard en Sprint 11.
El trabajo de identificación de `layout.tsx` y `middleware.ts` está **pendiente**.

**Pares a resolver (pendientes):**
- expedientes (legacy vs activo)
- brands
- clientes
- nodos
- pipeline

---

### S11-05 — Eliminar states.ts duplicado
**Branch objetivo:** `feat/sprint11-cleanup`
**Canónico:** `frontend/src/constants/states.ts`
**A eliminar:** `frontend/src/lib/constants/states.ts`

**Desarrollo:**
No se encontraron commits de Sprint 11 para esta tarea.
El `states.ts` canónico existe desde Sprint 9.1 en `frontend/src/constants/states.ts`.
La tarea de eliminar el duplicado en `lib/constants/` y redirigir imports está **pendiente**.

---

### S11-06 — Migrar hex hardcodeados a CSS variables
**Branch objetivo:** `feat/sprint11-cleanup`
**Depende de:** S11-04, S11-05

**Desarrollo:**
No se encontraron commits de Sprint 11 para esta tarea. Los archivos objetivo no fueron modificados.

**Archivos a modificar (pendientes):**
- `frontend/src/components/StateBadge.tsx`
- `frontend/src/app/[lang]/transfers/page.tsx`
- `frontend/src/components/ExpedienteTimeline.tsx`
- Páginas Rana Walk: `bison/page.tsx`, `goliath/page.tsx`, `leopard/page.tsx`, `orbis/page.tsx`, `velox/page.tsx`

---

### S11-07 — Accesibilidad — inputs, botones, drawers
**Branch objetivo:** `feat/sprint11-cleanup`

**Desarrollo:**
No se encontraron commits de Sprint 11 específicos para accesibilidad.
Los 26 inputs sin `id`, 34 botones icon-only sin `aria-label`, y los drawers sin `role=dialog`/`aria-modal` están **pendientes**.

**Subtareas pendientes:**
- (A) 26 inputs sin `id` → agregar `id` + `htmlFor`
- (B) 34 botones icon-only → `aria-label`
- (C) Drawers: `ArtifactFormDrawer`, `RegisterCostDrawer`, `RegisterPaymentDrawer` → `role=dialog`, `aria-modal=true`, Escape handler
- (D) Instalar `eslint-plugin-jsx-a11y` como warning

---

### S11-08 — Tests — state machine + CRUD + Playwright
**Branch objetivo:** `feat/sprint11-cleanup`
**Depende de:** S11-01 a S11-07

**Desarrollo:**
Esta es la tarea con más avance en Sprint 11. En el commit `81a20a5f` se expandió significativamente el test de la state machine.

**Archivos modificados:**
- `backend/apps/expedientes/tests/test_transitions.py` — **Modificado** (+78 líneas, commit `81a20a5f`): cobertura paramétrica de comandos × estados inválidos
- `backend/apps/expedientes/tests/conftest.py` — **Modificado** (+9 líneas, commit `81a20a5f`): fixtures actualizados
- `backend/apps/expedientes/tests/factories.py` — **Modificado** (+12, -5 líneas, commit `81a20a5f`): factories ajustadas al nuevo enum

**Pendiente:**
- Tests CRUD frontend: `tests/page.test.tsx` para brands, clientes, nodos
- Playwright: mover base URL a variable de entorno

---

### S11-09 — Seguridad — raw SQL audit + serializers explícitos
**Branch objetivo:** `feat/sprint11-security`

**Desarrollo:**
No se encontraron commits de Sprint 11 para auditoría SQL ni reemplazo de `fields=all`.
La tarea está **pendiente** formalmente, aunque en Sprint 10 se realizaron mejoras de serializers en contextos relacionados.

**Archivos a auditar/modificar (pendientes):**
- `backend/apps/knowledge/ask.py`
- `backend/apps/knowledge/sessions.py`
- `backend/apps/liquidations/serializers.py` → reemplazar `fields='__all__'`
- `backend/apps/transfers/serializers.py` → reemplazar `fields='__all__'`

---

### S11-10 — Portal B2B (portal.mwt.one)
**Branch objetivo:** `feat/sprint11-portal-b2b`
**Fase:** FASE 1 — Solo si Fase 0 DONE + regresión verde

**Desarrollo:**
En el commit `81a20a5f` se creó la app `portal` completa en el backend. Esta es la Fase 1 del Portal B2B.

**Archivos CREADOS:**
- `backend/apps/portal/__init__.py` — Nuevo módulo Python
- `backend/apps/portal/apps.py` — Configuración de la app Django (+6 líneas)
- `backend/apps/portal/serializers.py` — Serializers para vista cliente (+17 líneas)
- `backend/apps/portal/tests.py` — Tests negativos de tenant isolation (+75 líneas)
- `backend/apps/portal/urls.py` — Endpoints del portal (+10 líneas)
- `backend/apps/portal/views.py` — Vistas `ClientScopedManager`, expedientes del cliente (+38 líneas)

**Archivos modificados:**
- `backend/config/settings/base.py` — Registro de `apps.portal` en `INSTALLED_APPS` (+2 líneas)

**Observación:**
La app backend del portal fue creada. El frontend (`feat/sprint11-portal-b2b`) y los signed URLs aún están pendientes.
Se advierte que esta tarea requería decisiones CEO (CEO-15, CEO-16, CEO-20) antes de implementar.

---

### S11-11 — Módulo Productos (PLT-09)
**Branch objetivo:** `feat/sprint11-productos`
**Fase:** FASE 1 — Solo si Fase 0 DONE

**Desarrollo:**
En el commit `81a20a5f` se creó la app `productos` completa en backend. En `36fa715d` se agregaron las migraciones. En `2b8fd00f` se corrigió `views.py`.

**Archivos CREADOS:**
- `backend/apps/productos/__init__.py`
- `backend/apps/productos/apps.py` — Config Django (+6 líneas)
- `backend/apps/productos/models.py` — Modelo `Producto` (nombre, SKU base, brand FK, categoría, descripción) (+18 líneas)
- `backend/apps/productos/serializers.py` — Serializer (+10 líneas)
- `backend/apps/productos/tests.py` — Tests CRUD básicos (+42 líneas)
- `backend/apps/productos/urls.py` — Endpoints GET/POST `/api/productos/`, PUT/DELETE `/api/productos/{id}/` (+10 líneas)
- `backend/apps/productos/views.py` — Vistas CRUD (+12 líneas, +6 fixes commit `2b8fd00f`)
- `backend/apps/productos/migrations/0001_initial.py` — Migración inicial (commit `36fa715d`)

**Archivos modificados:**
- `backend/config/settings/base.py` — Registro de `apps.productos` en `INSTALLED_APPS`

**Fix adicional:**
- Commit `36fa715d`: `fix: add migrations for productos app — resolves 500 on /api/productos/`
- Commit `2b8fd00f`: corrección en `views.py` de `productos` (+6 líneas)

**Pendiente:**
- Frontend: página productos con tabla, filtro por brand, FormModal + ConfirmDialog
- Sidebar actualizado con enlace a Productos

---

### S11-12 — Tests finales Sprint 11
**Branch objetivo:** `feat/sprint11-cleanup`
**Depende de:** S11-01 a S11-11

**Desarrollo:**
No ejecutado. Requiere que Fase 0 completa esté terminada.

---

## ARCHIVOS DE PLANIFICACIÓN CREADOS

En el commit `81a20a5f` se subieron los archivos de planificación del Sprint 11 a la carpeta `Sprints/`:

| Archivo | Líneas | Descripción |
|---------|--------|-------------|
| `Sprints/GUIA_ALE_SPRINT11.md` | 158 | Guía de implementación para Alejandro |
| `Sprints/LOTE_SM_SPRINT11.md` | 416 | LOTE completo del Sprint 11 |
| `Sprints/PROMPT_ANTIGRAVITY_SPRINT11.md` | 275 | Prompt de ejecución Antigravity |

---

## OTROS ARCHIVOS MODIFICADOS / CREADOS (SPRINT 11)

### Backend — Infraestructura y fixes

| Archivo | Tipo | Commit | Descripción |
|---------|------|--------|-------------|
| `backend/apps/core/urls_ui.py` | Modificado | `81a20a5f` | +3 rutas, -1 ruta legacy |
| `backend/apps/core/views.py` | Modificado | `81a20a5f` | Ajuste de vistas (+4, -4 líneas) |
| `backend/apps/expedientes/urls_ui.py` | Modificado | `81a20a5f` | -3 rutas eliminadas |
| `backend/apps/knowledge/migrations/0002_alter_conversationlog_user.py` | Creado | `81a20a5f` | Migración FK user en ConversationLog |
| `backend/apps/users/migrations/0003_alter_mwtuser_groups.py` | Creado | `81a20a5f` | Migración grupos usuario |
| `backend/apps/users/migrations/0004_mwtuser_is_blocked.py` | Creado | `81a20a5f` | Campo `is_blocked` en MWTUser |
| `backend/apps/users/models.py` | Modificado | `81a20a5f` | +3 líneas (campo is_blocked) |
| `backend/apps/expedientes/services.py` | Modificado | `fa990412` | +50 líneas, -2 (lógica de servicios) |
| `backend/apps/expedientes/models.py` | Modificado | `fa990412` | +29 líneas (nuevos campos) |

### Backend — Fixes de migración (commits fix del día)

| Commit | Archivo | Descripción |
|--------|---------|-------------|
| `a108fff` | `backend/apps/core/urls_ui.py` | Registrar `FinancialDashboardView` → fix 404 |
| `bdc3f4d` | `backend/apps/expedientes/migrations/0012_...py` | FK `nodo_destino` faltante → fix 500 en `/api/ui/` |
| `f14dd26` | `backend/apps/expedientes/migrations/0012_...py` | No-op SeparateDatabaseAndState — columna ya existe |

### Scripts y Knowledge Base

| Archivo | Tipo | Commit | Descripción |
|---------|------|--------|-------------|
| `scripts/ENT_OPS_CASO_2391.md` | Creado | `fa990412` | Caso operativo (245 líneas) |
| `knowledge/MWT_KB_2026-03-13/ARTIFACT_REGISTRY.md` | Modificado | `fa990412` | +4, -2 líneas |
| `knowledge/MWT_KB_2026-03-13/ENT_COMERCIAL_COSTOS.md` | Modificado | `fa990412` | +29, -9 líneas |
| `knowledge/run_now.py` | Creado | `fa990412` | Script de ejecución knowledge (+9 líneas) |
| `verify_fields.py` | Creado | `fa990412` | Script de verificación de campos (+27 líneas) |
| `backend/check_settings.py` | Creado | `81a20a5f` | Script de verificación de settings (+17 líneas) |
| `backend/config/settings/test.py` | Creado | `81a20a5f` | Configuración de tests (+26 líneas) |

---

## RESUMEN DE COMMITS SPRINT 11

| Commit SHA | Fecha | Descripción | +/- Líneas |
|------------|-------|-------------|-----------|
| `81a20a5f` | 19-03-2026 18:42 | cambios varios 20260319 (bulk Sprint 11) | +2108 / -246 |
| `2b8fd00f` | 19-03-2026 18:54 | Fix productos/views.py | +6 |
| `36fa715d` | 19-03-2026 18:57 | Fix migraciones app productos | — |
| `fa990412` | 19-03-2026 19:16 | cambios varios 20260319 (enums, services, KB) | +466 / -13 |
| `a108fff` | 19-03-2026 19:18 | Fix FinancialDashboardView route | — |
| `bdc3f4d` | 19-03-2026 19:23 | Fix migración 0012 nodo_destino FK | — |
| `f14dd26` | 19-03-2026 19:25 | Fix no-op migration 0012 | — |

---

## OBSERVACIONES IMPORTANTES

1. **Las ramas `feat/sprint11-*` NO fueron creadas.** Todo el trabajo se hizo directamente sobre `main`, lo que no sigue el workflow definido en el LOTE.

2. **Fase 0 incompleta.** De las 9 tareas de limpieza (S11-01 a S11-09), solo S11-08 tiene avance significativo. Las tareas de eliminación de estados legacy, rutas duplicadas, hex hardcodeados y accesibilidad están pendientes.

3. **Fase 1 iniciada antes de completar Fase 0.** Tanto `portal` (S11-10) como `productos` (S11-11) fueron creadas en backend, cuando el prerequisito era `S11-01 a S11-09 DONE`.

4. **Migraciones de corrección el mismo día.** Los 3 commits de fix (`a108fff`, `bdc3f4d`, `f14dd26`) indican errores en migraciones que tuvieron que corregirse en caliente.

5. **S11-12 (Tests finales) no puede ejecutarse** hasta que Fase 0 esté completa.

---

*Documento generado automáticamente a partir del historial de commits del repositorio [github.com/Ale241302/mwt_one](https://github.com/Ale241302/mwt_one)*
