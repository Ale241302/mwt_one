# PLAN_IMPLEMENTACION_SPRINT9.MD
# MWT ONE — Sprint 9: UX Batch + Pipeline
# Estado: CONGELADO v2.0 — Aprobado CEO 2026-03-13
# Dominio: Plataforma (IDX_PLATAFORMA)
# Depende de: Sprint 8 (MWTUser + JWT + mwt-knowledge)

---

## Objetivo

Rediseñar la experiencia de usuario completa de consola.mwt.one.
Pasar de tabla estática de expedientes a un **pipeline operativo guiado**
donde el CEO siempre sepa qué hacer next.

**Score baseline auditoría (2026-03-13): 5.9/10 — BLOQUEADO**
**Score objetivo al cierre del sprint: 9.5/10**

Tres ejes:
1. Vista Pipeline Kanban como interfaz principal de operación.
2. Detalle de expediente con flujo de artefactos guiado por estado.
3. Módulos de gestión (Liquidación, Nodos, Transfers, Clientes, Brands, Usuarios).

---

## Branches del sprint

| Branch                          | Items                  |
|---------------------------------|------------------------|
| feat/s9-fase0-fixes             | S9-01, S9-02, S9-03, S9-16 |
| feat/s9-kanban-pipeline         | S9-04                  |
| feat/s9-detalle-acordeon        | S9-05                  |
| feat/s9-dashboard-mejorado      | S9-06                  |
| feat/s9-artifact-modals         | S9-07                  |
| feat/s9-liquidaciones           | S9-08, S9-09           |
| fix/s9-transfers-500            | S9-11                  |
| feat/s9-nodos-transfers         | S9-10, S9-12           |
| feat/s9-clientes-brands-usuarios| S9-13, S9-14, S9-15    |

---

## Fases y orden de ejecución

| Fase | Items               | Qué resuelve                        | Depende de    | Score target |
|------|---------------------|-------------------------------------|---------------|-------------|
| 0    | S9-01, S9-02, S9-03, S9-16 | Fixes fundacionales         | Nada          | 8.0+        |
| 1    | S9-04, S9-05, S9-06, S9-07 | Kanban + detalle + modals   | Fase 0        | 9.0+        |
| 2    | S9-08, S9-09        | Liquidación Marluvas UI             | Nada          | —           |
| 3    | S9-10, S9-11, S9-12 | Nodos + Transfers                   | S9-10 antes   | —           |
| 4    | S9-13, S9-14, S9-15 | Clientes + Brands + Usuarios        | Sprint 8      | 9.5+        |

---

## FASE 0 — Fixes fundacionales (Bloqueador)

### S9-01 — Corregir dropdown de estados
- **Agente:** AG-03 Frontend
- **Branch:** feat/s9-fase0-fixes
- **Archivo:** app/[lang]/(mwt)/(dashboard)/expedientes/page.tsx
- **Estado:** ⏳ PENDIENTE
- **Descripción:** Eliminar EVALUACION_PREVIA, FORMALIZACION, QC, ENTREGA del dropdown.
  Dejar solo los 8 estados canónicos de ENT_OPS_STATE_MACHINE v1.2.2.
- **Los 8 estados (en orden):** REGISTRO, PRODUCCION, PREPARACION, DESPACHO, TRANSITO,
  EN_DESTINO, CERRADO, CANCELADO
- **Implementación ideal:**
  ```ts
  // constants/states.ts
  export const CANONICAL_STATES = [
    'REGISTRO', 'PRODUCCION', 'PREPARACION', 'DESPACHO',
    'TRANSITO', 'EN_DESTINO', 'CERRADO', 'CANCELADO'
  ] as const;
  ```
- **Criterio DONE:** Dropdown muestra exactamente 8 estados. CANONICAL_STATES exportada.

---

### S9-02 — Corregir timeline del detalle de expediente
- **Agente:** AG-03 Frontend
- **Branch:** feat/s9-fase0-fixes
- **Archivo:** app/[lang]/(mwt)/(dashboard)/expedientes/[id]/page.tsx
- **Estado:** ⏳ PENDIENTE
- **Descripción:** Reemplazar los 7 pasos incorrectos por los estados canónicos.
  - Quitar: 'Facturado' (es ART-09, no estado)
  - Agregar: 'Despacho' entre Preparación y Tránsito
  - Agregar: indicador CANCELADO como badge rojo lateral (no como paso lineal)
- **Timeline correcto (7 pasos lineales):**
  Registro → Producción → Preparación → Despacho → Tránsito → En destino → Cerrado
- **Criterio DONE:** 7 pasos canónicos. CANCELADO badge lateral. Pulse con reduced-motion.

---

### S9-03 — Sidebar: navegación real + border-left Mint
- **Agente:** AG-03 Frontend
- **Branch:** feat/s9-fase0-fixes
- **Archivo:** app/[lang]/(mwt)/(dashboard)/layout.tsx
- **Estado:** ⏳ PENDIENTE
- **Criterio DONE:** 11 items, border Mint visible, toggle funciona, aria-label.

---

### S9-16 — Alinear identidad visual con ENT_PLAT_DESIGN_TOKENS
- **Agente:** AG-03 Frontend
- **Branch:** feat/s9-fase0-fixes
- **Estado:** ⏳ PENDIENTE
- **Fix 1:** General Sans cargada
- **Fix 2:** Refs en mono
- **Fix 3:** Badges globales uppercase + letter-spacing
- **Fix 4:** Card radius-xl (12px)
- **Fix 5:** Dark mode CSS variables
- **Criterio DONE:** 5 fixes aplicados. General Sans cargada. Badges con tokens.

