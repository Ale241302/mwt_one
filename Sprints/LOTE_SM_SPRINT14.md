# PATCH — LOTE_SM_SPRINT14 v3.1 → v3.2
# Corrección 1 ALTA residual + 2 MEDIA de re-auditoría ChatGPT 9.4/10

---

## FIX HR1 (ALTA) — Cascada agreement determinista cross-scope

Agregar en S14-02 y C4:

Regla de precedencia obligatoria para resolución de BrandClientAgreement:
1. subsidiary exact (party_type=subsidiary, party_id=client_subsidiary_id) — match directo
2. group (party_type=group, party_id=client_group_id) — herencia
3. brand_default (vía BrandConfigVersion defaults) — fallback

resolve_agreement(brand_id, client_subsidiary_id):
  1. Buscar agreement activo con party_type=subsidiary, party_id=subsidiary_id, vigente
  2. Si no → buscar con party_type=group, party_id=subsidiary.group_id, vigente
  3. Si no → null (usar brand defaults)
  4. Siempre retorna 0 o 1 resultado. Nunca 2.

Exclusion constraint existente (v3.1) garantiza max 1 por scope.
Esta regla garantiza que cross-scope no produce ambigüedad.

Persistir resultado: ClientOrder.resolved_agreement_id + ClientOrder.agreement_resolution_level: subsidiary | group | brand_default.

Test bloqueante:
- [ ] agreement_subsidiary + agreement_group ambos activos → resolve retorna subsidiary
- [ ] solo agreement_group activo → resolve retorna group
- [ ] ninguno → resolve retorna null (brand_default)
- [ ] NUNCA retorna 2 resultados

Nota: esta cascada es idéntica a PricePrecedencePolicy (subsidiary > group > pricelist_base). Consistencia arquitectónica.

## FIX HR2 (MEDIA) — Fingerprint sin fecha

Reemplazar en S14-13:

```
# ANTES (v3.1):
order_fingerprint = sha256(client_id + brand_id + sorted(skus) + sorted(tallas_flat) + date)

# DESPUÉS (v3.2):
content_fingerprint = sha256(client_id + brand_id + sorted(skus) + sorted(tallas_flat))
```

- Campo renombrado a content_fingerprint (sin fecha).
- Dedup query: `WHERE content_fingerprint = X AND created_at >= now() - interval '30 days'`
- Esto detecta pedidos con contenido idéntico en ventana 30 días independiente del día de creación.

Test:
- [ ] Orden día 1 y orden idéntica día 15 → mismo content_fingerprint → warning
- [ ] Orden día 1 y orden distinta (1 SKU diferente) día 15 → fingerprint distinto → sin warning

## FIX HN1 (MEDIA) — max_order_revisions anclaje único

En S14-02/S14-13:

- max_order_revisions vive en BrandConfigVersion como default de marca (ej: 3).
- BrandClientAgreement puede override con campo max_order_revisions: int | null. Null = usar brand default.
- Precedencia: agreement (si no null) > brand_config.
- Al crear ClientOrder draft: resolver y persistir resolved_max_revisions: int. No se re-evalúa después.

Test:
- [ ] Brand default 3, agreement null → resolved = 3
- [ ] Brand default 3, agreement override 5 → resolved = 5
- [ ] Orden con resolved_max_revisions=3, revision_count=3 → request-revision bloqueado

---

## Registro auditoría actualizado

| Auditor | Score | Fecha | Hallazgos | Estado |
|---------|-------|-------|-----------|--------|
| ChatGPT | 8.5/10 | 2026-03-20 | H1-H8 (4A, 4M) | Corregidos v3.0 |
| ChatGPT | 9.1/10 | 2026-03-20 | HR1-4+HN1-2 (2A, 4M) | Corregidos v3.1 |
| ChatGPT | 9.4/10 | 2026-03-20 | HR1(A)+HR2(M)+HN1(M) | Corregidos v3.2 |

## Changelog
- v3.2 (2026-03-20): +Cascada agreement determinista subsidiary>group>brand_default con test bloqueante (HR1). +agreement_resolution_level en ClientOrder. +content_fingerprint sin fecha, dedup por query temporal (HR2). +max_order_revisions anclado: BrandConfigVersion default, BrandClientAgreement override, resolved persistido (HN1).
