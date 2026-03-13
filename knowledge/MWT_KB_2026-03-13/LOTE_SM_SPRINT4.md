# LOTE_SM_SPRINT4 — Frontend Dashboard, Detalle Expediente, ART-09 Doble Vista
status: DONE — CERRADO · 12/12 items · 0 pendientes
visibility: INTERNAL
domain: Plataforma (IDX_PLATAFORMA)
version: 1.0
sprint: 4
depends_on: LOTE_SM_SPRINT3
nota_git: PRs nombradas feat/sprint7-item{8..13} en git — naming inconsistente, contenido correcto. No afecta funcionalidad.

---

## Objetivo

Frontend de la consola mwt.one — dashboard, lista expedientes, detalle, factura ART-09 con doble vista CEO/cliente. MinIO storage. Paperless-ngx unidireccional (Django → Paperless).

---

## Items ejecutados

| Item | Tarea | Agente | Estado |
|------|-------|--------|--------|
| S4-01 | Dashboard home (KPIs: expedientes activos, alertas crédito, bloqueados) | AG-03 | ✅ Done |
| S4-02 | Lista expedientes con filtros por estado y marca | AG-03 | ✅ Done |
| S4-03 | ART-09 Factura MWT — Generación + Doble Vista CEO/cliente | AG-03 | ✅ Done |
| S4-04 | Detalle expediente — timeline, datos, lista artefactos | AG-03 | ✅ Done |
| S4-05 | Dashboard financiero — totales y desglose por marca | AG-03 | ✅ Done |
| S4-06 | Navegación entre los 3 módulos (dashboard, expedientes, financiero) | AG-03 | ✅ Done |
| S4-07 | Componentes UI con ENT_PLAT_DESIGN_TOKENS | AG-03 | ✅ Done |
| S4-08 | Upload archivos multipart/form-data para artefactos con PDF | AG-03 | ✅ Done |
| S4-09 | MinIO storage integración para archivos de artefactos | AG-07 | ✅ Done |
| S4-10 | Mirror PDF (espejo documental para cliente) — endpoint backend | AG-02 | ✅ Done |
| S4-11 | Paperless-ngx — integración unidireccional Django → Paperless | AG-02 | ✅ Done |
| S4-12 | Tests Sprint 4 (frontend + backend + no-regresión S1-S3) | AG-06 | ✅ Done |

---

## Aclaraciones

- **S4-05 Dashboard financiero:** es la única vista P&L existente. El ítem S6-10 del Sprint 6 ("Dashboard P&L") NO es una funcionalidad adicional — es esta misma vista. Confirmado Alejandro 2026-03-12. No duplicar.
- **Paperless-ngx:** S4-11 implementa solo la dirección Django → Paperless. La dirección inversa (bidireccional/webhook) es pendiente PLT-01 en ENT_GOB_PENDIENTES.

---

## Cierre

- Items: 12/12 ✅ Done
- Pendientes: ninguno
- Tareas pasadas a otro sprint: ninguna

---

Stamp: DONE — CERRADO · 12/12 items · 0 pendientes · Confirmado auditoría 2026-03-12
Tareas pasadas: ninguna.
