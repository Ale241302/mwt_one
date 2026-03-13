# ENT_PLAT_FRONTENDS — Frontends y Roles
status: DRAFT
visibility: [INTERNAL]
domain: Plataforma (IDX_PLATAFORMA)
version: 1.0

---

## A. Tres instancias Next.js

| Frontend | URL | Tipo | Público | Función |
|----------|-----|------|---------|---------|
| Interno | mwt.one | SPA | CEO / equipo | Centro de Operaciones completo |
| Público | ranawalk.com | SSR | Público + agentes IA | Marca pública, catálogo, SEO, agentic commerce |
| Portal B2B | portal.mwt.one | SPA | Clientes + distribuidores | Expedientes, tracking, docs, órdenes, comisiones |

## B. mwt.one — Dashboard CEO

### B1. Secciones
- Centro de Operaciones: timeline expedientes, artefactos, flujos por marca, alertas.
- Contabilidad: rendimiento por modelo B/C, P&L por marca/cliente/expediente.
- Pricing: tablas por marca, fórmulas, simulador B vs C.
- Catálogo: 657+ SKUs multi-marca, atributos, MOQ, grades.
- Amazon Advertising: campañas, ACoS, keywords, budget — vista general + por producto.
- Marketplace: listings, performance ASIN, inventario FBA.
- Distribución: distribuidores, sub-distribuidores, territorios, comisiones.
- Forecast: demanda, tiempos, rutas, punto óptimo aéreo/marítimo.
- Configuración: roles, permisos, marcas, mercados, políticas.

### B2. Métricas clave
- Expedientes activos con semáforo tiempos (verde/amarillo/rojo basado en histórico).
- Costos acumulados vs margen proyectado por expediente.
- Rentabilidad en vivo por expediente, cliente, marca, modo B vs C.
- Cash flow: facturas por cobrar, pagos por salir, reloj crédito 90 días, prepaid/postpaid.
- Comparativa retroactiva: "¿qué hubiera pasado si hubiera elegido otro modelo?"

### B3. Alertas
- Expediente desviado de tiempos históricos.
- Costo supera proyección.
- Cliente debería reordenar según patrón.
- Barco/avión saturado en ruta frecuente.

## C. ranawalk.com — Sitio público

- Marca Rana Walk: identidad, productos, tecnologías.
- Catálogo público: 5 modelos, especificaciones, tallas.
- SEO: contenido optimizado, schema markup, llms.txt (ref → SCH_LLMS_TXT).
- Agentic commerce: endpoints UCP/ACP, MCP server, product feed (ref → ENT_PLAT_AGENTIC).

## D. portal.mwt.one — Portal B2B

Mismo frontend con permisos y vistas diferentes según rol.

### D1. Vista Cliente B2B (ej: Sondel)
- Mis pedidos: estado simple (Confirmado → En fabricación → En tránsito → En aduana → Listo).
- Tracking: carrier, número, itinerario, fecha estimada, link directo.
- Documentos: solo suyos, solo vista client (proforma, factura, BL/AWB).
- Historial: pedidos anteriores, patrones para reorden.
- Notificaciones: cambio estado, fecha actualizada, documento disponible.
- Valor: cliente deja de enviar correos preguntando estado.

### D2. Vista Distribuidor Rana Walk
- Catálogo RW asignado, órdenes, inventario asignado, comisiones.

### D3. Vista Sub-distribuidor
- Solo su porción del territorio y comisiones.

## E. Matriz de permisos

| Rol | Expedientes | Costos | Tracking | Documentos | Órdenes | Comisiones |
|-----|------------|--------|----------|------------|---------|------------|
| CEO | Todos | Internal + client | Todos | Todos | Sí | Todas |
| Cliente B2B | Solo suyos | Solo client | Solo suyos | Solo suyos | Sí (OC) | No |
| Distribuidor RW | Solo suyos | Solo client | Solo suyos | Solo suyos | Sí | Las suyas |
| Sub-distribuidor | Solo suyos | Solo client | Solo suyos | Solo suyos | Sí (limitado) | Las suyas |
| AI_AGENT | Catálogo read-only | Vista client | Solo del buyer | No | Sí (con límites) | No |

## F. Visualización expedientes (NO Kanban)

Vista de líneas de tiempo secuenciales. Cada expediente = línea horizontal con nodos (artefactos):
- ✅ completado
- 🔵 activo
- ⚪ pendiente
- 🔴 bloqueado/alerta

Cada línea largo diferente (cada flujo tiene artefactos diferentes). Filtrable por marca, cliente, modo, estado. Semáforos de tiempo vs histórico. Alertas información faltante. Barra progreso. Agrupación por estado similar.

---

Stamp: DRAFT — Pendiente aprobación CEO
