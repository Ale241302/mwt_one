# ENT_PLAT_FRONTENDS — Frontends y Roles
status: DRAFT
visibility: [INTERNAL]
domain: Plataforma (IDX_PLATAFORMA)
version: 2.0

---

## A. Tres webs — Dos conectadas, una estática

| Web | URL | Tipo | Público | Función | Conectada a plataforma |
|-----|-----|------|---------|---------|----------------------|
| Plataforma | mwt.one | SPA (Next.js) | Todos los usuarios con cuenta | Centro de Operaciones, RBAC filtra vista por rol | ✅ Sí — Django API |
| Marca pública | ranawalk.com | SSR (Next.js) | Público + agentes IA | Catálogo, SEO, agentic commerce | ✅ Sí — API read-only |
| Corporativa | muitowork.com | Estático | Público | Brochure corporativo. Quiénes somos, líneas de negocio, contacto | ❌ No — sin backend |

Decisión congelada: NO hay portal.mwt.one. Todo converge en mwt.one. Distribuidores, clientes B2B y CEO acceden al mismo frontend — RBAC filtra qué ve cada quien según LegalEntity y rol. Ref → ENT_PLAT_LEGAL_ENTITY.D-E.

## B. mwt.one — Plataforma única

### B1. Secciones

**MVP (Sprint 1-3):**
- Centro de Operaciones: timeline expedientes 8 estados, artefactos, flujos por marca, alertas.
- Costos: registro costos por expediente (vista única en Sprint 3, doble vista Sprint 4).
- Documentos: upload, tags, búsqueda, link a MinIO.
- Alertas: reloj crédito 90 días, semáforo tiempos.
- Dashboard resumen: top expedientes por riesgo (tiempo + crédito + costo).
- Acciones contextuales: Pipeline (transiciones por estado) + Ops (block, cost, supersede, void).

**Post-MVP:**
- Contabilidad: rendimiento por modelo B/C, P&L por marca/cliente/expediente.
- Pricing: tablas por marca, fórmulas, simulador B vs C.
- Catálogo: 657+ SKUs multi-marca, atributos, MOQ, grades.
- Amazon Advertising: campañas, ACoS, keywords, budget — vista general + por producto.
- Marketplace: listings, performance ASIN, inventario FBA.
- Distribución: distribuidores, sub-distribuidores, territorios, comisiones.
- Forecast: demanda, tiempos, rutas, punto óptimo aéreo/marítimo.
- Configuración: roles, permisos, marcas, mercados, políticas.

### B2. Métricas clave
- Expedientes activos con semáforo tiempos (Mint/Ámbar/Coral basado en credit_band).
- Costos acumulados vs margen proyectado por expediente.
- Rentabilidad en vivo por expediente, cliente, marca, modo B vs C.
- Cash flow: facturas por cobrar, pagos por salir, reloj crédito 90 días, prepaid/postpaid.
- Comparativa retroactiva: "¿qué hubiera pasado si hubiera elegido otro modelo?"

### B3. Alertas
- Expediente desviado de tiempos históricos.
- Costo supera proyección.
- Cliente debería reordenar según patrón.
- Barco/avión saturado en ruta frecuente.

### B4. Design System
Ref → ENT_PLAT_DESIGN_TOKENS (v1, aprobado Sprint 3)
Ref → ENT_COMP_VISUAL (v2, compliance visual)
Artefacto de referencia: mwt_design_system_v1.html

Paleta: Navy #013A57 + Mint #75CBB3 — identidad Rana Walk aplicada a toda la plataforma.
Tipografía: General Sans (display) + Plus Jakarta Sans (body) + JetBrains Mono (códigos).
Temas: Light (default Sprint 3). Dark mode definido en tokens, implementación Sprint 4+.
Componentes auditados: 9 (botones, badges, tabla, cards, timeline, sidebar, toasts, modal, inputs).
Semáforo crédito: Mint <60d, Ámbar 60-74d, Coral ≥75d. Backend calcula credit_band, frontend solo pinta.

### B5. Auth y acceso (Sprint 3)
Auth: Django session cookie + CSRF. Ref → LOTE_SM_SPRINT3 S3-D01.
Sprint 3: un solo usuario (CEO). Post-MVP: RBAC con roles según ENT_PLAT_LEGAL_ENTITY.

## C. ranawalk.com — Sitio público

