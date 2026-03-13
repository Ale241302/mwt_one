# ENT_PLAT_MODULOS — Módulos Funcionales del Sistema
status: DRAFT — Pendiente validación CEO
visibility: [INTERNAL]
domain: Plataforma (IDX_PLATAFORMA)
version: 1.0

---

## Visión General

MWT.ONE opera 3 líneas de negocio (Marluvas, Tecmater, Rana Walk) en 3 mercados (USA, CR, BR) a través de 12 módulos funcionales organizados en 4 fases de construcción.

Relación entre capas: ref → ENT_PLAT_SSOT
Stack técnico: ref → ENT_PLAT_DOCKER
Agentes de negocio: ref → ENT_GOB_AGENTES
Agentes técnicos: ref → PLB_ARCHITECT, PLB_API, PLB_FRONTEND, PLB_INTEGRATION, PLB_MIGRATION, PLB_QA, PLB_DEVOPS
Observabilidad: ref → ENT_PLAT_OBSERVABILIDAD
Arquitectura (frontends, infra): ref → ENT_PLAT_ARQUITECTURA

---

## FASE 1 — CORE

### M1: EXPEDIENTES (`expedientes/`)

| Aspecto | Detalle |
|---------|---------|
| Función | Gestión de procesos de importación (Marluvas → MWT → clientes) |
| Línea de negocio | Marluvas (principal), Tecmater |
| Status metodología | ✅ N1: 8 bloques · N2: 6 procesos · N3: 6 decisiones |
| Status construcción | ❌ Pendiente Architect |

**8 Bloques funcionales:**
1. Expediente — Proceso de importación, rastreo PO→entrega
2. Estado del Expediente — 8 estados, event sourcing append-only
3. Costos del Expediente — Desglose doble vista: internal [CEO-ONLY] vs client (distribuidor)
4. Modelo Financiero — Margen con 2 escenarios (aduana vs nacionalizado), arbitraje fiscal
5. Documentos — Adjuntos en MinIO, indexación automática por email (n8n)
6. Reloj de Crédito — 90 días desde AWB/BL, alertas P10, notificación fábrica 2d hábiles post-pago
7. Espejo Documental — PDF con códigos/precios del cliente, nunca costos de fábrica
8. Traductor de Códigos — Mapeo código cliente ↔ código fábrica ↔ SKU interno (SKUAlias)

**6 Procesos:**
1. Crear Expediente (CEO crea → estado "PI Solicitada" → auto-vincula entidad legal)
2. Recibir Documentos por Email (n8n detecta PI → MinIO → si AWB/BL activa Reloj)
3. Llenar Costos y Calcular Margen (CEO ingresa → sistema calcula → toggle impuestos)
4. Generar Documento para Cliente (Espejo + Traductor → PDF sin costos fábrica)
5. Monitorear Crédito y Cobrar (cron diario → alertas → pago → 2d hábiles → notificar fábrica)
6. Avanzar Estado (evento → append-only → evaluar transición → notificar)

**6 Decisiones resueltas (EXP-01 a EXP-06):**
- EXP-01: LegalEntity como modelo base, MWT emisor principal
- EXP-02: Reloj crédito 90d desde AWB/BL, alerta P10 a 80d
- EXP-03: Email indexer por pattern PI-XXXX en subject
- EXP-04: SKUAlias multi-owner (cliente, fábrica, customs, marketplace)
- EXP-05: Doble vista costos (internal_amount vs client_amount), PDF espejo
- EXP-06: Dos escenarios financieros, precios/impuestos editables, toggle manual

**Mapeo a Capa de Conocimiento:**

