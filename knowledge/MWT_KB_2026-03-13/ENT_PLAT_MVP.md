# ENT_PLAT_MVP — Minimum Viable Product Centro de Operaciones
status: DRAFT
visibility: [INTERNAL]
domain: Plataforma (IDX_PLATAFORMA)
version: 1.0
validated_by: Gemini, ChatGPT, Claude — 2026-02-26

---

## A. Objetivo

Darle al CEO visibilidad en tiempo real de expedientes, costos y tiempos. Reemplazar Google Drive + correo + cabeza del CEO como sistema operativo de la empresa.

### A1. Usuario
- CEO (1 persona).
- ~50-100 expedientes activos.
- Solo Marluvas en Sprint 1-3. Tecmater y Rana Walk en iteraciones posteriores.

### A2. Stack
- Ref → ENT_PLAT_INFRA.B (stack MVP: 6 contenedores).
- 1 VPS Hostinger KVM 8 (ref → ENT_PLAT_INFRA.A).
- Sin: n8n, Windmill, Celery workers complejos, event bus Redis Streams. Todo eso es post-MVP.

### A3. Criterio de "hecho"
El CEO puede abrir el sistema, ver todos sus expedientes activos con estado y semáforo de tiempos, registrar costos, subir documentos, y saber cuánto gana por expediente. Sin abrir Google Drive ni buscar en correo.

---

## B. Qué entra en MVP

### B1. De Capa 0 — Núcleo (ref → ENT_OPS_EXPEDIENTE.B)
- ✅ Modelo Expediente con todos los campos base.
- ✅ State Machine con transiciones manuales (CEO cambia estado). Estados: ref → ENT_OPS_EXPEDIENTE.D.
- ✅ Event Log simple (tabla append-only, no event sourcing puro).

### B2. De Capa 1 — Capacidades (ref → ENT_OPS_EXPEDIENTE.C)
- ✅ Costos doble vista. Ref → ENT_OPS_EXPEDIENTE.C1.
- ✅ Documentos (MinIO upload + tags + link a expediente).
- ✅ Reloj de crédito (90d desde AWB/BL + alerta P10 — cron básico).
- ✅ Traductor códigos (SKUAlias mínimo: mapping cliente ↔ fábrica).
- ⏳ Modelo financiero: solo margen básico. Dos escenarios para después.
- ❌ Espejo documental PDF: se genera manualmente hasta que haya sistema.

### B3. De Capa 2 — Artefactos (ref → ENT_PLAT_ARTEFACTOS.D para matriz completa MVP)
- ✅ ART-01 OC Cliente (upload + metadata).
- ✅ ART-02 Proforma MWT (consecutivo + líneas).
- ✅ ART-05 AWB/BL (carrier, tracking, fechas, activa reloj crédito).
- ✅ ART-11 Registro costos (cost lines progresivas).
- ⏳ ART-06 Cotización flete (si alcanza sprint 3).
- ⏳ ART-09 Factura MWT (si alcanza sprint 3).
- ❌ ART-03 Decisión B/C: campo mode en expediente, no artefacto separado.
- ❌ ART-04 Confirmación SAP: campo + documento adjunto, no artefacto.
- ❌ ART-07 Aprobación despacho: workflow extra, post-MVP.
- ❌ ART-08 Docs aduanales: post-MVP.
- ❌ ART-10 Factura comisión: solo modo B, post-MVP.
- ❌ ART-12 Nota compensación: CEO-only, no desbloquea visibilidad.

### B4. UI
- ✅ Lista de expedientes con filtros (marca, estado, cliente).
- ✅ Vista detalle expediente (campos, estado, artefactos, costos, documentos).
- ✅ Timeline visual básica: línea horizontal con nodos por estado, semáforo verde/amarillo/rojo vs tiempos promedio.
- ✅ Dashboard resumen: expedientes activos, alertas crédito, total costos/margen.
- ❌ Dashboard financiero completo: post-MVP.
- ❌ Dashboard cliente (portal.mwt.one): post-MVP.

---

## C. Qué NO entra en MVP (explícitamente)

