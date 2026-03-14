# GUÍA SPRINT 9 — MWT.ONE UX Batch + Pipeline

**Para:** Alejandro (AG-02 Backend / AG-03 Frontend)
**De:** CEO + Arquitecto (Claude)
**Estado:** CONGELADO v2.0 — Aprobado para ejecución
**Fecha:** 13 de marzo de 2026

---

## 1. Qué es este documento

Esta guía contiene todo lo que necesitás para ejecutar el Sprint 9 de consola.mwt.one.
El Sprint 9 es un **rediseño de la experiencia de usuario completa** de la consola.
Objetivo: pasar de tabla estática de expedientes a un pipeline operativo guiado.

**Documentos de referencia en el proyecto (KB):**
- `LOTE_SM_SPRINT9.md` — el spec detallado (versión CONGELADA v2.0)
- `ENT_PLAT_DESIGN_TOKENS.md v1.1` — design system actualizado
- `ENT_OPS_STATE_MACHINE.md` — fuente de verdad de estados y transiciones
- `REPORTE_AUDIT_BASELINE_20260313.md` — auditoría con 20 fixes
- `PLB_AUDIT_UX_FRONTEND.md` — protocolo de auditoría por fases

---

## 2. Contexto: Auditoría baseline

**Score baseline: 5.9 / 10 — BLOQUEADO**

Problemas principales detectados:

| Severidad | Problema |
|-----------|----------|
| CRÍTICO | Dropdown estados con EVALUACION_PREVIA, FORMALIZACION, QC (no canónicos) |
| CRÍTICO | Timeline del detalle muestra 'Facturado' como estado (es ART-09) y falta DESPACHO |
| CRÍTICO | Detalle del expediente plano — CEO no sabe qué hacer next |
| MAYOR | General Sans no cargada — headings usan fuente body |
| MAYOR | Badges sin uppercase ni letter-spacing, colores Tailwind en vez del design system |
| MAYOR | Sidebar sin border-left Mint en item activo |
| MAYOR | Refs EXP-XXXXX en heading font en vez de mono |
| MAYOR | Semáforo de crédito sin color/badge visual |

---

## 3. Orden de ejecución

| Fase | Items             | Qué resuelve              | Depende de | Target |
|------|-------------------|---------------------------|------------|--------|
| 0    | S9-01 a S9-03 + S9-16 | Fixes fundacionales   | Nada       | 8.0+   |
| 1    | S9-04 a S9-07     | Kanban + detalle + modals | Fase 0     | 9.0+   |
| 2    | S9-08 a S9-09     | Liquidación Marluvas UI   | Nada       | —      |
| 3    | S9-10 a S9-12     | Nodos + Transfers         | Nodos antes| —      |
| 4    | S9-13 a S9-15     | Clientes + Brands + Usuarios | Sprint 8| 9.5+   |

---

## 4. Fase 0 — Fixes fundacionales

### S9-01: Corregir dropdown de estados
**Archivo:** `app/[lang]/(mwt)/(dashboard)/expedientes/page.tsx`

**Eliminar:** EVALUACION_PREVIA, FORMALIZACION, QC, ENTREGA

**8 estados correctos (en orden):**
REGISTRO, PRODUCCION, PREPARACION, DESPACHO, TRANSITO, EN_DESTINO, CERRADO, CANCELADO

```ts
// constants/states.ts
export const CANONICAL_STATES = [
  'REGISTRO', 'PRODUCCION', 'PREPARACION', 'DESPACHO',
  'TRANSITO', 'EN_DESTINO', 'CERRADO', 'CANCELADO'
] as const;
```

### S9-02: Corregir timeline del detalle
**Archivo:** `app/[lang]/(mwt)/(dashboard)/expedientes/[id]/page.tsx`

**Quitar:** 'Facturado' (no es estado, es ART-09)
**Agregar:** 'Despacho' entre Preparación y Tránsito
**Agregar:** indicador CANCELADO como badge rojo lateral

Timeline correcto (7 pasos): Registro → Producción → Preparación → Despacho → Tránsito → En destino → Cerrado

