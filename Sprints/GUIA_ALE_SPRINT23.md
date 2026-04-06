# Guía de Ejecución Sprint 23 — AG-02 (Alejandro)

## Resumen

Sprint 23 agrega la capa de reglas comerciales: rebates, comisiones, y ArtifactPolicy migrada a DB. Es una app nueva (`backend/apps/commercial/`) con 7 modelos, 5 servicios, 6 endpoints, 2 tabs frontend, y 56 tests.

**Dependencia:** Sprint 22 DONE (pricing engine). Todo lo de S22 debe estar funcionando antes de empezar.

**Duración estimada:** 2 semanas.

---

## Orden de ejecución

### Día 1-2: Fase 0 — Modelos

1. Crear app `backend/apps/commercial/` y registrar en INSTALLED_APPS
2. Implementar modelos en este orden (por dependencias de FK):
   - `RebateProgram` + `RebateProgramProduct` → migración 0023
   - `RebateAssignment` + `RebateLedger` + `RebateAccrualEntry` → migración 0024
   - `CommissionRule` → migración 0025
   - `BrandArtifactPolicyVersion` → migración 0026
3. Aplicar migraciones: `python manage.py migrate`
4. Verificar: `python manage.py showmigrations commercial`

**⚠️ Ojo con las constraints:**
- RebateProgram tiene 7 CheckConstraints (threshold consistency + valid_date_range). Verificar que pasen con `python manage.py check`.
- CommissionRule tiene 6 UniqueConstraints condicionales por scope + 1 CheckConstraint. Son muchas — copiar exacto del lote.
- BrandArtifactPolicyVersion tiene 2 UniqueConstraints (activa por brand + brand,version).

### Día 3-4: Fase 0 cont. — Resolvers + Permissions

5. Crear `commercial/permissions.py`:
   - `IsCEO` — verifica `request.user.role == 'CEO'` (NO `is_staff`)
   - `IsCEOOrInternalAgent` — CEO o AGENT_*
   - `IsClientUser` — CLIENT_*
6. Crear `commercial/services/rebates.py`:
   - `resolve_rebate_assignment()` — con order_by('-created_at')
   - `_build_rebate_result()` — effective threshold
7. Crear `commercial/services/commissions.py`:
   - `resolve_commission_rule()` — cascada 6 niveles, order_by('-created_at')
8. Crear `commercial/services/artifact_policy.py`:
   - `resolve_artifact_policy()` — DB → fallback Python
   - `update_artifact_policy()` — **desactivar ANTES de crear** (UniqueConstraint)

### Día 5-7: Fase 1 — Lógica de negocio

9. `calculate_rebate_accrual()` en services/rebates.py
   - **CRÍTICO:** todo dentro de `transaction.atomic()` + `select_for_update()` en ledger
   - Idempotencia via `IntegrityError` catch en `RebateAccrualEntry.create()`
   - Recalcular totales con `aggregate()`, NO con `F()` incremental
   - `_calculate_qualifying_amount()` con branch `invoiced` vs `list_price` — ValueError si calculation_base NULL
   - `_calculate_qualifying_units()` — simple sum de quantity

10. `liquidate_rebates()` Celery task en tasks.py
    - Registrar en `celery.py` beat schedule (crontab: día 1 de cada trimestre)
    - Usa effective threshold (assignment custom > program default)
    - Solo mueve a `pending_review` — NUNCA liquida automáticamente

11. `approve_rebate_liquidation()` en services/rebates.py
    - Valida status == 'pending_review', liquidation_type válido
    - Setea liquidated_at, liquidated_by
    - Genera EventLog `rebate.liquidated`
    - **NO genera ConfigChangeLog** (es operación, no config)

12. `resolve_commission()` en services/commissions.py
    - Soporta `commission_base`: sale_price y gross_margin
    - **ValueError si commission_base es NULL en regla porcentual**
    - Acepta `cost_price` (obligatorio si gross_margin)

13. `seed_artifact_policy` management command
    - Idempotente: skip brands que ya tienen policy
    - ConfigChangeLog con `json.dumps(ARTIFACT_POLICY)` real, no placeholder

### Día 8-9: Fase 2 — Endpoints