- Marca Rana Walk: identidad, productos, tecnologías.
- Catálogo público: 5 modelos, especificaciones, tallas.
- SEO: contenido optimizado, schema markup, llms.txt (ref → SCH_LLMS_TXT).
- Agentic commerce: endpoints UCP/ACP, MCP server, product feed (ref → ENT_PLAT_AGENTIC).
- Sin login. Sin área privada. Distribuidores RW acceden a mwt.one, no a ranawalk.com.

## D. muitowork.com — Corporativa estática

- Brochure: quiénes somos, 3 líneas de negocio (Rana Walk, Marluvas, Tecmater), contacto.
- No conecta con la plataforma. No tiene backend. No tiene login.
- Puede ser HTML estático, WordPress, o cualquier cosa simple.

## E. Usuarios y roles por web

### E1. mwt.one — Todos los usuarios con cuenta

| Rol | LegalEntity | Qué ve | Qué puede hacer | MVP |
|-----|------------|--------|-----------------|-----|
| CEO | Muito/MWT | Todo (full visibility) | Todo (crear, aprobar, configurar, CRUD) | ✅ Sprint 3 |
| Admin | Muito/MWT | Todo excepto [CEO-ONLY] | CRUD catálogo, órdenes, expedientes | ❌ Post-MVP |
| OpsManager | Muito/MWT | Inventario, pedidos, expedientes | Gestión operativa sin aprobación final | ❌ Post-MVP |
| Cliente B2B | Sondel, otros | Solo sus expedientes (simplificado) | Solo lectura + tracking | ❌ Post-MVP |
| Distribuidor RW | Distribuidor CR/BR | Su inventario, órdenes, territorio, comisiones | Gestión de su perímetro | ❌ Post-MVP |
| Sub-distribuidor | Sub-dist | Su stock local, órdenes, sucursales | Gestión limitada | ❌ Post-MVP |
| AI_AGENT | Service token | Catálogo read-only, vista client | Operaciones con límites | ❌ Post-MVP |

MVP Sprint 3: solo CEO. Un rol, una sesión, auth ultra simple.

### E2. ranawalk.com — Sin login

| Visitante | Qué ve | Qué puede hacer |
|-----------|--------|-----------------|
| Público | Catálogo, productos, especificaciones | Navegar, buscar, ver precios públicos |
| Agente IA | Endpoints UCP/ACP, product feed | Consultar catálogo via API/MCP |

### E3. muitowork.com — Sin login

| Visitante | Qué ve |
|-----------|--------|
| Público | Brochure corporativo |

## F. Visualización expedientes (NO Kanban)

Vista de líneas de tiempo secuenciales. Cada expediente = línea horizontal con nodos por estado canónico (ref → ENT_OPS_STATE_MACHINE §B para los 8 estados).

Indicadores por nodo:
- Completado: Mint filled circle + ✓ (16px)
- Actual: Navy circle + pulse animation + box-shadow (20px)
- Futuro: hollow dashed circle (16px)
- Bloqueado: flag paralelo, no estado propio

Líneas: solid Mint (completadas), gradient (actual), dashed (futuras).

Cada línea largo diferente (cada flujo tiene artefactos diferentes). Filtrable por marca, cliente, modo, estado. Semáforos de tiempo vs histórico (credit_band). Alertas información faltante. Barra progreso. Agrupación por estado similar.

Implementación visual: ref → ENT_PLAT_DESIGN_TOKENS.E5 (Timeline component).
Implementación técnica: ref → LOTE_SM_SPRINT3 Item 5.

## G. Arquitectura técnica

```
                    ┌─────────────────┐
                    │   muitowork.com  │ (estático, sin backend)
                    └─────────────────┘
                    
┌──────────────┐    ┌─────────────────┐
│ ranawalk.com │◄──►│  Django API     │◄──► PostgreSQL
│ (Next.js SSR)│    │  (backend)      │◄──► Redis/Celery
└──────────────┘    └────────▲────────┘◄──► MinIO
                             │
                    ┌────────┴────────┐
                    │    mwt.one      │
                    │  (Next.js SPA)  │
                    │  nginx reverse  │
                    │  proxy: / → FE  │
                    │  /api/ → Django │
                    └─────────────────┘
```

Una sola API Django. Dos frontends Next.js la consumen. Un brochure estático aparte.

---

Stamp: DRAFT — Pendiente aprobación CEO
Origen: ENT_PLAT_FRONTENDS v1.1
Actualizado: 2026-02-27 — Eliminado portal.mwt.one (todo converge en mwt.one), agregado muitowork.com como estático, estructura corporativa alineada con ENT_PLAT_LEGAL_ENTITY v2, roles y MVP alineados con LOTE_SM_SPRINT3