| Dato/Regla | Entity requerido | Status |
|------------|-----------------|--------|
| Bloques + procesos + decisiones | ENT_EXP_EXPEDIENTE | [PENDIENTE — por crear] |
| Costos doble vista | ENT_EXP_COSTOS | [PENDIENTE — por crear] |
| Modelo financiero | ENT_EXP_FINANCIERO | [PENDIENTE — por crear] |
| Documentos MinIO | ENT_EXP_DOCUMENTOS | [PENDIENTE — por crear] |
| Reloj crédito | ENT_EXP_CREDITO | [PENDIENTE — por crear] |
| Espejo documental | ENT_EXP_ESPEJO | [PENDIENTE — por crear] |
| Traductor códigos | ENT_EXP_TRADUCTOR | [PENDIENTE — por crear] |
| Workflows n8n | PLB_EXPEDIENTES | [PENDIENTE — por crear] |

**Dependencias:** core/ (LegalEntity), brands/ (issuing_entity), catalog/ (SKUAlias)

---

### M2: PRICING (`pricing/`)

| Aspecto | Detalle |
|---------|---------|
| Función | 3 estrategias de pricing enchufables. PriceTable versionada. ref → POL_INMUTABILIDAD |
| Línea de negocio | Todas |
| Status metodología | ❌ Pendiente N1 |
| Status construcción | ❌ Pendiente |

**Mapeo a Capa de Conocimiento:**

| Dato/Regla | Entity requerido | Status |
|------------|-----------------|--------|
| Price ladder | ENT_COMERCIAL_PRICING [CEO-ONLY] | ✅ Existe |
| Costos FOB, flete, Amazon fees | ENT_COMERCIAL_COSTOS [CEO-ONLY] | ✅ Existe |
| Fórmulas BE-ACoS, cash flow | ENT_COMERCIAL_FINANZAS [CEO-ONLY] | ✅ Existe |
| PriceTable versionada (effective_from/to) | [PENDIENTE — absorber de legacy SSOT_Data_Contracts] | PENDIENTE |

**Dependencias:** core/, brands/, catalog/

---

### M3: CORE (`core/`)

| Aspecto | Detalle |
|---------|---------|
| Función | Users, roles RBAC, LegalEntity, permisos. Todo depende de esto. |
| Línea de negocio | Todas |
| Status metodología | ❌ Pendiente N1 |
| Status construcción | ❌ Pendiente |

**10 Roles del sistema:**

| Rol | Plataforma | Alcance |
|-----|-----------|---------|
| CEO | mwt.one | TODO |
| Admin | mwt.one | CRUD catálogo, órdenes, expedientes. Sin CEO-ONLY |
| OpsManager | mwt.one | Inventario, pedidos, expedientes, payouts (crear no aprobar) |
| CreatorManager | mwt.one | Onboarding afiliados, contratos, content approvals |
| Viewer | mwt.one | Dashboards read-only |
| AIAgent | Ambas | Según etiqueta del agente. Service token |
| Distributor | ranawalk.com | Su inventario, órdenes, territorio |
| SubDistributor | ranawalk.com | Su stock local, órdenes, sucursales |
| Affiliate | ranawalk.com | Su ledger, métricas, comisión, estado pago |
| Anonymous | ranawalk.com | Catálogo público, localizador tiendas |

**Mapeo a Capa de Conocimiento:**

| Dato/Regla | Entity requerido | Status |
|------------|-----------------|--------|
| Etiquetas visibilidad | POL_VISIBILIDAD | ✅ Existe |
| Matriz acceso por rol | ENT_GOB_ACCESO | ✅ Existe (expandir con 10 roles) |
| 6 agentes de negocio | ENT_GOB_AGENTES | ✅ Existe |
| LegalEntity | ENT_PLAT_LEGAL_ENTITY | [PENDIENTE — por crear] |
| Acciones por riesgo | ENT_PLAT_SEGURIDAD | ✅ Existe (expandir) |

**Dependencias:** Ninguna (es la base)

---

### M4: CATÁLOGO (`catalog/`)

| Aspecto | Detalle |
|---------|---------|
| Función | Productos, SKUs, variantes, tallas, assets, SKUAlias |
| Línea de negocio | Todas |
| Status metodología | ❌ Pendiente N1 |
| Status construcción | ❌ Pendiente |

**Mapeo a Capa de Conocimiento:**

