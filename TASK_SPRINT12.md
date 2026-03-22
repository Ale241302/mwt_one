# TASK_SPRINT12.md - Sprint 12 Execution Tracker

**Proyecto:** mwt_one
**Repositorio:** https://github.com/Ale241302/mwt_one
**Branch:** main
**Fecha inicio:** 2026-03-20

---

## FASE 0 — Refactorización Backend (P0 OBLIGATORIO)

| ID | Tarea | Status | Horas | Depende de |
|----|-------|--------|-------|------------|
| S12-01 | Dividir services.py (1,371 líneas) en 9 módulos | **PENDING** | 4h | - |
| S12-02 | Consolidar services_sprint5.py (312 líneas) en services/ | **PENDING** | 2h | S12-01 |
| S12-03 | Colapsar 18+ APIViews en CommandDispatchView | **PENDING** | 3h | S12-01 |
| S12-04 | drf-spectacular → Swagger /api/docs/ | **PENDING** | 2h | S12-03 |
| S12-05 | Paginación opt-in (3 vistas) + error envelope | **PENDING** | 2h | S12-04 |
| S12-06 | db_index (4 campos), scripts, console→logger.ts | **PENDING** | 2h | S12-05 |

---

## FASE 1 — CI/CD (PARALELO)

| ID | Tarea | Status | Horas | Depende de |
|----|-------|--------|-------|------------|
| S12-07 | Pipelines ci.yml y deploy.yml | **PENDING** | 4h | - (paralelo) |

---

## FASE 2 — Frontend + Features (SOLO DESPUÉS DE FASE 0 DONE)

| ID | Tarea | Status | Horas | Depende de |
|----|-------|--------|-------|------------|
| S12-08 | Hooks useFetch/useCRUD + migrar 3 páginas | **PENDING** | 3h | Fase 0 DONE |
| S12-09 | DrawerShell.tsx + useFormSubmit hook | **PENDING** | 2h | Fase 0 DONE |
| S12-10 | Carry-over Sprint 11 (Portal B2B / Productos) | **PENDING** | - | Fase 0 DONE |
| S12-11 | Módulo Inventario: InventoryEntry, 4 endpoints | **PENDING** | 4h | S12-10 |
| ~~S12-12~~ | ~~WhatsApp Business API~~ | **SKIP** | - | Meta condicional |

---

## QA

| ID | Tarea | Status | Horas | Depende de |
|----|-------|--------|-------|------------|
| S12-13 | Checklist tests: refactor, frontend, CI/CD, regresión | **PENDING** | 2h | S12-01 a S12-11 |

---

## Orden de Ejecución

### FASE 0 (Secuencial)
1. **S12-01** → Dividir services.py (PRIMERA)
2. **S12-02** → Consolidar services_sprint5.py (después de S12-01)
3. **S12-03** → Colapsar APIViews (después de S12-01, puede ser paralelo a S12-02)
4. **S12-04** → Documentación API con drf-spectacular
5. **S12-05** → Paginación opt-in + error responses
6. **S12-06** → Limpieza (db_index, scripts, logger.ts)

### FASE 1 (Paralelo a Fase 0)
7. **S12-07** → CI/CD Pipelines (independiente)

### FASE 2 (Solo después de Fase 0 + S12-07 DONE)
8. **S12-08** → Hooks useFetch/useCRUD
9. **S12-09** → DrawerShell.tsx + useFormSubmit
10. **S12-10** → Carry-over Sprint 11 (si aplica)
11. **S12-11** → Módulo Inventario

### QA
12. **S12-13** → Checklist de tests

---

## Dependencias

```
S12-01 ──┬── S12-02
         ├── S12-03
         │      ├── S12-04
         │      │      ├── S12-05
         │      │      │      └── S12-06
         │      │      │             └── [FASE 0 DONE]
         │      │      │                    ├── S12-08
         │      │      │                    ├── S12-09
         │      │      │                    ├── S12-10 ── S12-11
         │      │      │                    └── S12-13
         │      │      │
S12-07 ──┘ (paralelo)

S12-12 = SKIP (condicional Meta)
```

---

## Reglas HARD

1. **Tests como safety net:** pytest debe pasar ANTES y DESPUÉS de cada refactor sin modificar tests
2. **API contracts FROZEN:** URLs y shapes de request/response NO cambian
3. **services/__init__.py re-exporta TODO:** 22 símbolos accesibles vía `from apps.expedientes.services import X`
4. **Ningún archivo >300 líneas**
5. **Paginación opt-in, no global**
6. **Fase 2 BLOQUEADA hasta Fase 0 DONE**
7. **S12-12 OMITIDO** (WhatsApp Business API - condicional a Meta)

---

## Progreso

- [ ] Fase 0 completada
- [ ] Fase 1 completada
- [ ] Fase 2 iniciada
- [ ] QA pasada

**Último commit:** -
**Último push:** -