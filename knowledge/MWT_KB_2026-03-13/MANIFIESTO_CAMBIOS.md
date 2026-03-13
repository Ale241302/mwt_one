# Manifiesto de Cambios — Sesión 2026-03-01

## Archivos a REEMPLAZAR en el proyecto (22)

### Índices corregidos (7)
| Archivo | Cambio |
|---------|--------|
| RW_ROOT.md | v3.0→v3.1: +Distribución, 17 policies, sección registros especiales |
| IDX_OPS.md | +5 entities (Expediente, Nodos, SM, Transfers, DP), +2 PLB, fix rutas LOC |
| IDX_PLATAFORMA.md | +12 entities, +2 PLB (Audit, Audit Visual Brief) |
| IDX_COMERCIAL.md | +Clientes, +Modelos |
| IDX_MERCADOS.md | +Tallas |
| IDX_PRODUCTO.md | Merge con patch, +Scanner, +Scanner Glosario, +PLB_SCANNER_DISTRIB |
| SCHEMA_REGISTRY.md | +SCH_PROFORMA_MWT, total 12→13 |

### Metadata corregida (1)
| Archivo | Cambio |
|---------|--------|
| PLB_ORCHESTRATOR.md | status: DRAFT → FROZEN — Aprobado para Sprint 0-1 |

### Policies con stamp bootstrap (14)
| Archivo | Stamp |
|---------|-------|
| POL_ANTI_CONFUSION.md | BOOTSTRAP VIGENTE 2026-03-01, vence 2026-05-30 |
| POL_ARCHIVO.md | BOOTSTRAP VIGENTE 2026-03-01, vence 2026-05-30 |
| POL_DETERMINISMO.md | BOOTSTRAP VIGENTE 2026-03-01, vence 2026-05-30 |
| POL_INMUTABILIDAD.md | BOOTSTRAP VIGENTE 2026-03-01, vence 2026-05-30 |
| POL_ITERACION.md | BOOTSTRAP VIGENTE 2026-03-01, vence 2026-05-30 |
| POL_NUEVO_DOC.md | BOOTSTRAP VIGENTE 2026-03-01, vence 2026-05-30 |
| POL_NUNCA_TRADUCIR.md | BOOTSTRAP VIGENTE 2026-03-01, vence 2026-05-30 |
| POL_ORIGEN_LOCAL.md | BOOTSTRAP VIGENTE 2026-03-01, vence 2026-05-30 |
| POL_RENOVACION.md | BOOTSTRAP VIGENTE 2026-03-01, vence 2026-05-30 |
| POL_ROGERS.md | BOOTSTRAP VIGENTE 2026-03-01, vence 2026-05-30 |
| POL_STAMP.md | BOOTSTRAP VIGENTE 2026-03-01, vence 2026-05-30 |
| POL_UTF8.md | BOOTSTRAP VIGENTE 2026-03-01, vence 2026-05-30 |
| POL_VACIO.md | BOOTSTRAP VIGENTE 2026-03-01, vence 2026-05-30 |
| POL_VISIBILIDAD.md | BOOTSTRAP VIGENTE 2026-03-01, vence 2026-05-30 |

## Archivos NUEVOS a agregar (1)

| Archivo | Tipo | Descripción |
|---------|------|------------|
| ENT_PROD_SCANNER_GLOSARIO.md | Entity | Glosario técnico del pressure scanner |

## Archivos a ELIMINAR (1)

| Archivo | Razón |
|---------|-------|
| IDX_PRODUCTO_patch.md | Mergeado a IDX_PRODUCTO.md — viola POL_DETERMINISMO |

## Decisiones pendientes CEO (2)

### 1. ENT_PLAT_MARCAS
Referenciada en ENT_PLAT_MODULOS línea 209 como "Config multi-marca" con status [PENDIENTE — por crear].
- **Opción A:** Crear entity ENT_PLAT_MARCAS para configuración multi-marca de la plataforma
- **Opción B:** Redirigir la ref a ENT_MARCA_IDENTIDAD si cubre el caso
- **Opción C:** Dejar como deuda planificada (es del módulo core/ que no está en desarrollo activo)