---

## FASE 1 — Kanban + Detalle + Modals (P0)

### S9-04 — Vista Kanban pipeline
- **Branch:** feat/s9-kanban-pipeline
- **Ruta:** /pipeline (vista DEFAULT)
- **Estado:** ⏳ PENDIENTE
- **Criterio DONE:** 6 columnas con datos reales. Semáforo siempre texto+color+ícono.

### S9-05 — Detalle expediente con acordeón de artefactos
- **Branch:** feat/s9-detalle-acordeon
- **Ruta:** /expedientes/[id]
- **Estado:** ⏳ PENDIENTE
- **Criterio DONE:** Acordeón funcional. Gate visible. Sin emojis. Copy aprobado.

### S9-06 — Dashboard mejorado con mini-pipeline
- **Branch:** feat/s9-dashboard-mejorado
- **Estado:** ⏳ PENDIENTE
- **Criterio DONE:** Mini-pipeline con conteos reales. Click navega. Top 3 acciones.

### S9-07 — Flujos de acción inline — modals de artefactos
- **Branch:** feat/s9-artifact-modals
- **Estado:** ⏳ PENDIENTE
- **Criterio DONE:** ART-01, ART-05, ART-09 end-to-end. Modal cierra y pipeline actualiza.

---

## FASE 2 — Liquidación Marluvas UI (P1)

### S9-08 — Lista de liquidaciones (/liquidaciones)
- **Branch:** feat/s9-liquidaciones
- **Estado:** ⏳ PENDIENTE
- **Pendiente backend (S9-P01):** URL exacta endpoint ART-10

### S9-09 — Detalle liquidación — reconciliación visual
- **Branch:** feat/s9-liquidaciones
- **Estado:** ⏳ PENDIENTE
- **Criterio DONE:** Upload Excel procesa. Tabla comparativa muestra. Aprobación bulk funciona.

---

## FASE 3 — Nodos + Transfers UI (P1)

### S9-10 — Grid de nodos logísticos (/nodos)
- **Branch:** feat/s9-nodos-transfers
- **Estado:** ⏳ PENDIENTE
- **Pendiente backend (S9-P02):** verificar si /api/nodes/ existe

### S9-11 — Fix /api/transfers/ — error 500
- **Branch:** fix/s9-transfers-500
- **Estado:** ⏳ PENDIENTE
- **Criterio DONE:** GET /api/transfers/ retorna 200. Sin errores en logs.

### S9-12 — Lista + detalle de transfers (/transfers)
- **Branch:** feat/s9-nodos-transfers
- **Estado:** ⏳ PENDIENTE
- **Criterio DONE:** Lista y detalle con datos reales. Mini-pipeline funcional.

---

## FASE 4 — Clientes + Brands + Usuarios CRUD (P2)

### S9-13 — Clientes CRUD (/clientes)
- **Branch:** feat/s9-clientes-brands-usuarios
- **Estado:** ⏳ PENDIENTE
- **Pendiente backend (S9-P03):** CRUD completo POST/PUT/DELETE

### S9-14 — Brands CRUD (/brands)
- **Branch:** feat/s9-clientes-brands-usuarios
- **Estado:** ⏳ PENDIENTE
- **GET /api/brands/ ya responde 200.** Verificar soporte POST/PUT.

### S9-15 — Usuarios — gestión multi-usuario (/usuarios)
- **Branch:** feat/s9-clientes-brands-usuarios
- **Estado:** ⏳ PENDIENTE
- **Pendiente (S9-P04):** URLs endpoints MWTUser post-Sprint 8

---

## Pendientes abiertos

| ID    | Qué verificar                                         | Antes de | Cómo reportar |
|-------|-------------------------------------------------------|----------|---------------|
| S9-P01| URL exacta endpoint liquidaciones (ART-10 Sprint 5)   | S9-08    | Msg al CEO    |
| S9-P02| ¿Existe /api/nodes/? Probe devolvió 404.              | S9-10    | Msg al CEO    |
| S9-P03| ¿Endpoint clientes soporta POST/PUT o solo GET?       | S9-13    | Msg al CEO    |
| S9-P04| URLs endpoints MWTUser post Sprint 8                  | S9-15    | Msg al CEO    |
| S9-P05| Campo by_status en /api/ui/dashboard/                 | S9-06    | Msg al CEO    |

---

## Criterio de DONE del sprint

- [ ] Todas las rutas nuevas responden y renderizan sin error.
- [ ] Kanban pipeline: expedientes distribuidos por estado canónico.
- [ ] Detalle: artefactos por estado con status correcto.
- [ ] Al menos 3 modals end-to-end: ART-01, ART-05, ART-09.
- [ ] Liquidaciones: upload Excel procesa y muestra tabla comparativa.
- [ ] Nodos: CRUD funcional con grid de cards.
- [ ] Transfers: lista y detalle renderizan con datos reales.
- [ ] Sidebar con todas las rutas nuevas + Mint border en item activo.
- [ ] Sin regresiones en dashboard, expedientes lista, financiero.
- [ ] General Sans cargada y usada en headings display.
- [ ] Badges con uppercase, letter-spacing y colores del design system.
- [ ] Semáforo de riesgo: color + texto + ícono en todas las vistas.
- [ ] Score auditoría global 9.5+ en Ronda 4.

---

*Documento generado: 2026-03-14 | Versión: v2.0 CONGELADO*
*Ref: LOTE_SM_SPRINT9.md v2.0 + GUIA_SPRINT9_ALEJANDRO.docx v2.0*