| Dato/Regla | Entity requerido | Status |
|------------|-----------------|--------|
| 5 productos Rana Walk (bloques A-F) | ENT_PROD_{GOL,VEL,ORB,LEO,BIS} | ✅ Existe |
| 6 tecnologías | ENT_TECH | ✅ Existe |
| Comparativa 8 beneficios × 5 productos | ENT_PROD_COMPARATIVA | ✅ Existe |
| Secuencia lanzamiento | ENT_PROD_LANZAMIENTO | ✅ Existe |
| Tallas (15 sistemas × 6 tallas × 4 mercados) | ENT_OPS_TALLAS | ✅ Existe |
| SKUAlias multi-owner | [PENDIENTE — absorber EXP-04 legacy a catalog/] | PENDIENTE |
| Productos Marluvas | [PENDIENTE — NO INVENTAR] | PENDIENTE |
| Productos Tecmater | [PENDIENTE — NO INVENTAR] | PENDIENTE |

**Dependencias:** core/, brands/

---

### M5: ÓRDENES (`orders/`)

| Aspecto | Detalle |
|---------|---------|
| Función | Órdenes multicanal, state machine |
| Línea de negocio | Todas |
| Status metodología | ❌ Pendiente N1 |
| Status construcción | ❌ Pendiente |

**Mapeo a Capa de Conocimiento:**

| Dato/Regla | Entity requerido | Status |
|------------|-----------------|--------|
| Canal Amazon FBA USA | ENT_MERCADO_USA | ✅ Existe |
| Config por mercado | ENT_MERCADO_{M} | ✅ Existe |
| Checkout enabled por país | ENT_MERCADO_{M} | [PENDIENTE — absorber legacy Country_Rules] |

**Dependencias:** core/, brands/, catalog/, pricing/

---

### M6: MARCAS (`brands/`)

| Aspecto | Detalle |
|---------|---------|
| Función | Config por marca, feature flags, issuing_entity |
| Línea de negocio | Todas |
| Status metodología | ❌ Pendiente N1 |
| Status construcción | ❌ Pendiente |

**3 Marcas:**

| Marca | Tipo | Issuing Entity | Status |
|-------|------|---------------|--------|
| Rana Walk | Marca propia (plantillas biomecánicas) | Muito Work Limitada | ACTIVO |
| Marluvas | Distribución (calzado seguridad BR) | Muito Work Limitada | ACTIVO |
| Tecmater | [PENDIENTE — NO INVENTAR] | [PENDIENTE] | [PENDIENTE] |

**Mapeo a Capa de Conocimiento:**

| Dato/Regla | Entity requerido | Status |
|------------|-----------------|--------|
| Identidad Rana Walk | ENT_MARCA_IDENTIDAD | ✅ Existe |
| Origen (4 capas) | ENT_MARCA_ORIGEN | ✅ Existe |
| Sello "American Technology Inside" | ENT_MARCA_SELLO | ✅ Existe |
| Propiedad intelectual | ENT_MARCA_IP | ✅ Existe |
| E-E-A-T (3 versiones) | ENT_MARCA_EEAT | ✅ Existe |
| Config multi-marca | ENT_PLAT_MARCAS | [PENDIENTE — por crear] |

**Dependencias:** core/

---

## FASE 2 — OPERACIONES

### M7: INVENTARIO (`inventory/`)

| Aspecto | Detalle |
|---------|---------|
| Función | Multi-nodo (FBA + bodega + 3PL), snapshots, semáforos, backorders |
| Línea de negocio | Rana Walk (FBA), Marluvas (bodega) |
| Status metodología | ❌ Pendiente N1 |
| Status construcción | ❌ Pendiente |

**3 Nodos de fulfillment:**

| Nodo | SSOT | Quién controla stock |
|------|------|---------------------|
| FBA-US | Amazon FBA (SP-API) | Amazon |
| OWN-WH (bodega) | PostgreSQL (inventory/) | Sistema MWT |
| 3PL-{ID} | WMS del 3PL | 3PL |

**Mapeo a Capa de Conocimiento:**

