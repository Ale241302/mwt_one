# ENT_PLAT_CANALES — Canales de Venta y Go-to-Market
status: DRAFT
visibility: [INTERNAL]
domain: Plataforma (IDX_PLATAFORMA)
version: 1.0

---

## A. Canales definidos

| # | Canal | Marca(s) | Status | Módulo principal |
|---|-------|---------|--------|-----------------|
| 1 | Amazon FBA | Rana Walk | ACTIVO (Goliath) | marketplace/ |
| 2 | Walmart Marketplace | Rana Walk | PLANIFICADO | marketplace/ |
| 3 | DTC (ranawalk.com) | Rana Walk | PLANIFICADO | orders/ + ENT_PLAT_FRONTENDS (SSR) |
| 4 | MCP / IA (Agentic Commerce) | Rana Walk | PLANIFICADO | ref → ENT_PLAT_AGENTIC |
| 5 | Distribución B2B | Marluvas, Tecmater, RW futuro | ACTIVO (Marluvas) | expedientes/ + distribution/ |
| 6 | Expedientes Import/Export | Todas | ACTIVO (Marluvas) | expedientes/ |

Decisión CEO (sesión 5): cada canal tiene flujo nativo con reglas diferenciadas de inventario, ads, pricing y forecast.

## B. Ciclo Go-to-Market por canal (3 fases)

| Fase | Objetivo | Reglas diferenciadas |
|------|---------|---------------------|
| Entrada | Llegar al mercado, setup, primeras ventas | Inventario mínimo, PPC agresivo (si marketplace), listing/profile setup |
| Mantenimiento | Optimizar, mantener ranking/posición, controlar costos | Inventario estable, PPC optimizado, reviews management |
| Crecimiento | Escalar PPC, lanzar productos, expandir mercados | Inventario scale-up, nuevos SKUs, forecast avanzado |

Cada canal × fase tiene reglas operativas específicas. Ref → playbooks por canal (PLB_OPS_AMAZON para canal 1, [PENDIENTE — por crear] para canales 2-6).

## C. Relación canal ↔ flujo expediente

| Canal | Usa expedientes | Usa artefactos | Flujo automático |
|-------|----------------|---------------|-----------------|
| Amazon FBA | No — fulfillment directo FBA | No | Inventory replenishment + PPC vía SP-API |
| Walmart | No — fulfillment WFS | No | Similar Amazon, reglas ads diferentes |
| DTC | No — checkout directo | No | Orden → fulfillment propio o 3PL |
| MCP / IA | No — transacción vía API | No | ref → ENT_PLAT_AGENTIC (UCP/ACP) |
| Distribución B2B | Sí — expediente por operación | Sí — combo por brand+mode | ref → ENT_OPS_EXPEDIENTE + ENT_PLAT_ARTEFACTOS |
| Expedientes Import/Export | Sí — centro de operaciones | Sí — catálogo completo ART-01..12 | ref → ENT_PLAT_MVP |

## D. Feature flag por SKU en canales

Decisión CEO (sesión 5): MCP Server necesita catálogo de 657 SKUs con toggle on/off por SKU — puede ser que no se tenga permiso para todos.

Aplica a todos los canales: cada SKU puede estar habilitado/deshabilitado por canal.
Ref → catalog/ (campo `channel_enabled[]` por SKU, [PENDIENTE — ARCH]).

## E. Escalamiento distribución (decisión CEO sesión 5)

Rana Walk al escalar en distribuidores:
- Flujos automáticos con forecast
- Balanceo inventarios regionales, locales, de cliente
- Franquiciado master con sub-franquicias o distribuidores e influencers
- Cada nivel = flujo de comportamiento nativo diferente pero adaptable

Ref → ENT_DIST_DISTRIBUIDORES para detalle de estructura distribución.

---

Stamp: DRAFT — Pendiente aprobación CEO