Estilos (ENT_PLAT_DESIGN_TOKENS E5):
- Completado: dot 16px, fondo Mint (#75CBB3), ícono check blanco
- Activo: dot 20px, fondo Navy (#013A57), animación pulse
- Futuro: dot 16px, hueco con borde dashed

```css
/* globals.css */
@keyframes timeline-pulse {
  0%   { box-shadow: 0 0 0 0 rgba(1,58,87,0.2); }
  70%  { box-shadow: 0 0 0 6px rgba(1,58,87,0); }
  100% { box-shadow: 0 0 0 0 rgba(1,58,87,0); }
}
.animate-timeline-pulse {
  animation: timeline-pulse 2s infinite cubic-bezier(0.4,0,0.2,1);
}
@media (prefers-reduced-motion: reduce) {
  .animate-timeline-pulse { animation: none; }
}
```

### S9-03: Sidebar completo
**Archivo:** `app/[lang]/(mwt)/(dashboard)/layout.tsx`

Orden del sidebar:
1. Dashboard → `/`
2. Pipeline → `/pipeline` (NUEVO)
3. Expedientes → `/expedientes`
4. Financiero → `/dashboard/financial`
5. Liquidaciones → `/liquidaciones` (NUEVO)
6. Nodos → `/nodos` (NUEVO)
7. Transfers → `/transfers` (NUEVO)
8. Clientes → `/clientes` (NUEVO)
9. Brands → `/brands` (NUEVO)
10. Usuarios → `/usuarios` (NUEVO)
11. Configuración → gris, badge 'Sprint 10', sin link

Fix item activo:
```css
/* ANTES */
border-l-4 border-transparent
/* DESPUÉS */
border-l-[3px] border-mint bg-[rgba(255,255,255,0.06)]
```

Toggle sidebar 64px / 240px:
```css
.transition-sidebar {
  transition-property: width, border-color, background-color;
  transition-duration: 300ms;
  transition-timing-function: cubic-bezier(0.2, 0, 0, 1);
}
```

Accesibilidad: `aria-label` + `title` en cada item cuando colapsado.

### S9-16: Alinear identidad visual

**Fix 1 — General Sans:** Agregar al Next.js font loader. Aplicar a display-xl, display-lg, display-md.

**Fix 2 — Refs en mono:**
```jsx
// ANTES
<h1 className="text-2xl font-display font-bold">EXP-e23f926b</h1>
// DESPUÉS
<span className="font-mono text-sm font-medium">EXP-e23f926b</span>
```

**Fix 3 — Badges globales:**
```css
text-transform: uppercase;
letter-spacing: 0.5px;
/* Success */ color: #0E8A6D; background: #F0FAF6;
/* Warning */ color: #B45309; background: #FFF7ED;
/* Critical */ color: #DC2626; background: #FEF2F2;
```

**Fix 4 — Card radius-xl:** `border-radius: var(--radius-xl)` (12px)

**Fix 5 — Dark mode CSS variables:**
```css
@media (prefers-color-scheme: dark), .dark {
  --bg: #0B1929;
  --surface: #0F2337;
  --text-primary: #F1F5F9;
  --interactive: #75CBB3;
}
```

**Sombras multicapa PROP-01:**
```css
--shadow-sm: 0 1px 2px rgba(1,58,87,0.04), 0 2px 8px -2px rgba(1,58,87,0.08);
```

---

## 5. Fase 1 — Kanban + Detalle + Modals

### S9-04: Vista Kanban pipeline
**Branch:** `feat/s9-kanban-pipeline`
**Ruta:** `/pipeline` (vista DEFAULT al abrir la consola)

**Estructura:**
- 6 columnas = REGISTRO, PRODUCCION, PREPARACION, DESPACHO, TRANSITO, EN_DESTINO
- CERRADO y CANCELADO solo accesibles por filtro
- Header de columna con conteo de expedientes

**Cada card muestra:**
- Ref (EXP-XXXXX) en font-mono, clickable al detalle
- Cliente (nombre)
- Marca (pill con color)
- Semáforo: AL DÍA / RIESGO / CRÍTICO — siempre color + texto + ícono Lucide
- Dots numerados por artefacto (verde=done, gris=pending, rojo=blocked)
- Acción pendiente en cursiva
- Si `is_blocked=true`: borde rojo izquierdo + badge BLOQUEADO

**Endpoint:** `GET /api/ui/expedientes/?status={estado}`

### S9-05: Detalle expediente con acordeón
**Branch:** `feat/s9-detalle-acordeon`
**Ruta:** `/expedientes/[id]` (rediseño completo)

**Endpoints:**
- `GET /api/ui/expedientes/{id}/` → datos + available_actions
- `GET /api/expedientes/{id}/costs/`
- `GET /api/expedientes/{id}/financial-summary/`
- `GET /api/expedientes/{id}/documents/`

### S9-06: Dashboard mejorado
**Branch:** `feat/s9-dashboard-mejorado`

Agregar:
- Barra horizontal mini-pipeline: 6 segmentos con conteo por estado
- Filtro semáforo: 3 botones toggle (verde/amarillo/rojo)
- Sección "Próximas acciones": top 3 expedientes con acción inmediata

**Pendiente backend (S9-P05):** verificar campo `by_status` en `/api/ui/dashboard/`

### S9-07: Modals de artefactos
**Branch:** `feat/s9-artifact-modals`

| Artefacto | Fields del modal                            | Command backend       |
|-----------|---------------------------------------------|-----------------------|
| ART-01    | Upload archivo + items[] (SKU, cant, precio)| C2 RegisterOC         |
| ART-02    | Líneas producto, montos, consecutivo        | C3 CreateProforma     |
| ART-03    | Select: COMISION / FULL                     | C4 DecideModeBC       |
| ART-04    | SAP ID, fecha fabricación                   | C5 RegisterSAPConfirmation |
| ART-05    | Tipo, carrier, origen, destino, tracking    | C7 RegisterShipment   |
| ART-06    | Monto, modo, freight_mode                   | C8 RegisterFreightQuote|
| ART-08    | NCM[], DAI%, permisos[]                     | C9 RegisterCustomsDocs|
| ART-07    | Aprobado por (nombre), fecha                | C10 ApproveDispatch   |
| ART-09    | Total cliente, moneda                       | C13 IssueInvoice      |

---

## 6. Fases 2, 3 y 4 — Módulos de gestión

### Fase 2 — Liquidaciones (S9-08, S9-09)
- **Lista:** Ruta `/liquidaciones` — Tabla: Período, Monto total, Expedientes, Estado, Fecha
- **Detalle:** Ruta `/liquidaciones/[id]` — Drag-and-drop Excel, tabla comparativa, aprobación bulk

### Fase 3 — Nodos + Transfers (S9-10 a S9-12)
- **S9-10 Nodos (/nodos):** Grid de cards — tipo, país, entidad legal, capabilities
- **S9-11 Fix /api/transfers/ 500:** Debuggear y arreglar ANTES de construir UI
- **S9-12 Transfers (/transfers):** Lista y detalle con mini-pipeline 6 estados

### Fase 4 — CRUD entities (S9-13 a S9-15)
- **S9-13 Clientes (/clientes):** Lista con búsqueda, detalle, CRUD completo
- **S9-14 Brands (/brands):** Grid cards, form crear/editar
- **S9-15 Usuarios (/usuarios):** Lista MWTUser, form con rol y permisos granulares

---

## 7. Copy exacto aprobado

### Empty states

| Ubicación                               | Copy aprobado                                                  |
|-----------------------------------------|----------------------------------------------------------------|
| Lista — columna Actividad               | Sin eventos registrados                                        |
| Detalle — acciones (CERRADO)            | Este expediente completó su flujo operativo.                   |
| Detalle — documentos vacío              | Los documentos adjuntos y PDFs generados aparecerán aquí.     |
| Detalle — artefactos vacío              | Sin artefactos en este expediente.                             |
| Detalle — costos vacío                  | Sin costos registrados para este expediente.                   |
| Dashboard financiero en cero            | No hay datos financieros registrados todavía.                  |
| Dashboard — tabla riesgo vacía          | Todos los expedientes están al día.                            |
| Dashboard — tabla bloqueados vacía      | Sin expedientes bloqueados actualmente.                        |

### Subtítulos de páginas nuevas

| Página         | Subtítulo                                               |
|----------------|---------------------------------------------------------|
| /expedientes   | Consulta y filtra expedientes por estado, cliente y riesgo. |
| /pipeline      | Vista operativa de expedientes activos por estado.      |
| /liquidaciones | Reconciliación de pagos Marluvas.                       |
| /nodos         | Red de puntos operativos.                               |
| /transfers     | Movimientos de producto entre nodos.                    |
| /clientes      | Gestión de clientes B2B.                                |
| /brands        | Configuración de marcas operativas.                     |
| /usuarios      | Gestión de acceso y roles.                              |

---

## 8. Componente: Semáforo de riesgo crediticio

Usar en TODAS las vistas con días de crédito. **NUNCA solo color — siempre color + texto + ícono.**

| Band  | Background | Text       | Texto visible | Ícono Lucide   |
|-------|------------|------------|---------------|----------------|
| GREEN | #F0FAF6    | #0E8A6D    | AL DÍA        | check-circle   |
| AMBER | #FFF7ED    | #B45309    | RIESGO        | alert-triangle |
| RED   | #FEF2F2    | #DC2626    | CRÍTICO       | alert-octagon  |

---

## 9. Pendientes por verificar

| ID    | Qué verificar                                         | Antes de |
|-------|-------------------------------------------------------|----------|
| S9-P01| URL exacta endpoint liquidaciones (ART-10 Sprint 5)   | S9-08    |
| S9-P02| ¿Existe /api/nodes/? Probe devolvió 404               | S9-10    |
| S9-P03| ¿Endpoint clientes soporta POST/PUT o solo GET?       | S9-13    |
| S9-P04| URLs endpoints MWTUser post Sprint 8                  | S9-15    |
| S9-P05| Campo by_status en /api/ui/dashboard/                 | S9-06    |

---

## 10. Protocolo de auditoría

| Ronda   | Cuándo                | Score target    |
|---------|-----------------------|-----------------|
| Ronda 1 | Completada (baseline) | 5.9/10 BLOQUEADO|
| Ronda 2 | Después de Fase 0     | 8.0+            |
| Ronda 3 | Después de Fase 1     | 9.0+            |
| Ronda 4 | Cierre del sprint     | **9.5+ = DONE** |

Auditores: ChatGPT (UX/copy/accesibilidad) + Gemini (código/visual) + Claude (endpoints/datos).

**Cualquier duda → mensaje al CEO. No adivines.**

*Documento: GUIA_SPRINT9_ALEJANDRO.md v2.0 — 2026-03-14*