| Dato/Regla | Entity requerido | Status |
|------------|-----------------|--------|
| Safety stock 35d, semáforos | ENT_OPS_INVENTARIO | ✅ Existe |
| Regla PPC vs stock | ENT_OPS_INVENTARIO | ✅ Existe |
| Demand planning F1-F4 | ENT_OPS_DEMAND_PLANNING | ✅ Existe |
| 4 rutas × 3 escenarios | ENT_OPS_LOGISTICA | ✅ Existe |
| Empaque físico | ENT_OPS_EMPAQUE_FISICO | ✅ Existe |
| Inventario multi-nodo, ledger, oversell | [PENDIENTE — absorber legacy Inventory_Operations] | PENDIENTE |

**Dependencias:** core/, catalog/

---

### M8: MARKETPLACE (`marketplace/`)

| Aspecto | Detalle |
|---------|---------|
| Función | Conectores Amazon/Walmart/ML normalizados |
| Línea de negocio | Rana Walk |
| Status metodología | ❌ Pendiente N1 |
| Status construcción | ❌ Pendiente |

**Mapeo a Capa de Conocimiento:**

| Dato/Regla | Entity requerido | Status |
|------------|-----------------|--------|
| Competencia | ENT_MKT_COMPETENCIA [CEO-ONLY] | ✅ Existe |
| Keywords | ENT_MKT_KEYWORDS | ✅ Existe |
| Amazon compliance | ENT_COMP_AMAZON | ✅ Existe |
| Listing schema | SCH_LISTING_AMAZON | ✅ Existe |
| A+ Content | SCH_APLUS_CONTENT | ✅ Existe |
| Playbooks | PLB_COPY, PLB_ADS, PLB_GROWTH, PLB_SUPPORT | ✅ Existen |
| Conectores SP-API | [PENDIENTE — absorber legacy 04_integration.md] | PENDIENTE |

**Dependencias:** core/, catalog/, inventory/

---

### M9: ANALYTICS (`analytics/`)

| Aspecto | Detalle |
|---------|---------|
| Función | KPIs, P&L, reportes, dashboards |
| Línea de negocio | Todas |
| Status metodología | ❌ Pendiente N1 |
| Status construcción | ❌ Pendiente |

**Mapeo a Capa de Conocimiento:**

| Dato/Regla | Entity requerido | Status |
|------------|-----------------|--------|
| KPIs automatización, MTTR | [PENDIENTE — absorber legacy Observability_Antifraud] | PENDIENTE |
| Dashboard alertas | ENT_GOB_ALERTAS | ✅ Existe |
| Demand planning dashboard | ENT_OPS_DEMAND_PLANNING | ✅ Existe |

**Dependencias:** Todos los módulos anteriores (consume datos de todos)

---

## FASE 3 — DISTRIBUCIÓN

### M10: DISTRIBUCIÓN (`distribution/`)

| Aspecto | Detalle |
|---------|---------|
| Función | Distribuidores, sub-distribuidores, POS, territorios |
| Línea de negocio | Marluvas (activo), Rana Walk (futuro) |
| Status metodología | ❌ Pendiente N1 |
| Status construcción | ❌ Pendiente |

**Mapeo a Capa de Conocimiento:**

| Dato/Regla | Entity requerido | Status |
|------------|-----------------|--------|
| Distribuidores, territorios | ENT_DIST_DISTRIBUIDORES | [PENDIENTE — por crear] |
| Roles Distributor/SubDistributor | ENT_GOB_ACCESO | ✅ Existe (expandir) |

**Dependencias:** core/, catalog/, pricing/, inventory/

---

### M11: AFILIADOS (`affiliates/`)

| Aspecto | Detalle |
|---------|---------|
| Función | Attribution ledger, códigos, QR, Amazon Attribution |
| Línea de negocio | Rana Walk |
| Status metodología | ❌ Pendiente N1 |
| Status construcción | ❌ Pendiente |

**6 Eventos del Attribution Ledger:**