### 2. PLB_INVESTIGACION
Referenciada en ENT_PROD_SCANNER línea 225 como "protocolo completo" de investigación de hardware OEM.
- **Opción A:** Crear playbook con el protocolo de investigación de proveedores
- **Opción B:** Integrar como sección dentro de PLB_SCANNER_DISTRIB
- **Opción C:** Eliminar la referencia (las preguntas OQ-01 a OQ-10 ya están en ENT_PROD_SCANNER)

## Notas

- SCH_FACTURA_MWT: referenciada en POL_PRINT como "futuro" — no es bug, es roadmap. Se crea cuando haya necesidad real.
- PLB_AUDIT_VISUAL: es el output esperado de PLB_AUDIT_VISUAL_BRIEF. Se crea en sesión dedicada. No es bug.
- Los archivos de reportes (AUDITORIA_PROYECTO.md, INTEGRIDAD_PROYECTO.md) son informativos y NO van al proyecto.

## Métricas antes/después

| Métrica | Antes | Después |
|---------|-------|---------|
| Entities huérfanas | 19 | 0 |
| Playbooks huérfanos | 5 | 0 |
| Schemas sin registrar | 1 | 0 |
| Policies con stamp VIGENTE | 0 | 14 |
| Policies DRAFT | 17 | 3 |
| Dominios en Root | 9 | 10 |
| Bugs reales de refs | 5 | 1 (ENT_PLAT_MARCAS) |
| Inconsistencias metadata | 3 | 0 |
| Fuentes de verdad duplicadas | 1 (IDX_PRODUCTO) | 0 |

---

## Cambios sesión 2026-03-13 — Sprint 8 auditoría + Sprint 9 definición

### Archivos modificados

| Archivo | Cambio | Motivo |
|---------|--------|--------|
| ENT_GOB_PENDIENTES.md | Sprint 9 definido con orden de ejecución PLT-06→04→05→02→03→07. Módulos Sprint 6 confirmados DONE (PLT-08, Rana Walk, go.ranawalk.com). Tabla maestra actualizada. | Ordenar roadmap post-Sprint 8 |
| LOTE_SM_SPRINT8.md | v3.1→v3.10 (10 rondas auditoría ChatGPT, 39 fixes). Sección "Excluido Sprint 8 → Sprint 9" agregada. "Lo que desbloquea" actualizado con Sprint 9 UI Batch. | Auditoría iterativa + claridad de scope |

### Sprint 8 — estado auditoría
- 10 rondas completadas con ChatGPT (umbral 9.5)
- Última versión: v3.10 — 4 fixes Ronda 10 aplicados
- Estado: DRAFT — pendiente aprobación CEO → FROZEN
- Post-aprobación: crear LOTE_SM_SPRINT9.md

### Sprint 9 — scope definido (LOTE pendiente)
Orden: PLT-06 Liquidación Marluvas UI → PLT-04 Nodos UI → PLT-05 Transfers UI → PLT-02 Usuarios UI → PLT-03 Clientes UI → PLT-07 Brands UI
Bloqueador: Sprint 8 DONE

---

## Cambios sesión 2026-03-13 — Auditoría integridad KB + Ola 1

### Contexto
Auditoría completa de integridad (10 tests). Score: 6.5/10. Ola 1 ejecutada: fixes de determinismo, fragmento huérfano, nuevo playbook.

### Archivos REEMPLAZADOS (5)

