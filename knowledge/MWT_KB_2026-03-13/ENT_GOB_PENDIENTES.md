# ENT_GOB_PENDIENTES
status: VIGENTE
visibility: INTERNAL
version: 5.0
stamp: VIGENTE — actualizado 2026-03-13
domain: Gobernanza (IDX_GOBERNANZA)
classification: ENTITY — Lista maestra de pendientes operativos por dominio

---

## Sprint 9 — UI Batch (DEFINIDO — pendiente spec LOTE)

**Objetivo:** construir todos los módulos de consola UI que tienen backend ya funcional. Sprint puramente frontend (AG-03). Sin nuevos endpoints POST — solo consumo de APIs existentes salvo excepciones anotadas.

**Bloqueador:** Sprint 8 DONE (MWTUser + JWT — PLT-02 depende de esto).

**Orden de ejecución dentro del sprint:**

| Orden | ID | Módulo | Dependencia interna | Notas |
|-------|----|--------|--------------------|----|
| 1 | PLT-06 | Liquidación Marluvas UI | Ninguna | Backend Sprints 1–5. P0 operacional. |
| 2 | PLT-04 | Nodos Logísticos UI | Ninguna | Backend Sprint 5. Debe ir antes que Transfers. |
| 3 | PLT-05 | Transfers UI | PLT-04 (Nodos) | Backend Sprint 5–6. Depende de Nodos en UI. |
| 4 | PLT-02 | Usuarios UI | Sprint 8 backend | Gestión multi-usuario. Depende de MWTUser. |
| 5 | PLT-03 | Clientes UI | Ninguna | Endpoint GET ya existe. CRUD en UI. |
| 6 | PLT-07 | Brands UI | Ninguna | Backend existe. |

**Excluido de Sprint 9 → Sprint 10:**
- PLT-09 Módulo Productos (depende de Brands + Nodos completados)
- PLT-10 Módulo Inventario (depende de Productos + Nodos)

**Estado:** lista definida — LOTE_SM_SPRINT9.md por crear (post-aprobación Sprint 8).

---

## Módulos ejecutados en Sprint 6 — NO pendientes

Los siguientes módulos estaban en la lista original pero fueron completados en Sprint 6 (DONE 2026-03-12):

| Módulo | Estado | Referencia |
|--------|--------|------------|
| Consola QR (UI + backend) | ✅ DONE Sprint 6 | LOTE_SM_SPRINT6 Item 6 |
| Rana Walk en mwt.one (brand config, expedientes, artefactos, transfers) | ✅ DONE Sprint 6 | LOTE_SM_SPRINT6 Items 1–3 |
| go.ranawalk.com DNS resolution (CNAME + Nginx + SSL) | ✅ DONE Sprint 6 | LOTE_SM_SPRINT6 Item 7 |

---

## Pendientes Plataforma — tabla maestra

| ID | Dominio | Pendiente | Estado | Bloqueador | Sprint |
|----|---------|-----------|--------|-----------|--------|
| PLT-01 | Plataforma | Paperless-ngx webhook bidireccional (Paperless → Django con OCR) | Integración lista, webhook NO activo | Confirmar soporte webhook en versión instalada de Paperless-ngx | Post-Sprint 9 |
| PLT-02 | Plataforma | Usuarios UI — gestión multi-usuario en consola | Pendiente | Sprint 8 MWTUser | Sprint 9 |
| PLT-03 | Plataforma | Clientes UI — CRUD dedicado | Pendiente | Ninguno | Sprint 9 |
| PLT-04 | Plataforma | Nodos Logísticos UI | Pendiente | Ninguno | Sprint 9 |
| PLT-05 | Plataforma | Transfers UI | Pendiente | PLT-04 | Sprint 9 |
| PLT-06 | Plataforma | Liquidación Marluvas UI | Pendiente | Ninguno | Sprint 9 |
| PLT-07 | Plataforma | Brands UI | Pendiente | Ninguno | Sprint 9 |
| PLT-08 | Plataforma | Consola QR UI | ✅ DONE Sprint 6 | — | — |
| PLT-09 | Plataforma | Módulo Productos | Pendiente | PLT-04 + PLT-07 | Sprint 10 |
| PLT-10 | Plataforma | Módulo Inventario | Pendiente | PLT-09 | Sprint 11 |

---

## Detalle técnico apps Django (Sprint 8+)

Origen: fusión desde ENT_PLAT_MODULOS_PENDIENTES v1.1 (DEPRECATED v5.0)

### Apps Django — estado real verificado con Alejandro

| App | Backend | Frontend consola | Notas |
|-----|---------|-----------------|-------|
| `expedientes` | ✅ 39 endpoints | ✅ Sprint 7 completo | Operativo |
| `brands` | ✅ Existe (fixtures + generate_brands_fixtures.py) | ❌ Sin UI | Backend confirmado. Leer models.py antes de implementar UI |
| `transfers` | ✅ Existe app (C30–C35) | ❌ Sin UI | Backend completo |
| `liquidations` | ✅ Existe app (C25–C28) | ❌ Sin UI | Backend completo |
| `qr` | ✅ Existe app + resolver | ✅ DONE Sprint 6 | Operativo |
| `core` | ✅ Base | — | |
| `integrations` | ✅ Existe | — | |

### Apps Django AUSENTES — deben crearse

| App | Sprint | Bloqueador |
|-----|--------|-----------|
| `users` (MWTUser extendido) | 8 | **En construcción** — LOTE_SM_SPRINT8 Pilar A |
| `permission_groups` | 8 | **En construcción** — LOTE_SM_SPRINT8 Pilar A |
| `knowledge` | 8 | **En construcción** — LOTE_SM_SPRINT8 Pilar B |
| `clients` (app dedicada) | 9 | Endpoint GET ya existe en expedientes |
| `nodes` (LogisticNode) | 9 | Referenciado en transfers, sin app dedicada |
| `products` | 10 | Prerequisito: Brands UI + Nodes |
| `inventory` | 11 | Prerequisito: Products + Nodes |

### Convenciones para Sprint 9+

- Backend: DRF · ModelViewSet o APIView · JWT auth
- Frontend: Next.js 14 App Router · `[lang]/(mwt)/(dashboard)/{modulo}/`
- Formularios: Drawer lateral (CRUD) · Página nueva (formularios complejos)
- Todos los modelos: UUID pk · is_active · created_at · updated_at · deleted_at (soft delete)
- RBAC: CEO = superuser en MVP · guards reales post-Sprint 8

---

## Inteligencia de modelos — Lab Multi-LLM

Sección alimentada por resultados del protocolo PLB_INTEL_ITERACION_MANUAL.

[PENDIENTE — primeros experimentos por registrar]

Cuando haya masa crítica de datos (10+ experimentos por categoría), esta sección se gradúa a entity propia ENT_GOB_INTEL_MODELOS.

---

**Aclaración S6-10:** Dashboard P&L no es pendiente. Es la vista financiera S4-05 ya existente.

Origen: AUDITORIA_SPRINTS_20260312.md + respuestas directas Alejandro 2026-03-12
Actualizado: 2026-03-13 — Sprint 9 definido, fusión MODULOS_PENDIENTES, sección Inteligencia de modelos

Changelog:
- v3.x: versiones anteriores sin campo version: declarado
- v4.0: campo version: agregado para cumplir estándar de entities (Obs.2 diagnóstico 2026-03-13)
- v5.0: fusión de ENT_PLAT_MODULOS_PENDIENTES (DEPRECATED). Agregado detalle técnico apps Django, convenciones Sprint 9+, sección Inteligencia de modelos.
