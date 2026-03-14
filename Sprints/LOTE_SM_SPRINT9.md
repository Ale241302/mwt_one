# LOTE_SM_SPRINT9 — UX Batch + Pipeline
status: FROZEN — Aprobado para ejecución
visibility: INTERNAL
stamp: CONGELADO v2.0 — Aprobado CEO 2026-03-13
domain: Plataforma (IDX_PLATAFORMA)
version: 2.0
sprint: 9
priority: P0
depends_on: LOTE_SM_SPRINT8
refs: ENT_PLAT_FRONTENDS, ENT_OPS_STATE_MACHINE, ENT_PLAT_ARTEFACTOS, ENT_GOB_PENDIENTES, ARTIFACT_REGISTRY, ENT_PLAT_DESIGN_TOKENS
revisado_por: Arquitecto (Claude) — 2026-03-13
auditado_por: ChatGPT (GPT-5 Thinking) D1/D2/D3/D6, Gemini (3.1 Pro) D4/D7/D8, Claude (Opus 4.6) D5 — 2026-03-13
audit_baseline_score: 5.9/10 (BLOQUEADO — pre-Sprint 9)
audit_ref: REPORTE_AUDIT_BASELINE_20260313.md

---

## Objetivo

Rediseñar la experiencia de usuario de consola.mwt.one. Tres ejes:
1. Vista Pipeline Kanban como interfaz principal de operación.
2. Detalle de expediente con flujo de artefactos guiado por estado.
3. Módulos de gestión (Liquidación, Nodos, Transfers, Clientes, Brands, Usuarios).

**No es un sprint puramente frontend.** Incluye 1 fix backend (S9-11: `/api/transfers/` 500 error) y endpoints CRUD para Clientes (S9-13). El resto consume APIs existentes de Sprints 1–8.

**Decisión arquitectónica CEO 2026-03-13:** Kanban es la vista default del pipeline.

---

## Bloqueador

Sprint 8 DONE (MWTUser + JWT). Confirmado por CEO: Sprint 8 ejecutado, Ale entrega tareas finales 2026-03-14.

---

## Fases y orden de ejecución

### Fase 0 — Fix fundacional (Prerequisito)

| Item  | Tarea                                                | Agente | Depende de | Prioridad  |
|-------|------------------------------------------------------|--------|-----------|------------|
| S9-01 | Corregir dropdown de estados a state machine canónica | AG-03  | Nada      | Bloqueador |
| S9-02 | Corregir timeline del detalle de expediente          | AG-03  | Nada      | Bloqueador |
| S9-03 | Sidebar: actualizar navegación real + border-left Mint| AG-03  | Nada      | Bloqueador |
| S9-16 | Alinear identidad visual con ENT_PLAT_DESIGN_TOKENS  | AG-03  | Nada      | Bloqueador |

### Fase 1 — Kanban pipeline + detalle con artefactos (P0)

| Item  | Tarea                                               | Agente | Depende de  | Prioridad |
|-------|-----------------------------------------------------|--------|------------|----------|
| S9-04 | Vista Kanban pipeline                               | AG-03  | S9-01, S9-03| P0       |
| S9-05 | Detalle expediente con acordeón de artefactos       | AG-03  | S9-02      | P0       |
| S9-06 | Dashboard mejorado con mini-pipeline                | AG-03  | S9-04      | P0       |
| S9-07 | Flujos de acción inline (modals de artefactos)      | AG-03  | S9-05      | P0       |

### Fase 2 — Liquidación Marluvas UI (PLT-06, P1)

| Item  | Tarea                                    | Agente | Depende de | Prioridad |
|-------|------------------------------------------|--------|-----------|----------|
| S9-08 | Ruta /liquidaciones — lista              | AG-03  | Nada      | P1       |
| S9-09 | Detalle liquidación — reconciliación visual| AG-03 | S9-08     | P1       |

### Fase 3 — Nodos + Transfers UI (PLT-04/05, P1)

| Item  | Tarea                                  | Agente       | Depende de       | Prioridad |
|-------|----------------------------------------|--------------|-----------------|----------|
| S9-10 | Ruta /nodos — grid de nodos logísticos | AG-03        | Nada             | P1       |
| S9-11 | Fix /api/transfers/ 500 error          | AG-02        | Nada             | P1       |
| S9-12 | Ruta /transfers — lista + detalle      | AG-03        | S9-10, S9-11     | P1       |

### Fase 4 — Clientes + Brands + Usuarios CRUD (PLT-03/07/02, P2)

| Item  | Tarea                                  | Agente          | Depende de | Prioridad |
|-------|----------------------------------------|-----------------|-----------|----------|
| S9-13 | Ruta /clientes — CRUD completo         | AG-03 + AG-02   | Nada      | P2       |
| S9-14 | Ruta /brands — CRUD de marcas          | AG-03           | Nada      | P2       |
| S9-15 | Ruta /usuarios — gestión multi-usuario | AG-03 + AG-02   | Sprint 8  | P2       |

---

## Pendientes abiertos en este sprint

| ID     | Pendiente                                              | Bloqueador | Quién resuelve |
|--------|--------------------------------------------------------|-----------|----------------|
| S9-P01 | URL exacta endpoint liquidaciones (ART-10)             | Ale confirma post Sprint 8 | AG-02 |
| S9-P02 | Endpoint `/api/nodes/` — ¿existe o hay que crear?     | Ale confirma | AG-02 |
| S9-P03 | Endpoint CRUD completo para clientes (POST/PUT)        | Backend Sprint 9 | AG-02 |
| S9-P04 | URL exacta endpoints MWTUser post Sprint 8             | Ale entrega 2026-03-14 | AG-02 |
| S9-P05 | Campo `by_status` en `/api/ui/dashboard/`              | Backend Sprint 9 | AG-02 |

---

## Criterio de DONE del sprint

1. Todas las rutas nuevas responden y renderizan sin error.
2. Kanban pipeline muestra expedientes correctamente distribuidos por estado canónico.
3. Detalle de expediente muestra artefactos por estado con status correcto.
4. Al menos 3 modals de artefactos funcionan end-to-end (ART-01, ART-05, ART-09 como mínimo).
5. Liquidaciones: upload Excel procesa y muestra tabla comparativa.
6. Nodos: CRUD funcional con grid de cards.
7. Transfers: lista y detalle renderizan con datos reales.
8. Sidebar refleja todas las rutas nuevas.
9. No hay regresiones en funcionalidad existente (dashboard, expedientes lista, financiero).

---

## Lo que NO entra en Sprint 9 (→ Sprint 10+)

| Tarea                                  | Sprint destino | Razón                                |
|----------------------------------------|----------------|--------------------------------------|
| Portal B2B cliente (portal.mwt.one)    | Sprint 10      | Groundwork de permisos listo en S9   |
| Vista Calendario de expedientes         | Sprint 10      | Pipeline + Tabla cubren operación    |
| Módulo Configuración                   | Sprint 10      | Depende de Sprint 9 completo         |
| Módulo Productos (PLT-09)              | Sprint 10      | Depende de Brands + Nodos            |
| Módulo Inventario (PLT-10)             | Sprint 11      | Depende de Productos                 |
| Paperless bidireccional (PLT-01)       | Sprint 10      | Webhook no activo                    |
| Espejo documental PDF                  | Sprint 10      | Depende de Paperless bidireccional   |

*Documento: LOTE_SM_SPRINT9.md v2.0 CONGELADO — 2026-03-14*