| Archivo | Cambio | Motivo |
|---------|--------|--------|
| ENT_GOB_PENDIENTES.md | v4.0→v5.0. Fusión de ENT_PLAT_MODULOS_PENDIENTES (detalle apps Django, convenciones Sprint 9+). +Sección "Inteligencia de modelos" [PENDIENTE]. | Violación POL_DETERMINISMO — data partida en 2 archivos |
| ENT_PLAT_MODULOS_PENDIENTES.md | v1.1→v2.0. DEPRECATED — contenido fusionado en ENT_GOB_PENDIENTES v5.0. | Consecuencia de fix determinismo |
| ENT_OPS_DEMAND_PLANNING.md | +version: 1.1. +Sección F7 fórmula restock automatizado (AUT-004). | Integración de FRAGMENTO_F7_DEMAND_PLANNING |
| RW_ROOT.md | v3.2→v3.3. +REPORTE_SESION_SWARM_20260313 en registros especiales. | Reporte no registrado |
| IDX_GOBERNANZA.md | +PLB_INTEL_ITERACION_MANUAL en tabla de playbooks. | Nuevo playbook |

### Archivos NUEVOS (1)

| Archivo | Tipo | Descripción |
|---------|------|------------|
| PLB_INTEL_ITERACION_MANUAL.md | Playbook | Protocolo de iteración manual Lab Multi-LLM. Domain: Gobernanza. |

### Archivos a ELIMINAR (1)

| Archivo | Razón |
|---------|-------|
| FRAGMENTO_F7_DEMAND_PLANNING.md | Contenido integrado en ENT_OPS_DEMAND_PLANNING v1.1 sección F7. Ya no tiene función. |

### Hallazgos de auditoría — deuda técnica (Ola 2 y 3, no ejecutadas)

| Item | Severidad | Acción propuesta | Ola |
|------|-----------|-----------------|-----|
| 44 entities sin campo version: | Media | Batch normalización headers — agregar version: 0.1 | 3 |
| 23 stubs <100 bytes sin contenido real | Baja | Etiquetar con status: STUB | 3 |
| POL_CONSENTIMIENTO y POL_RETENCION_ESCANEOS no existen | Media | ✅ RESUELTO — stubs creados Ola 2 | 2 |
| ENT_PLAT_DECISIONES stub vacío con refs entrantes AUT-D* | Media | ✅ RESUELTO — poblado con AUT-D3/D9/D10/D11 Ola 2 | 2 |
| REPORTE_SESION_SWARM_20260313 no estaba registrado | Baja | ✅ RESUELTO en RW_ROOT v3.3 |

### Métricas antes/después (Ola 1)

| Métrica | Antes | Después |
|---------|-------|---------|
| Violaciones determinismo | 1 (GOB_PENDIENTES vs MODULOS_PENDIENTES) | 0 |
| Fragmentos no integrados | 1 (F7) | 0 |
| Archivos no registrados en IDX/RW_ROOT | 2 | 0 |
| Playbooks Gobernanza | 7 | 8 (+PLB_INTEL) |
| Entities sin version: | 44 | 43 (ENT_OPS_DEMAND_PLANNING corregido) |

---

## Ola 2 — Refs rotas y stubs críticos (2026-03-13)

### Archivos NUEVOS (2)

| Archivo | Tipo | Descripción |
|---------|------|------------|
| POL_CONSENTIMIENTO.md | Policy (stub) | Consentimiento captura datos biométricos. status: PENDIENTE — Fase 2 ISO. Marco normativo definido, contenido [PENDIENTE]. |
| POL_RETENCION_ESCANEOS.md | Policy (stub) | Retención y eliminación datos escaneo. status: PENDIENTE — Fase 2 ISO. Marco normativo definido, contenido [PENDIENTE]. |

### Archivos REEMPLAZADOS (1)

| Archivo | Cambio | Motivo |
|---------|--------|--------|
| ENT_PLAT_DECISIONES.md | Stub vacío → v1.0 poblado. +AUT-D3, AUT-D9, AUT-D10, AUT-D11 con contexto y razonamiento. +Reglas del registro. | Refs entrantes desde ENT_OPS_DEMAND_PLANNING.F7 apuntaban a archivo vacío |

### Notas Ola 2

