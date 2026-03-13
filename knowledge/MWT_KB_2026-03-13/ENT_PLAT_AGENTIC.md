# ENT_PLAT_AGENTIC — Agentic Commerce
status: DRAFT
visibility: [INTERNAL]
domain: Plataforma (IDX_PLATAFORMA)
version: 1.0

---

## A. Contexto mercado

### A1. Protocolos activos (Q1 2026)
- Google UCP (Universal Commerce Protocol): lanzado enero 2026 con Shopify, Walmart, Target, Visa, Mastercard, Stripe, Adyen, 20+ partners.
- OpenAI ACP (Agentic Commerce Protocol): lanzado febrero 2026 con Stripe. "Buy it in ChatGPT" live con Etsy, pronto 1M+ merchants Shopify.
- Anthropic MCP (Model Context Protocol): Claude en Chrome, extensible con MCP servers propios.
- Los tres protocolos son compatibles entre sí.

### A2. Datos de mercado
- McKinsey: comercio agéntico redirigirá $3-5 trillones gasto retail global para 2030.
- ChatGPT procesa ~50M consultas de compras diarias.
- Clientes usando Rufus Amazon: 60% más probabilidad de convertir.
- Regla crítica: si checkout no acepta agente autenticado, agente mueve transacción a otro comerciante. No discute, no reintenta, se va.

## B. Capacidades que agentes IA pueden ejecutar

| Capacidad | Mecanismo | MWT necesita |
|-----------|----------|-------------|
| Descubrir productos | llms.txt, schema markup, product feeds | Implementar en ranawalk.com |
| Consultar disponibilidad/precio/tallas | API pública o MCP server | MCP server propio |
| Iniciar checkout programáticamente | UCP/ACP endpoints | Endpoints en Django DRF |
| Completar compra con pago tokenizado | AP2 (Google), Stripe SPT (OpenAI) | Integración Stripe |

## C. Implementación MWT

### C1. MCP Server propio (Python/Django)
Exponer:
- Catálogo multi-marca (657 SKUs) con atributos, precios vista client, tallas, disponibilidad.
- Capacidad crear órdenes (con límites por rol AI_AGENT).
- Tracking pedidos existentes (portal B2B).
- Registro/descubrimiento por agentes.
Stack: mcp-server-python, autenticación por API key (separado del JWT usuarios humanos).

### C2. UCP endpoints
- /.well-known/ucp con capabilities: checkout, catalog, fulfillment.
- Negotiation: merchant profile + agent profile.
- Payment handlers: Stripe, Adyen, PayPal.

### C3. ACP endpoints (DRF)
4 endpoints core:
- POST /acp/checkout/ — Create Checkout
- GET /acp/checkout/{id}/ — Get Checkout
- PATCH /acp/checkout/{id}/ — Update Checkout
- POST /acp/checkout/{id}/complete/ — Complete Checkout
Stripe Shared Payment Token (SPT) para pagos.
Registro OpenAI para descubrimiento desde ChatGPT.

### C4. Product feed estructurado
- Formato: JSON-LD + OpenAI Product Feed Specification.
- Frecuencia actualización: hasta cada 15 min.
- Generación desde Django para 657 SKUs con inventario real-time.
- Relación con llms.txt: ref → SCH_LLMS_TXT.

### C5. Agentic SEO / ACO
- ACO = Agent Commerce Optimization (vs SEO tradicional).
- Optimización para selección por agentes en reasoning process.
- Schema markup adicional para agentes.
- Monitoreo tráfico agéntico: user-agents ChatGPT-User, Claude-User, Perplexity-User.

## D. Reglas B2B en agentic commerce

MWT no es retailer B2C estándar. Agentes operan dentro de reglas:

### D1. Filtros contextuales que el sistema expone
| Regla | Descripción | Si viola |
|-------|------------|---------|
| Certificaciones por país | CA (Brasil), ANSI (USA), ISO/BS EN (Europa) | Sistema responde con alternativas certificadas para ese destino |
| MOQ | Múltiplos caja master por SKU (12-95) | Sistema sugiere cantidad válida más cercana |
| Condiciones pago por comprador | Cada distribuidor tiene condiciones negociadas | Agente ve SUS condiciones, no genéricas |
| Pricing por modelo | B/C/FULL según transacción | Agente consulta precio que aplica para ese comprador |
| Territorios exclusividad | Distribuidor con territorio exclusivo | Agente no puede generar OC para otro distribuidor en ese territorio |
| Disponibilidad vs fabricación | RW: stock FBA. Marluvas: contra pedido. | Agente ve lead time real, no solo disponible/no disponible |

### D2. Escalación CEO (agent escalation)
Cuando regla de negocio requiere intervención humana (no limitación técnica):
- Monto supera umbral → requiere aprobación CEO antes de ejecutar.
- Producto sin certificación para destino → escalar para evaluación.
- Excepción MOQ → CEO aprueba caja incompleta.
- UCP tiene `requires_escalation` en state machine checkout — adaptar para governance de negocio.

### D3. Rol AI_AGENT
- Catálogo: read-only.
- Inventario: read-only.
- Pricing: vista client solamente.
- Órdenes: crear con límites (monto máximo, SKUs permitidos, MOQ forzado).
- Expedientes: sin acceso.
- Costos: sin acceso.
- Rate limiting y autenticación por API key separada.

## E. Aplicación por frontend

| Frontend | Agentic commerce |
|----------|-----------------|
| ranawalk.com | Full: UCP, ACP, MCP, product feed, llms.txt, ACO |
| portal.mwt.one | MCP server para distribuidores B2B (agente crea OC en nombre de distribuidor) |
| mwt.one | No aplica (interno) |

---

Stamp: DRAFT — Pendiente aprobación CEO
