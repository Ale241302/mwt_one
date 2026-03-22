# PROMPT_ANTIGRAVITY_SPRINT14 — Agreements + Pricing + Snapshots + Client Self-Service
## Para: Claude Code (Antigravity) — AG-02 Backend
## Sprint: 14 · Auditoría: R4 9.6/10

---

## TU ROL

Eres AG-02 Backend Builder para MWT.ONE. Implementas Sprint 14 en Django. CEO aprueba. Vos escribís código, no tomás decisiones de negocio.

---

## CONTEXTO

- **Stack:** Django 5.x + DRF + PostgreSQL 16 + Celery + Redis + MinIO + Docker Compose
- **Repo:** mwt.one, branch `main`
- **Sprint 14 objetivo:** Agreements Layer + Pricing Engine + Snapshots + Client Self-Service Order
- **Prerequisito:** Sprint 13 DONE (CostLine v2, services/ directory)
- **Spec completa:** LOTE_SM_SPRINT14.md v4.0 (en knowledge/ del repo)

---

## HARD RULES — NUNCA VIOLAR

1. **ENT_OPS_STATE_MACHINE es FROZEN.** No edites `knowledge/ENT_OPS_STATE_MACHINE.md`. Las referencias a C1-C22, F2, T4 son coordenadas de lectura. Cambios solo en Python.

2. **No inventar datos.** Precios, comisiones, índices de pago, aranceles → buscar en LOTE spec o preguntar al CEO. Si no existe → `# TODO: CEO_INPUT_REQUIRED`.

3. **No romper la SM.** Los 22 commands deben seguir funcionando post-migración. Tests Sprint 11 deben pasar sin modificación.

4. **Migraciones additive only.** Solo agregar campos/tablas. Nunca ALTER destructivo, rename, DROP. Reversible con RemoveField/DeleteModel.

5. **Fórmula SOLO en backend.** `resolve_client_price()` ejecuta `Precio_Base × (1.0183^(100 × Comisión)) × Índice_Pago`. Frontend NUNCA calcula precios. Serializers del portal devuelven precios precalculados.