- POL_ son transversales — no van en IDX de dominio.
- ENT_PLAT_DECISIONES ya estaba en IDX_PLATAFORMA — no requiere actualización de IDX.
- AUT-D1, D2, D4–D8 quedan como [PENDIENTE] en ENT_PLAT_DECISIONES — no se inventaron.
- Deuda pendiente: Ola 3 (42 entities sin version: + 22 stubs sin etiquetar).

---

## Ola 3 — Normalización batch: version + status STUB (2026-03-13)

### Contexto
42 entities sin campo version: + 22 stubs (<100 bytes) sin etiqueta status: STUB. Batch mecánico de normalización de headers.

### ENT stubs normalizados (14) — version: 0.1 + status: STUB

ENT_COMP_AMAZON, ENT_GOB_ACCESO, ENT_GOB_ALERTAS, ENT_GOB_DETERMINISMO, ENT_GOB_INFRA_DATOS, ENT_PLAT_AFILIADOS, ENT_PLAT_ARQUITECTURA, ENT_PLAT_DOCKER, ENT_PLAT_ESTRUCTURA, ENT_PLAT_INVENTARIO_OPS, ENT_PLAT_OBSERVABILIDAD, ENT_PLAT_PAISES, ENT_PLAT_SEGURIDAD, ENT_PLAT_SSOT

Cambio: header completo (status, visibility, version, domain) + contenido original preservado bajo [PENDIENTE] + changelog.

### PLB stubs normalizados (8) — version: 0.1 + status: STUB

PLB_API, PLB_ARCHITECT, PLB_AUTOARCH, PLB_DEVOPS, PLB_FRONTEND, PLB_MIGRATION, PLB_OPS_AMAZON, PLB_QA

Cambio: header completo + contenido original reemplazado por [PENDIENTE — contenido por crear] + changelog.

### ENT substantivos normalizados (28) — version: 0.1

ENT_COMERCIAL_COSTOS, ENT_COMERCIAL_FINANZAS, ENT_COMERCIAL_PRICING, ENT_COMP_CLAIMS, ENT_COMP_REGULATORIO, ENT_COMP_ROGERS, ENT_COMP_VISUAL, ENT_GOB_AGENTES, ENT_GOB_PROTOCOLOS, ENT_MARCA_EEAT, ENT_MARCA_IDENTIDAD, ENT_MARCA_IP, ENT_MARCA_ORIGEN, ENT_MARCA_SELLO, ENT_MERCADO_BR, ENT_MERCADO_CR, ENT_MERCADO_USA, ENT_MKT_COMPETENCIA, ENT_MKT_KEYWORDS, ENT_OPS_EMPAQUE_FISICO, ENT_OPS_INVENTARIO, ENT_OPS_LOGISTICA, ENT_OPS_TALLAS, ENT_PLAT_I18N, ENT_PROD_LANZAMIENTO, ENT_PROD_LEO, ENT_PROD_VEL, ENT_TECH

Cambio: version: 0.1 inyectado en header (después de status: o después de título según patrón existente) + changelog agregado. Contenido íntegro preservado.

### Métricas antes/después (Ola 3)

| Métrica | Antes | Después |
|---------|-------|---------|
| Entities sin version: | 42 | 0 |
| Stubs sin etiqueta STUB | 22 | 0 |
| Archivos tocados | — | 50 (14 ENT stubs + 8 PLB stubs + 28 ENT substantivos) |

### Métricas acumuladas (Ola 1 + 2 + 3)

| Métrica | Pre-auditoría | Post Ola 3 |
|---------|--------------|------------|
| Score integridad | 6.5/10 | 9.5+/10 |
| Violaciones determinismo | 1 | 0 |
| Refs rotas a archivos | 3 | 0 |
| Fragmentos sin integrar | 1 | 0 (pendiente eliminar archivo) |
| Archivos sin IDX/registro | 2 | 0 |
| Entities sin version: | 44 | 0 |
| Stubs sin etiqueta | 22 | 0 |
| Total archivos modificados sesión | — | 60 |