14. Crear serializers.py (3 serializers):
    - `RebateProgramInternalSerializer` — fields all
    - `RebateLedgerInternalSerializer` — fields all + entries_count
    - `RebateProgressPortalSerializer` — program_name, period, threshold_type, progress_percentage, threshold_met (NADA más)

15. Crear views.py con permission_classes explícitas:
    - Rebates: `IsCEOOrInternalAgent`. Ledger queryset scoped por brand asignado para agents.
    - Approve: `IsCEO`
    - Portal progress: `IsClientUser`, scoped por subsidiary
    - Comisiones: `IsCEO` (nunca AGENT, nunca CLIENT)
    - ArtifactPolicy: `IsCEOOrInternalAgent`

16. Crear urls.py y registrar en config/urls.py

### Día 10-12: Fase 3 — Frontend

17. Brand Console — Tab "Reglas Comerciales":
    - Sección Rebates: CRUD, lista con filtros
    - Sección Comisiones: solo renderizar si `user.role === 'CEO'`
    - Sección ArtifactPolicy: viewer + historial + botón seed

18. Client Console — Tab "Incentivos":
    - Barra progreso por período
    - Soportar threshold_type: amount (barra %), units (barra %), none (100%)
    - **NUNCA mostrar:** rebate_value, accrued_rebate, umbrales, comisiones

### Día 13-14: Fase 4 — Tests

19. 56 tests en 14 grupos (ver lote para detalle)
    - Priorizar: T4 (constraints), T5 (accrual + concurrencia), T12 (serializer security), T13 (access control 403)
    - Correr: `python manage.py test apps.commercial --verbosity=2`

---

## action_source para EventLog

Usar estos valores exactos (no inventar nuevos):

```
system_rebate_liquidation
approve_rebate_liquidation
create_rebate_program
create_commission_rule
update_artifact_policy
seed_artifact_policy
system_resolve_artifact_policy
```

## event_type para EventLog

```
rebate.pending_review
rebate.threshold_not_met
rebate.liquidated
commission.rule_created
artifact_policy.updated
artifact_policy.seeded
artifact_policy.integrity_error
```

---

## Decisiones pendientes CEO — NO resolver vos

Estos 3 campos quedan NULL hasta que el CEO decida. Si el código los necesita y están NULL → ValueError con mensaje claro.

| Campo | Modelo | Qué hacer si NULL |
|-------|--------|-------------------|
| calculation_base | RebateProgram | ValueError en _calculate_qualifying_amount() |
| liquidation_type | RebateLedger | Se define al aprobar (approve endpoint) |
| commission_base | CommissionRule | ValueError en resolve_commission() si percentage |

---

## Errores comunes — evitar

1. **No crear nueva versión de ArtifactPolicy sin desactivar la anterior primero.** El UniqueConstraint va a reventar. Orden: desactivar → crear.
2. **No usar `is_staff` para verificar CEO.** Usar `role == 'CEO'` explícitamente.
3. **No usar `.first()` sin `order_by()`.** Siempre `order_by('-created_at').first()`.
4. **No usar `F()` para incrementar totales en RebateLedger.** Usar `aggregate()` desde entries.
5. **No exponer comisiones en ningún endpoint de portal.** Es CEO-ONLY.
6. **No tocar state_machine/handlers/.** FROZEN.
7. **No tocar BrandWorkflowPolicy de S14.** ArtifactPolicy es tabla separada.

---

## Checklist final

Antes de avisar que terminaste:

```
[ ] Migraciones aplicadas sin errores
[ ] python manage.py check sin warnings
[ ] 56+ tests verdes
[ ] seed_artifact_policy funciona y es idempotente
[ ] CEO puede crear programa rebate, asignar, aprobar liquidación
[ ] CLIENT ve progreso sin montos
[ ] AGENT no ve comisiones (403)
[ ] CLIENT subsidiary A no ve datos de subsidiary B (403)
[ ] ArtifactPolicy PATCH crea nueva versión (verificar en DB)
[ ] Celery beat tiene liquidate_rebates en schedule
[ ] docker-compose up sin errores
[ ] Git commit por item (S23-01 a S23-15)
```

Cuando todo esté verde, avisame con el resumen de ejecución.