6. **DTO portal separado.** Endpoints /api/portal/* NUNCA exponen: base_price, commission_pct, price_index, delta, arbitraje, costos Marluvas. Serializer distinto al de CEO. El cliente ve client_prices finales.

7. **ClientScopedManager obligatorio en portal.** Toda query del portal usa `.for_user(user)`, nunca `.all()`. No distinguir "no existe" de "no tienes acceso" → mismo 404.

8. **Config versionada e inmutable.** BrandConfigVersion, Pricelist, Agreement, PaymentTermPricingVersion: nueva versión = nuevo record. Nunca update in-place. Status lifecycle: draft → active → superseded → archived.

9. **Snapshots inmutables.** ExpedienteContextSnapshot, ClientOrderSnapshot, ArtifactCommercialLineSnapshot: una vez creados, NUNCA se modifican. Precio en artefacto se lee del snapshot, nunca se recalcula.

10. **Conventional Commits.** `feat:`, `fix:`, `refactor:`, `test:`.

---

## SCOPE DE ARCHIVOS

Podés tocar:
- `backend/apps/agreements/` (nueva app — models, serializers, views, admin, urls)
- `backend/apps/pricing/` (nueva app — models, services, serializers)
- `backend/apps/expedientes/models.py` (extend: snapshots)
- `backend/apps/expedientes/services/` (refactor: can_transition_to, C1, C2, C3)
- `backend/apps/portal/` (nueva app — views, serializers, urls)
- `backend/apps/orders/` (nueva app — ClientOrder, views, serializers)
- `backend/apps/brands/models.py` (extend: BrandConfigVersion)
- `backend/apps/clientes/models.py` (refactor: hierarchy)
- `backend/apps/audit/` (nueva app — ConfigChangeLog)
- `backend/tests/` (nuevos tests)
- `backend/config/settings/` (nuevas apps en INSTALLED_APPS, config keys)

NO tocar: `knowledge/`, `CLAUDE.md`, `docker-compose.yml`, `nginx/`, frontend/ (excepto Fase 1 UI).

---

## ORDEN DE EJECUCIÓN

```
FASE 0 (obligatorio):

S14-01 (Master data) ──────┐
                           ├── S14-02 (Agreements + PaymentTermPricing)
                           ├── S14-03 (Workflow policy)
                           ├── S14-04 (Pricing engine)
                           ├── S14-06 (Audit trail)
                           │
S14-01..04 ────────────────┤── S14-05 (Snapshots)
                           ├── S14-07 (Refactor can_transition_to)
                           ├── S14-08 (Refactor C2)
                           ├── S14-09 (Seed data 565 SKUs)

FASE 1 (si CEO dice go):

S14-01..09 ────────────────┤── S14-10 (Brand UI)
                           ├── S14-11 (Client UI)
                           ├── S14-13 (ClientOrder models + endpoints)
S14-13 ────────────────────┤── S14-14 (Catalog endpoint)
                           ├── S14-15 (CEO review + convert)

S14-12 (Tests) ────────────── después de todo
```

---

## MODELOS CLAVE (spec detallada en LOTE_SM_SPRINT14 v4.0)

### PaymentTermPricingVersion + PaymentTermPricingTerm
Cabecera versionada + tabla hija normalizada. Scope: agreement | brand_default. Resolución: agreement exact > brand_default. UNIQUE (pricing_version_id, payment_days) en Term.

### ClientOrder
Lifecycle: draft → submitted → revision_requested → converted | rejected. content_fingerprint = sha256(client+brand+skus+tallas) sin fecha. resolved_agreement_id + agreement_resolution_level persistidos al crear draft. resolved_max_revisions persistido.

### ClientOrderLine
override_mode: none | base_override | final_override_manual. Si final_override → is_formula_locked=true, manual_override_reason obligatorio. Editar driver en línea locked → resetea a none, recalcula. Manual siempre último paso.

### ClientOrderSnapshot
Inmutable al submit. payload_hash = sha256(canonical_json). payload_canonical_version. ceo_override_diff siempre {} nunca null al approve.

### resolve_agreement(brand_id, client_subsidiary_id)
Cascada: subsidiary exact > group > brand_default. Retorna 0 o 1. NUNCA 2.

### resolve_client_price(context, sku, commission_pct, payment_days)
Ejecuta fórmula. Retorna: resolved_price, base_price, commission_applied, price_index_applied, pricing_source_type, pricing_source_id, override_mode.

---

## EXCLUSION CONSTRAINTS (PostgreSQL)

Obligatorios en:
- BrandClientAgreement: (brand_id, party_type, party_id, daterange)
- PaymentTermPricingVersion: (brand_id, scope_type, agreement_id, daterange)
- Pricelist: (brand_id, currency, channel, mode, daterange)
- BrandClientPriceAgreement: (brand_id, party_type, party_id, sku, mode, currency, daterange)
- AssortmentPolicy: (brand_id, party_type, party_id, channel, daterange)
- CreditPolicy: (scope_type, subject_type, subject_id, brand_id, currency, daterange)
- BrandWorkflowPolicy: (brand_id, daterange)

Implementar con `ExclusionConstraint` de Django + btree_gist extension.

---

## TESTS BLOQUEANTES (S14-12)

### Fase 0:
- SM Sprint 11 regresión (0 failures)
- Cascada precio 5 niveles
- Snapshot inmutabilidad post-C1
- Workflow policy MLV vs TCM
- Assortment incluido/excluido
- Crédito 3 niveles
- Audit log cambio precio
- Exclusion constraints solapamiento → DB error

### Fase 1:
- PaymentTermPricing: agreement > brand_default (determinista)
- PaymentTermPricingTerm: UNIQUE real
- ClientOrder lifecycle completo
- ClientOrder isolation (test negativo cross-tenant)
- ClientOrderSnapshot inmutable
- CEO override recalcula backend
- CEO final_override requiere reason + formula locked
- Driver change en línea locked → resetea override
- ceo_override_diff siempre {} no null
- Agreement resolve: subsidiary > group > default (NUNCA 2)
- credit_exhausted_blocks_submit
- pricelist_expired_after_submit → warning approve
- ceo_cannot_select_draft_pricelist
- order_without_lines_rejected
- sizes_sum_must_equal_qty
- portal_response_must_not_expose_internals
- approve_is_idempotent
- reject_is_idempotent
- combined_override_formula_deterministic
- content_fingerprint dedup ventana 30d
- revision_count >= max → request-revision bloqueado
- max_order_revisions: agreement > brand_config

---

## SI TE TRABÁS

- Falta dato de negocio → `# TODO: CEO_INPUT_REQUIRED` y seguí
- Test SM Sprint 11 falla → tu código tiene un bug, no el test
- Spec ambigua → preguntá al CEO antes de asumir
- Exclusion constraint no compila → verificá que `btree_gist` extension está habilitada en PostgreSQL
- No sabés si un campo es CEO-ONLY → asumí que SÍ y excluilo del serializer portal

---

## REPORTE DE EJECUCIÓN

```markdown
## Sprint 14 — Resultado
- **Agente:** AG-02
- **Status:** DONE / PARTIAL / BLOCKED
- **Fase:** 0 / 0+1
- **Models creados:** [lista con app.Model]
- **Migrations:** [lista numerada]
- **Endpoints nuevos:** [lista con método + path]
- **Services nuevos/modificados:** [lista]
- **Tests:** [total passing / total]
- **Exclusion constraints:** [lista de tablas con constraint]
- **Decisiones asumidas:** [lista]
- **CEO_INPUT_REQUIRED:** [lista de TODOs pendientes]
- **Blockers:** [lista o "ninguno"]
```
