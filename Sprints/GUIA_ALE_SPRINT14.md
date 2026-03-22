# GUÍA ALEJANDRO — Sprint 14: Agreements Layer + Client Self-Service
## Para: Alejandro (AG-02 Backend + AG-03 Frontend) · Fecha: 2026-03-20

---

## Qué es este sprint

El más grande hasta ahora. Transforma la plataforma de "hardcoded para Marluvas" a "parametrizada por marca" y agrega la posibilidad de que el cliente cree su propia orden desde el portal. 23 items, 2 fases. Fase 0 es obligatoria (models + backend). Fase 1 es opcional (UI + self-service).

En resumen: después de este sprint, agregar Tecmater o una marca nueva es configuración, no código. Y Sondel puede hacer su pedido sin mandarte un email.

---

## Contexto (para que entiendas el "por qué")

Hoy cada orden llega por email. Vos cruzás precios manualmente contra la Tabela COMEX, evaluás si B o C, generás la proforma. Eso funciona con 12 expedientes. No funciona con 50.

Lo que construimos:

1. **Agreements Layer** — Toda la configuración comercial (quién puede comprar qué, a qué precio, con qué plazo) vive en tablas versionadas. Cambiar un precio = crear nueva versión, nunca editar la anterior.

2. **Pricing Engine** — El sistema resuelve el precio por cascada: override subsidiaria > override grupo > pricelist base. La fórmula de Marluvas `Precio_Base × (1.0183^(100 × Comisión)) × Índice_Pago` se ejecuta en backend. El frontend nunca calcula.

3. **Snapshots** — Al crear un expediente, se congela TODA la configuración vigente en ese momento. Si mañana cambia la pricelist, los expedientes viejos no se ven afectados.

4. **Client Self-Service** — Sondel entra a portal.mwt.one, ve su catálogo con precios ya calculados, arma su orden, elige plazo de pago (que afecta el precio), y la manda. Vos la recibís ya con todo calculado para revisar.

---

## Prerequisito

Sprint 13 Fase 0 DONE. Sprint 11-12 refactors estables. services/ directory existe.

---

## FASE 0 — Lo que hay que hacer sí o sí (estimado 4-5 días)

### 1. Master Data models (S14-01)

Nuevos modelos Django:

- **BrandConfigVersion** — configuración operativa de marca, versionada. Campos: brand (FK), version (semver), default_currency, default_mode, allowed_operation_modes (jsonb), dispatch_modes (jsonb), has_sap, has_production, max_order_revisions (int default 3), valid_from, valid_to, status.
- **CatalogVersion** — versión del catálogo, FK a Brand.
- **ProductMaster ampliado** — agregarle: hs_code, weight_kg, cbm, moq, country_eligibility (jsonb), channel_eligibility (jsonb), uom, country_of_origin, lead_time_days.
- **ProductVariant** — variant_sku, attributes (jsonb), barcode, FK a ProductMaster.
- **ClientUltimateParent, ClientGroup** — refactor del Client actual.
- **ClientSubsidiary** — FK a ClientGroup, alias (3-8 chars), country, FK a LegalEntity. El expediente siempre apunta acá.
- **ClientBrandExternalCode** — código SAP por subsidiaria × marca.

### 2. Agreements models (S14-02)

- **BrandClientAgreement** — versionado, CommercialFilter embebido (mode, channel, currency, incoterm). Scope: party_type (group|subsidiary) + party_id. **Exclusion constraint**: máximo 1 activo por (brand_id, party_type, party_id, daterange). max_order_revisions override (nullable).
- **BrandClientPriceAgreement** — override de precio por SKU.
- **BrandSupplierAgreement** — contrato con proveedor.
- **AssortmentPolicy** — include_rules / exclude_rules (jsonb).
- **CreditPolicy + CreditExposure** — 3 niveles scope.
- **PaymentTermPricingVersion** — cabecera versionada (brand_id, scope_type: agreement|brand_default, agreement_id nullable, version, valid_from/to, status). Resolución: agreement > brand_default.
- **PaymentTermPricingTerm** — tabla hija: pricing_version_id, payment_days, price_index, label. UNIQUE (pricing_version_id, payment_days).

### 3. Workflow Policy (S14-03)