| Componente | Razón de exclusión | Cuándo entra |
|-----------|-------------------|-------------|
| Event sourcing puro | Overhead. Estado actual + log es suficiente. | Cuando haya 500+ expedientes |
| Plugin architecture | Overhead. Artefactos tipados primero. | Cuando haya 3er tipo de artefacto no previsto |
| Redis Streams event bus | No necesario con 1 usuario y <100 expedientes | Cuando haya múltiples consumers |
| n8n / Windmill | No necesario en MVP. Automatizaciones manuales. | Sprint 4+ |
| Celery workers complejos | Cron básico de Django es suficiente | Cuando haya tareas pesadas |
| Agentic commerce (UCP/ACP/MCP) | Feature de crecimiento, no de supervivencia | Después de MVP estable |
| Portal B2B (portal.mwt.one) | Solo CEO usa MVP | Cuando haya clientes en el sistema |
| ranawalk.com SSR | Sitio público es independiente del Centro Ops | En paralelo si hay recursos |
| Tecmater / Rana Walk en flujos | MVP = solo Marluvas. Las otras son más simples. | Sprint 5+ |
| Forecast / inteligencia operativa | Necesita data histórica que aún no existe | Cuando haya 6+ meses de data |

---

## D. Secuencia de construcción — 4 Sprints

### Sprint 0 — Infraestructura (Día 1-2)
- Stack MVP: ref → ENT_PLAT_INFRA.B (6 contenedores).
- Deploy en KVM 8. SSL para mwt.one.
- Criterio: el stack corre y responde en el navegador.

### Sprint 1 — Núcleo + Visibilidad (Día 3-8)
- Modelo Expediente + LegalEntity + campos base.
- State machine (estados canónicos ref → ENT_OPS_EXPEDIENTE.D, transiciones manuales CEO).
- Event log simple (tabla append-only).
- Artefactos mínimos: OC (upload) + Proforma (consecutivo + metadata).
- UI: lista expedientes + vista detalle + filtros.
- **Resultado: el CEO deja de vivir en Drive + cabeza.**

### Sprint 2 — Documentos + Tiempos (Día 9-14)
- Documentos (ref → ENT_OPS_EXPEDIENTE.C3): upload + tags + búsqueda + link a expediente.
- AWB/BL artefacto: carrier, tracking, fechas ETD/ETA.
- Reloj crédito 90d desde AWB/BL + alerta P10 (cron Django).
- Timeline visual básica con semáforos.
- **Resultado: el CEO ve qué está tarde sin perseguir correos.**

### Sprint 3 — Costos + Control (Día 15-21)
- Costos doble vista (ref → ENT_OPS_EXPEDIENTE.C1).
- Margen básico (ref → ENT_OPS_EXPEDIENTE.C2 — solo escenario 1 en MVP).
- SKUAlias mínimo (cliente ↔ fábrica).
- Dashboard resumen: top expedientes por riesgo (tiempo + crédito + costo).
- **Resultado: decisiones rápidas con datos, no arqueología de documentos.**

### Sprint 4 — Mejoras (Día 22+)
- Cotización flete y docs aduanales como artefactos.
- Factura MWT generación.
- Modelo financiero segundo escenario.
- Espejo documental PDF.
- Preparar para Tecmater (flujo simplificado, sin SAP).

---

## E. Dependencias de construcción

| Sprint | Depende de | Entities v3.0 que consume |
|--------|-----------|--------------------------|
| 0 | Nada | ENT_PLAT_INFRA |
| 1 | Sprint 0 | ENT_OPS_EXPEDIENTE, ENT_COMERCIAL_MODELOS |
| 2 | Sprint 1 | ENT_OPS_EXPEDIENTE.C3 (Docs), C4 (Crédito) |
| 3 | Sprint 2 | ENT_OPS_EXPEDIENTE.C1 (Costos), C5 (SKUAlias), ENT_COMERCIAL_PRICING |
| 4 | Sprint 3 | ENT_OPS_EXPEDIENTE.C2 (Financiero), C6 (Espejo) |

---

Stamp: DRAFT — Pendiente aprobación CEO

---

## F. Aclaraciones post-implementación — confirmadas 2026-03-12

### F1. Dashboard P&L (S6-10) — NO ES ENTREGABLE SEPARADO
El ítem S6-10 "Dashboard P&L por marca/cliente/período" del Sprint 6 **no existe como funcionalidad adicional**. Es la misma vista financiera implementada en Sprint 4 (S4-05 "Dashboard financiero — totales y desglose por marca"). Confirmado por Alejandro 2026-03-12.

**Implicación:** No generar spec, ítem ni LOTE para Dashboard P&L hasta que el CEO defina una funcionalidad genuinamente nueva que vaya más allá de S4-05.

### F2. Paperless-ngx — estado real
- Dirección Django → Paperless: ✅ operativo desde Sprint 4-5
- Dirección Paperless → Django (bidireccional/OCR/webhook): integración dejada lista para activar, webhook NO activo. Pendiente PLT-01 en ENT_GOB_PENDIENTES.

Stamp actualización: CEO 2026-03-12
