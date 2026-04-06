# PROMPT ANTIGRAVITY — Sprint 23

Sos un desarrollador senior Django+React ejecutando el Sprint 23 de una plataforma B2B de comercio exterior. Tu trabajo es implementar exactamente lo que dice el lote, sin inventar, sin saltear, sin reinterpretar.

## Contexto del proyecto

- **Stack:** Django 4.2 + DRF + PostgreSQL + Celery + Redis + React + TypeScript + Tailwind
- **Servidor:** Hostinger KVM 8, Docker Compose, dominio mwt.one
- **Repo:** sjoalfaro/mwt-knowledge-hub (backend en backend/, frontend en frontend/)
- **Auth:** JWT con expiración, modelo users_mwtuser (settings.AUTH_USER_MODEL)
- **State machine:** FROZEN — no tocar nada en state_machine/handlers/
- **Patrón de config:** S14-C5 versionado inmutable. ArtifactPolicy = append-only. RebateProgram/CommissionRule = PATCH in-place + ConfigChangeLog (excepción MVP aprobada).
- **Seguridad:** ClientScopedManager con for_user(user). CEO-ONLY data nunca en endpoints portal. Signed URLs para documentos.

## Sprint anterior (S22 — DONE)

Ya implementado y desplegado:
- `resolve_client_price()` v2 con waterfall 4 pasos
- PriceListVersion con N activas + extinción por versión completa
- EarlyPaymentPolicy (cliente × plazo → %)
- GradeItem + _resolve_grade_constraints() (MOQ como grade)
- ClientProductAssignment permanente con cached pricing
- Upload pricelist CSV/Excel en Brand Console Tab 5
- Bulk assignment por product_key
- Recálculo Celery al activar pricelist
- Alerta margen via EventLog event_type='margin.alert'
- 44+ tests

## Sprint 23 — Scope

**Objetivo:** Reglas comerciales: rebates + herencia brand>client>subsidiary + ArtifactPolicy a DB.

**Nueva app:** `backend/apps/commercial/`

### Fase 0 — Modelos y migraciones
- S23-01: RebateProgram (con threshold_type, 7 CheckConstraints incl. valid_date_range)
- S23-02: RebateAssignment (UniqueConstraints condicionales) + RebateLedger + RebateAccrualEntry
- S23-03: CommissionRule (NO-TEMPORAL MVP, 6 UniqueConstraints por scope, CheckConstraint one_level_only)
- S23-04: BrandArtifactPolicyVersion (append-only, UniqueConstraint activa + brand,version)
- S23-05: Resolvers específicos (resolve_rebate_assignment, resolve_commission_rule)

### Fase 1 — Lógica de negocio
- S23-06: calculate_rebate_accrual() con transaction.atomic + select_for_update + IntegrityError catch
- S23-07: liquidate_rebates() Celery task trimestral con effective threshold
- S23-07b: approve_rebate_liquidation() servicio explícito
- S23-08: resolve_commission() con commission_base enum (sale_price|gross_margin)
- S23-09: seed_artifact_policy management command

### Fase 2 — Endpoints
- S23-10: API Rebates (IsCEOOrInternalAgent + portal scoped)
- S23-11: API Comisiones (IsCEO only)
- S23-12: API ArtifactPolicy (INTERNAL, PATCH = append-only)

### Fase 3 — Frontend
- S23-13: Brand Console Tab "Reglas Comerciales" (rebates + comisiones CEO + ArtifactPolicy)
- S23-14: Client Console Tab "Incentivos" (progreso sin montos)
- S23-15: Frontend checks manuales (7 checks)

### Fase 4 — Tests (56+)
- 14 grupos de tests detallados en el lote

## Reglas de ejecución

1. **Ejecutar en orden de fases.** No empezar Fase 1 sin Fase 0 completa y migraciones aplicadas.
2. **No inventar datos.** Si algo no está en el lote, preguntar. Nunca asumir.
3. **No tocar archivos FROZEN.** state_machine/handlers/ es intocable.
4. **Tests primero si hay duda.** Ante ambigüedad, escribir el test que valide el comportamiento esperado y después implementar.
5. **ConfigChangeLog en todo PATCH de RebateProgram y CommissionRule.** Guardar old_value y new_value como JSON.
6. **Commits atómicos por item.** Un commit por S23-XX. Mensaje: `S23-XX: [descripción corta]`.
7. **No hardcodear.** Credenciales en env vars. URLs en config.
8. **Migraciones numeradas.** Nombrar descriptivamente: `0023_rebate_program.py`, `0024_commission_rule.py`, etc.

## Decisiones CEO pendientes — usar estos defaults hasta que se resuelvan

| Decisión | Default temporal | Campo |
|----------|-----------------|-------|
| DEC-S23-01 | calculation_base = NULL, ValueError en runtime si se usa | RebateProgram.calculation_base |
| DEC-S23-02 | liquidation_type = NULL hasta aprobación | RebateLedger.liquidation_type |
| DEC-S23-03 | commission_base = NULL, ValueError en runtime si percentage + NULL | CommissionRule.commission_base |

## Archivos a crear/modificar

Ver tabla completa en el lote. Resumen: 16 archivos (12 nuevos en apps/commercial/, 4 modificados).

## Validación final (Gate)

Antes de avisar que terminaste, verificar estos 12 checks:
- [ ] Rebate accrual concurrency-safe
- [ ] Liquidación → pending_review con effective threshold
- [ ] CEO aprueba → liquidated
- [ ] Override subsidiary no afecta otras
- [ ] Constraints previenen duplicados activos (DB-level)
- [ ] Comisión soporta sale_price Y gross_margin
- [ ] ArtifactPolicy append-only con fallback constante
- [ ] Herencia brand>client>subsidiary en rebates Y comisiones
- [ ] Portal no expone valores sensibles
- [ ] Portal scoped por subsidiary (403 cross-access)
- [ ] Tests verdes (56+)
- [ ] Seed idempotente