| Evento | Trigger | Inmutable |
|--------|---------|-----------|
| CLICK | Usuario clic en link/QR | Sí |
| ORDER | Venta atribuida (ventana 14d) | Sí |
| RETURN | Devolución registrada | Sí |
| PAYOUT_CREATED | Cálculo mensual | Sí |
| PAYOUT_APPROVED | CEO aprueba | Sí |
| PAYOUT_PAID | Pago ejecutado | Sí |

**Mapeo a Capa de Conocimiento:**

| Dato/Regla | Entity requerido | Status |
|------------|-----------------|--------|
| Attribution ledger (6 eventos) | ENT_DIST_ATTRIBUTION | [PENDIENTE — por crear] |
| Content governance afiliados | PLB_COMPLIANCE | ✅ Existe (absorber legacy) |
| Anti-fraude | [PENDIENTE — absorber legacy Observability_Antifraud] | PENDIENTE |

**Dependencias:** core/, catalog/, orders/, marketplace/

---

## FASE 4 — PAGOS

### M12: PAGOS (`payments/`)

| Aspecto | Detalle |
|---------|---------|
| Función | Comisiones, payouts, comprobantes |
| Línea de negocio | Rana Walk (afiliados), Marluvas (fábricas) |
| Status metodología | ❌ Pendiente N1 |
| Status construcción | ❌ Pendiente |

**Mapeo a Capa de Conocimiento:**

| Dato/Regla | Entity requerido | Status |
|------------|-----------------|--------|
| Fórmula commission_max | ENT_DIST_COMISIONES | [PENDIENTE — por crear] |
| Tiers (seed/normal/bonus) | ENT_DIST_COMISIONES | [PENDIENTE — por crear] |
| Guardrails (return rate >25% congela payout) | ENT_DIST_COMISIONES | [PENDIENTE — por crear] |
| Reserve devoluciones 15% | ENT_DIST_COMISIONES | [PENDIENTE — por crear] |

**Dependencias:** core/, affiliates/, orders/

---

## ESTADO DE PROGRESO

| # | Módulo | Fase | N1 | N2 | N3 | Architect | Mapeo Capa 1 |
|---|--------|------|----|----|----|-----------|--------------| 
| 1 | expedientes/ | 1 | ✅ 8 | ✅ 6 | ✅ 6 | ❌ | ❌ (7 entities por crear) |
| 2 | pricing/ | 1 | ❌ | ❌ | ❌ | ❌ | 🟡 (3 existen, faltan data contracts) |
| 3 | core/ | 1 | ❌ | ❌ | ❌ | ❌ | 🟡 (2 existen, faltan LegalEntity + 10 roles) |
| 4 | catalog/ | 1 | ❌ | ❌ | ❌ | ❌ | ✅ (RW completo, falta Marluvas/Tecmater) |
| 5 | orders/ | 1 | ❌ | ❌ | ❌ | ❌ | 🟡 (mercados existen, falta state machine) |
| 6 | brands/ | 1 | ❌ | ❌ | ❌ | ❌ | 🟡 (RW completa, falta multi-marca) |
| 7 | inventory/ | 2 | ❌ | ❌ | ❌ | ❌ | ✅ (inventario + demand planning + logística) |
| 8 | marketplace/ | 2 | ❌ | ❌ | ❌ | ❌ | ✅ (schemas + playbooks completos) |
| 9 | analytics/ | 2 | ❌ | ❌ | ❌ | ❌ | 🟡 (alertas existen, faltan KPIs) |
| 10 | distribution/ | 3 | ❌ | ❌ | ❌ | ❌ | ❌ (entities por crear) |
| 11 | affiliates/ | 3 | ❌ | ❌ | ❌ | ❌ | ❌ (entities por crear) |
| 12 | payments/ | 4 | ❌ | ❌ | ❌ | ❌ | ❌ (entities por crear) |

Leyenda: ✅ = entities completos · 🟡 = parciales · ❌ = por crear

---

Stamp: DRAFT — Pendiente aprobación CEO