BrandWorkflowPolicy + StatePolicy + CommandPolicy + ArtifactRequirement + TransitionPolicy. Seed para Marluvas y Tecmater. Validador.

### 4. Pricing Engine (S14-04)

Pricelist + PricelistItem + PricingRuleSet + PricingRule + PricePrecedencePolicy.

Función clave: `resolve_client_price(context, sku, commission_pct, payment_days)` que retorna precio final + source traceability. Override modes: none, base_override, final_override_manual.

### 5. Snapshots (S14-05)

ExpedienteContextSnapshot — inmutable, refs a todas las versiones activas. ArtifactCommercialLineSnapshot — precio + comisión + override_mode por línea.

### 6. Audit trail (S14-06)

ConfigChangeLog con signals.

### 7. Refactors (S14-07, S14-08)

can_transition_to() lee de BrandWorkflowPolicy. C2 valida contra ProductMaster + AssortmentPolicy.

### 8. Seed data (S14-09)

565 SKUs desde JSON nomenclatura. Pricelist COMEX. Workflow policies. PaymentTermPricingVersion para MLV default + Sondel.

---

## FASE 1 — Si hay tiempo (estimado 5-6 días)

### UI (S14-10, S14-11)
Brand Console con 4 tabs. Client Console con 7 tabs (incluye Pricing por plazo como viewer de versiones y Órdenes).

### Client Self-Service (S14-13, S14-14, S14-15)

El plato fuerte. ClientOrder + ClientOrderLine + ClientOrderSnapshot. Catalog endpoint. CEO review con override. Esto fue auditado 4 veces hasta score 9.6/10.

Las reglas clave:
- **DTO portal separado** — el cliente NUNCA ve base_price, commission_pct, price_index, delta, arbitraje. Solo ve precios finales.
- **Doble freeze** — snapshot al submit (lo que vio el cliente) + snapshot al approve (lo que decidió el CEO). ceo_override_diff registra cambios.
- **Fórmula solo backend** — frontend solo renderiza.
- **Dedup** — content_fingerprint + client_po_number + ventana 30 días.
- **Revision loop** — el CEO puede devolver la orden al cliente. Max 3 revisiones (configurable).

---

## Lo que NO tenés que hacer

- ❌ Editar ENT_OPS_STATE_MACHINE (FROZEN)
- ❌ Inventar precios, comisiones, índices de pago
- ❌ Exponer datos CEO-ONLY en endpoints del portal
- ❌ Calcular precios en frontend
- ❌ Editar PaymentTermPricingVersion in-place (siempre nueva versión)
- ❌ Permitir .all() en queries del portal (siempre ClientScopedManager)

---

## Lo que sí tenés que hacer si te trabás

- Si necesitás un índice de pago real → `# TODO: CEO_INPUT_REQUIRED (CEO-27)` y usá placeholder
- Si un test SM de Sprint 11 falla → tu código tiene un bug
- Si no queda claro si algo es CEO-ONLY o visible para cliente → preguntá

---

## Checklist de entrega

```
FASE 0
[ ] Todas las migrations generadas y aplicadas
[ ] Exclusion constraints activos en PostgreSQL
[ ] resolve_client_price funciona end-to-end
[ ] can_transition_to lee de BrandWorkflowPolicy
[ ] 565 SKUs cargados como ProductMaster
[ ] Tests SM Sprint 11 sin regresión
[ ] ConfigChangeLog registra cambios sensibles

FASE 1 (si se implementa)
[ ] Portal endpoints: 0 datos CEO-ONLY en response
[ ] ClientOrderSnapshot inmutable al submit
[ ] CEO override recalcula via backend
[ ] approve/reject idempotentes
[ ] content_fingerprint dedup funciona
[ ] 22 tests bloqueantes pasando
```

---

## Reporte de ejecución (entregá esto al terminar)

```markdown
## Resultado de ejecución
- **Agente:** AG-02 Alejandro
- **Lote:** LOTE_SM_SPRINT14
- **Status:** DONE / PARTIAL / BLOCKED
- **Fase completada:** 0 / 0+1
- **Archivos creados:** [lista]
- **Archivos modificados:** [lista]
- **Decisiones asumidas:** [lista]
- **Blockers:** [lista o "ninguno"]
- **Tests ejecutados:** [resumen]
- **TODO CEO_INPUT_REQUIRED:** [si quedó alguno]
```
