# LOTE_SM_SPRINT23 — Reglas Comerciales: Rebates + Herencia + ArtifactPolicy a DB
id: LOTE_SM_SPRINT23
version: 1.4
visibility: [INTERNAL]
domain: Plataforma (IDX_PLATAFORMA)
status: DRAFT
stamp: DRAFT v1.4 — 2026-04-05
tipo: Lote ruteado (ref → PLB_ORCHESTRATOR §E)
sprint: 23
priority: P0 (camino crítico → bloquea S24 portal autogestión)
depends_on: LOTE_SM_SPRINT22 (DONE — pricing engine + pricelists + assignments)
refs: ENT_OPS_STATE_MACHINE (FROZEN v1.2.2),
      ENT_COMERCIAL_PRICING (SSOT — price ladder),
      ENT_COMERCIAL_COSTOS (SSOT — estructura costos),
      LOTE_SM_SPRINT14 (DONE — agreements layer, BrandWorkflowPolicy v1),
      LOTE_SM_SPRINT20 (DONE — proformas + ArtifactPolicy constante Python),
      LOTE_SM_SPRINT22 (DONE — pricing engine, resolve_client_price() v2, EarlyPaymentPolicy, GradeItem),
      ROADMAP_EXTENDIDO_POST_DIRECTRIZ (VIGENTE — numeración definitiva)

changelog:
  - v1.0 (2026-04-05): Compilación inicial. 15 items en 4 fases. Fuente: ROADMAP_EXTENDIDO S23 + estado real post-S22. Decisiones pendientes CEO identificadas: 3 (DEC-S23-01 a DEC-S23-03).
  - v1.1 (2026-04-05): Fixes auditoría R1 (ChatGPT 8.2/10 — 4B + 3M + 2m). B1: ArtifactPolicy reescrita como append-only (BrandArtifactPolicyVersion) con constraint una sola activa por brand, PATCH clona+desactiva+crea dentro de transaction.atomic(). B2: UniqueConstraints condicionales en RebateAssignment y CommissionRule; resolvers con order_by explícito (-created_at). B3: resolve_commercial_rule() eliminado, reemplazado por resolvers específicos. B4: calculation_base nullable hasta CEO; +commission_base enum soportando ambas opciones. M1: accrual con transaction.atomic() + select_for_update() + IntegrityError catch + recálculo desde entries. M2: effective threshold + threshold_type. M3: permission_classes explícitas + for_user scoping + tests 403. m1: seed guarda JSON real. m2: +8 tests edge cases.
  - v1.2 (2026-04-05): Fixes auditoría R2 (ChatGPT 9.1/10 — 2B + 3M + 2m). B1-R2: update_artifact_policy() desactiva antes de crear. B2-R2: 6 constraints separadas por scope. M1-R2: CheckConstraints threshold_type. M2-R2: reference_date en comisiones. M3-R2: approve_rebate_liquidation() service. m1-R2: EventLog integrity_error. m2-R2: UniqueConstraint(brand,version).
  - v1.3 (2026-04-05): Fixes auditoría R3 (ChatGPT 9.3/10 — 1B + 3M + 2m). B1-R3: CommissionRule no-temporal MVP. M1-R3: ValueError si commission_base NULL. M2-R3: +2 CheckConstraints cruzados. M3-R3: docstring approve corregida. m1-R3: tabla archivos 52+. m2-R3: action_source agregado.
  - v1.4 (2026-04-05): Fixes auditoría R4 (ChatGPT 9.4/10 — 0B + 3M + 2m). M1-R4: excepción MVP explícita para PATCH in-place en RebateProgram/CommissionRule (con ConfigChangeLog); append-only solo para ArtifactPolicy; migración completa diferida a v2. M2-R4: pseudocódigo _calculate_qualifying_amount() con ambos paths (invoiced vs list_price) + ValueError si calculation_base NULL + _calculate_qualifying_units(). M3-R4: T2 expandido a 6 tests (cross-field exclusion + valid_date_range), T5 expandido a 9 (+invoiced, +list_price). m1-R4: system_rebate_accrual eliminado de action_source (accrual no genera EventLog, trazabilidad via RebateAccrualEntry). m2-R4: CheckConstraint valid_to >= valid_from en RebateProgram. Total tests: 56.

---

## Contexto

Sprint 23 extiende la capa comercial de S22 con tres capacidades:

1. **Rebates** — programas de incentivo por volumen/período que devuelven un % o monto al cliente al cierre de trimestre.
2. **Herencia brand > client > subsidiary** — reglas comerciales se definen a nivel brand, heredan a client, override a subsidiary.
3. **ArtifactPolicy a DB** — constante Python migra a tabla versionada append-only con fallback.

**Estado post-Sprint 22 (DONE — 2026-04-05):**
- Pricing engine: `resolve_client_price()` v2, waterfall 4 pasos (CPA → BCPA → PriceList MIN → manual)
- N pricelists activas con extinción por versión completa
- EarlyPaymentPolicy, GradeItem + _resolve_grade_constraints()
- Upload pricelist CSV/Excel, ClientProductAssignment permanente, bulk assignment
- Recálculo Celery, alerta margen via EventLog, 44+ tests
- Brand Console Tab 4/5, Client Console Tab Catalog

**Estado post-Sprint 14 (agreements):** BrandWorkflowPolicy v1, ClientProductAssignment v1, ExpedienteContextSnapshot
**Estado post-Sprint 20/20B (ArtifactPolicy):** artifact_policy.py constante Python, custom_artifact_policy, SG-01 confirmada

---

## Decisiones ya resueltas (NO preguntar de nuevo)

| Decisión | Ref | Detalle |
|----------|-----|---------|
| ArtifactPolicy constante → DB en S23 | SG-01 / S20 | Tabla versionada append-only con fallback |
| ClientProductAssignment permanente | DEC-S22-01 | is_active toggle |
| N pricelists activas con extinción | DEC-S22-02 | MIN(precio), extinción por versión completa |
| Pronto pago como policy por cliente | DEC-S22-03 | EarlyPaymentPolicy: cliente × plazo → % |
| Rebate anual/trimestral | DEC-S22-03b | Liquidación trimestral, programa anual |
| Versionado config inmutable | S14-C5 | Nuevo cambio = nueva versión + ConfigChangeLog. **Excepción MVP aprobada (R4):** RebateProgram y CommissionRule se editan PATCH in-place con ConfigChangeLog (audit trail) pero sin append-only. ArtifactPolicy sí es append-only. Migrar a append-only para todas las reglas comerciales queda diferido a v2 junto con temporalidad en CommissionRule. |
| Proforma como unidad operativa | DIRECTRIZ / S20 | Mode B o C a nivel proforma |

## Decisiones pendientes CEO (resolver ANTES de ejecutar)

| ID | Decisión | Opciones | Recomendación | Impacto |
|----|----------|----------|---------------|---------|
| DEC-S23-01 | Rebate: % sobre facturado o sobre precio de lista | A) Sobre facturado, B) Sobre precio de lista | **A) Sobre facturado** — estándar industria, más simple | calculation_base en RebateProgram (nullable hasta decisión) |
| DEC-S23-02 | Liquidación rebate: crédito o pago directo | A) Crédito, B) Pago directo | **A) Crédito** para MVP | RebateLedger y flujo de caja |
| DEC-S23-03 | Comisión MWT: % sobre precio venta o % sobre margen | A) Sobre precio venta, B) Sobre margen bruto | **A) Sobre precio** — no expone costos | commission_base enum. Ambas opciones soportadas sin refactor |

---

## Fase 0 — Modelos y migraciones

### S23-01 · RebateProgram

```python
class RebateProgram(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    brand = models.ForeignKey('brands.Brand', on_delete=models.PROTECT)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    period_type = models.CharField(max_length=20, choices=[('quarterly', 'Trimestral'), ('annual', 'Anual')])
    valid_from = models.DateField()
    valid_to = models.DateField()
    rebate_type = models.CharField(max_length=20, choices=[('percentage', 'Porcentaje'), ('fixed_amount', 'Monto fijo por unidad')])
    rebate_value = models.DecimalField(max_digits=10, decimal_places=4)
    # FIX B4: nullable hasta decisión CEO
    calculation_base = models.CharField(max_length=20, choices=[('invoiced', 'Sobre facturado'), ('list_price', 'Sobre precio lista')], null=True, blank=True)
    # FIX M2: threshold_type explícito
    threshold_type = models.CharField(max_length=20, choices=[('amount', 'Por monto'), ('units', 'Por unidades'), ('none', 'Sin umbral')], default='none')
    min_threshold_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    min_threshold_units = models.IntegerField(null=True, blank=True)
    applies_to_all_products = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    class Meta:
        indexes = [models.Index(fields=['brand', 'is_active']), models.Index(fields=['valid_from', 'valid_to'])]
        constraints = [
            # FIX M1-R2: threshold_type consistency
            models.CheckConstraint(check=~models.Q(threshold_type='amount', min_threshold_amount__isnull=True), name='threshold_amount_requires_value'),
            models.CheckConstraint(check=~models.Q(threshold_type='units', min_threshold_units__isnull=True), name='threshold_units_requires_value'),
            models.CheckConstraint(check=~models.Q(threshold_type='none', min_threshold_amount__isnull=False), name='threshold_none_no_amount'),
            models.CheckConstraint(check=~models.Q(threshold_type='none', min_threshold_units__isnull=False), name='threshold_none_no_units'),
            # FIX M2-R3: cross-field exclusion — amount no permite units poblado y viceversa
            models.CheckConstraint(check=~models.Q(threshold_type='amount', min_threshold_units__isnull=False), name='threshold_amount_no_units'),
            models.CheckConstraint(check=~models.Q(threshold_type='units', min_threshold_amount__isnull=False), name='threshold_units_no_amount'),
            # FIX m2-R4: rango de fechas válido
            models.CheckConstraint(check=models.Q(valid_to__gte=models.F('valid_from')), name='rebate_program_valid_date_range'),
        ]

class RebateProgramProduct(models.Model):
    rebate_program = models.ForeignKey(RebateProgram, on_delete=models.CASCADE, related_name='product_scope')
    product_key = models.CharField(max_length=50)
    class Meta:
        unique_together = ['rebate_program', 'product_key']
```

### S23-02 · RebateAssignment + RebateLedger + RebateAccrualEntry

```python
class RebateAssignment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    rebate_program = models.ForeignKey(RebateProgram, on_delete=models.PROTECT)
    client = models.ForeignKey('clients.Client', on_delete=models.PROTECT, null=True, blank=True)
    client_subsidiary = models.ForeignKey('clients.ClientSubsidiary', on_delete=models.PROTECT, null=True, blank=True)
    custom_rebate_value = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    custom_min_threshold_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    custom_min_threshold_units = models.IntegerField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        constraints = [
            models.CheckConstraint(
                check=(models.Q(client__isnull=False, client_subsidiary__isnull=True) | models.Q(client__isnull=True, client_subsidiary__isnull=False)),
                name='rebate_assignment_one_level_only'),
            # FIX B2: Solo 1 activo por programa×client
            models.UniqueConstraint(fields=['rebate_program', 'client'], condition=models.Q(is_active=True, client__isnull=False), name='unique_active_rebate_per_program_client'),
            # FIX B2: Solo 1 activo por programa×subsidiary
            models.UniqueConstraint(fields=['rebate_program', 'client_subsidiary'], condition=models.Q(is_active=True, client_subsidiary__isnull=False), name='unique_active_rebate_per_program_subsidiary'),
        ]
        indexes = [models.Index(fields=['rebate_program', 'client']), models.Index(fields=['rebate_program', 'client_subsidiary'])]

class RebateLedger(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    rebate_assignment = models.ForeignKey(RebateAssignment, on_delete=models.PROTECT)
    period_start = models.DateField()
    period_end = models.DateField()
    total_qualifying_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    total_qualifying_units = models.IntegerField(default=0)
    accrued_rebate = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=[('accruing', 'Acumulando'), ('pending_review', 'Pendiente CEO'), ('liquidated', 'Liquidado'), ('cancelled', 'Cancelado')], default='accruing')
    liquidated_at = models.DateTimeField(null=True, blank=True)
    liquidated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True)
    liquidation_type = models.CharField(max_length=20, choices=[('credit', 'Crédito'), ('payment', 'Pago directo')], null=True, blank=True)
    class Meta:
        indexes = [models.Index(fields=['rebate_assignment', 'period_start']), models.Index(fields=['status'])]
        unique_together = ['rebate_assignment', 'period_start', 'period_end']

class RebateAccrualEntry(models.Model):
    ledger = models.ForeignKey(RebateLedger, on_delete=models.CASCADE, related_name='entries')
    proforma = models.ForeignKey('proformas.Proforma', on_delete=models.PROTECT)
    qualifying_amount = models.DecimalField(max_digits=14, decimal_places=2)
    qualifying_units = models.IntegerField()
    accrued_rebate = models.DecimalField(max_digits=14, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        unique_together = ['ledger', 'proforma']
```

### S23-03 · CommissionRule

```python
class CommissionRule(models.Model):
    """
    Modelo NO-TEMPORAL (MVP): una sola regla viva por scope.
    Historial via ConfigChangeLog + is_active toggle.
    Temporalidad real (valid_from/to, solapamiento) diferida a v2.
    FIX B1-R3: eliminados valid_from/valid_to para resolver contradicción
    entre vigencia temporal y unicidad activa por scope.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    brand = models.ForeignKey('brands.Brand', on_delete=models.PROTECT)
    product_key = models.CharField(max_length=50, null=True, blank=True)
    commission_type = models.CharField(max_length=20, choices=[('percentage', 'Porcentaje'), ('fixed_per_unit', 'Monto fijo')])
    # FIX B4: soporta ambas opciones DEC-S23-03
    # FIX M1-R3: nullable pero ValueError si NULL en percentage (no asumir sale_price)
    commission_base = models.CharField(max_length=20, choices=[('sale_price', 'Sobre precio venta'), ('gross_margin', 'Sobre margen bruto')], null=True, blank=True)
    commission_value = models.DecimalField(max_digits=10, decimal_places=4)
    client = models.ForeignKey('clients.Client', on_delete=models.PROTECT, null=True, blank=True)
    client_subsidiary = models.ForeignKey('clients.ClientSubsidiary', on_delete=models.PROTECT, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        constraints = [
            # FIX B2: one_level_only
            models.CheckConstraint(
                check=(models.Q(client__isnull=True, client_subsidiary__isnull=True) | models.Q(client__isnull=False, client_subsidiary__isnull=True) | models.Q(client__isnull=True, client_subsidiary__isnull=False)),
                name='commission_rule_one_level_only'),
            # FIX B2-R2: constraints separadas por scope (NULLs en unique no previenen duplicados en PG)
            # Brand default (no product)
            models.UniqueConstraint(fields=['brand'], condition=models.Q(is_active=True, product_key__isnull=True, client__isnull=True, client_subsidiary__isnull=True), name='unique_commission_brand_default'),
            # Brand + product
            models.UniqueConstraint(fields=['brand', 'product_key'], condition=models.Q(is_active=True, client__isnull=True, client_subsidiary__isnull=True, product_key__isnull=False), name='unique_commission_brand_product'),
            # Client default (no product)
            models.UniqueConstraint(fields=['brand', 'client'], condition=models.Q(is_active=True, product_key__isnull=True, client__isnull=False, client_subsidiary__isnull=True), name='unique_commission_client_default'),
            # Client + product
            models.UniqueConstraint(fields=['brand', 'client', 'product_key'], condition=models.Q(is_active=True, client__isnull=False, client_subsidiary__isnull=True, product_key__isnull=False), name='unique_commission_client_product'),
            # Subsidiary default (no product)
            models.UniqueConstraint(fields=['brand', 'client_subsidiary'], condition=models.Q(is_active=True, product_key__isnull=True, client__isnull=True, client_subsidiary__isnull=False), name='unique_commission_subsidiary_default'),
            # Subsidiary + product
            models.UniqueConstraint(fields=['brand', 'client_subsidiary', 'product_key'], condition=models.Q(is_active=True, client__isnull=True, client_subsidiary__isnull=False, product_key__isnull=False), name='unique_commission_subsidiary_product'),
        ]
        indexes = [models.Index(fields=['brand', 'product_key', 'is_active']), models.Index(fields=['brand', 'client', 'is_active'])]
```

**Nota 1:** CommissionRule es CEO-ONLY data. Si DEC-S23-03=gross_margin, resolve_commission() requiere cost_price.

### S23-04 · BrandArtifactPolicyVersion (append-only — FIX B1)

Tabla separada de BrandWorkflowPolicy. Cada edición clona la anterior + desactiva + crea nueva en transaction.atomic().

```python
class BrandArtifactPolicyVersion(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    brand = models.ForeignKey('brands.Brand', on_delete=models.PROTECT, related_name='artifact_policy_versions')
    version = models.IntegerField()
    artifact_policy = models.JSONField()
    # JSON: {"C5_COTIZACION_APROBADA": {"artifacts": ["ART-01"], "conditions": {"mode": "B"}}, ...}
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True)
    superseded_by = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True)
    change_reason = models.CharField(max_length=500, blank=True)
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['brand'], condition=models.Q(is_active=True), name='unique_active_artifact_policy_per_brand'),
            # FIX m2-R2: unicidad por (brand, version) para invariancia append-only
            models.UniqueConstraint(fields=['brand', 'version'], name='unique_artifact_policy_brand_version'),
        ]
        indexes = [models.Index(fields=['brand', 'is_active']), models.Index(fields=['brand', 'version'])]
        ordering = ['-version']
```

**resolve_artifact_policy():**

```python
def resolve_artifact_policy(brand_id, transition, mode):
    """Cascada: DB (BrandArtifactPolicyVersion) → constante Python."""
    try:
        pv = BrandArtifactPolicyVersion.objects.get(brand_id=brand_id, is_active=True)
        if transition in pv.artifact_policy:
            rule = pv.artifact_policy[transition]
            cond = rule.get('conditions', {})
            if 'mode' in cond and cond['mode'] != mode:
                pass  # No aplica, fallback
            else:
                return {'artifacts': rule['artifacts'], 'source': 'db', 'policy_version': pv.version}
    except BrandArtifactPolicyVersion.DoesNotExist:
        pass
    except BrandArtifactPolicyVersion.MultipleObjectsReturned:
        import logging; logging.error(f"Multiple active policies for brand {brand_id}")
        # FIX m1-R2: alerta operativa, no solo log silencioso
        EventLog.objects.create(event_type='artifact_policy.integrity_error', action_source='system_resolve_artifact_policy',
            payload={'brand_id': str(brand_id), 'error': 'MultipleObjectsReturned — constraint violation'})
    
    from apps.expedientes.artifact_policy import ARTIFACT_POLICY
    if transition in ARTIFACT_POLICY:
        return {'artifacts': ARTIFACT_POLICY[transition].get('artifacts', []), 'source': 'python_constant', 'policy_version': 0}
    return {'artifacts': [], 'source': 'none', 'policy_version': 0}
```

**update_artifact_policy() — PATCH (append-only, FIX B1-R2: desactivar antes de crear):**

```python
def update_artifact_policy(brand_id, new_policy, user, reason):
    with transaction.atomic():
        current = BrandArtifactPolicyVersion.objects.select_for_update().filter(brand_id=brand_id, is_active=True).first()
        new_ver = (current.version + 1) if current else 1
        old_snapshot = json.dumps(current.artifact_policy) if current else None
        # FIX B1-R2: desactivar primero para no chocar con UniqueConstraint
        if current:
            current.is_active = False
            current.save(update_fields=['is_active'])
        # Crear nueva versión (ahora no hay otra activa)
        new_obj = BrandArtifactPolicyVersion.objects.create(
            brand_id=brand_id, version=new_ver, artifact_policy=new_policy,
            is_active=True, created_by=user, change_reason=reason)
        # Vincular superseded_by en la anterior
        if current:
            current.superseded_by = new_obj
            current.save(update_fields=['superseded_by'])
        ConfigChangeLog.objects.create(
            model_name='BrandArtifactPolicyVersion', record_id=str(new_obj.id),
            field_name='artifact_policy', old_value=old_snapshot,
            new_value=json.dumps(new_policy), changed_by=user, change_reason=reason)
    return new_obj
```

### S23-05 · Resolvers específicos (FIX B3 — no genéricos)

**resolve_rebate_assignment():**

```python
def resolve_rebate_assignment(rebate_program_id, client_id, subsidiary_id):
    """Cascada: subsidiary override > client assignment."""
    if subsidiary_id:
        sub = RebateAssignment.objects.filter(
            rebate_program_id=rebate_program_id, client_subsidiary_id=subsidiary_id, is_active=True
        ).order_by('-created_at').first()
        if sub:
            return _build_rebate_result(sub, 'subsidiary', True)
    if client_id:
        cli = RebateAssignment.objects.filter(
            rebate_program_id=rebate_program_id, client_id=client_id,
            client_subsidiary__isnull=True, is_active=True
        ).order_by('-created_at').first()
        if cli:
            return _build_rebate_result(cli, 'client', False)
    return {'assignment': None, 'level': 'none', 'is_override': False, 'effective_rebate_value': None, 'effective_threshold': None}

def _build_rebate_result(assignment, level, is_override):
    """FIX M2: effective threshold = assignment custom > program default."""
    program = assignment.rebate_program
    eff_value = assignment.custom_rebate_value or program.rebate_value
    if program.threshold_type == 'amount':
        eff_threshold = assignment.custom_min_threshold_amount or program.min_threshold_amount
    elif program.threshold_type == 'units':
        eff_threshold = assignment.custom_min_threshold_units or program.min_threshold_units
    else:
        eff_threshold = None
    return {'assignment': assignment, 'level': level, 'is_override': is_override, 'effective_rebate_value': eff_value, 'effective_threshold': eff_threshold}
```

**resolve_commission_rule():**

```python
def resolve_commission_rule(brand_id, client_id, subsidiary_id, product_key=None):
    """Cascada: subsidiary+product > subsidiary default > client+product > client default > brand+product > brand default.
    FIX B1-R3: modelo no-temporal MVP. Sin valid_from/to ni reference_date. Una regla activa por scope."""
    base = CommissionRule.objects.filter(brand_id=brand_id, is_active=True)
    order = ['-created_at']
    
    for level_filters, level, override in [
        ({'client_subsidiary_id': subsidiary_id}, 'subsidiary', True) if subsidiary_id else (None, None, None),
        ({'client_id': client_id, 'client_subsidiary__isnull': True}, 'client', False) if client_id else (None, None, None),
        ({'client__isnull': True, 'client_subsidiary__isnull': True}, 'brand', False),
    ]:
        if level_filters is None:
            continue
        for pk_filter in ([{'product_key': product_key}] if product_key else []) + [{'product_key__isnull': True}]:
            rule = base.filter(**level_filters, **pk_filter).order_by(*order).first()
            if rule:
                return {'rule': rule, 'level': level, 'is_override': override}
    return {'rule': None, 'level': 'none', 'is_override': False}
```

**Nota 2:** Resolvers específicos, NO genéricos. RebateAssignment no tiene product_key ni brand directo. EarlyPaymentPolicy de S22 mantiene su propio resolver.

---

## Fase 1 — Lógica de negocio

### S23-06 · calculate_rebate_accrual() — FIX M1 concurrencia

```python
def calculate_rebate_accrual(proforma_id):
    """Concurrency-safe: transaction.atomic + select_for_update + IntegrityError catch."""
    proforma = Proforma.objects.select_related('expediente__subsidiary__client').get(id=proforma_id)
    subsidiary = proforma.expediente.subsidiary
    client = subsidiary.client
    brand = proforma.expediente.brand
    accruals = []
    
    assignments = RebateAssignment.objects.filter(
        is_active=True, rebate_program__is_active=True, rebate_program__brand=brand,
        rebate_program__valid_from__lte=proforma.closed_at.date(),
        rebate_program__valid_to__gte=proforma.closed_at.date(),
    ).filter(models.Q(client=client) | models.Q(client_subsidiary=subsidiary)).select_related('rebate_program')
    
    for assignment in assignments:
        program = assignment.rebate_program
        if not program.applies_to_all_products:
            pf_keys = set(proforma.lines.values_list('product__product_key', flat=True))
            prog_keys = set(program.product_scope.values_list('product_key', flat=True))
            if not (pf_keys & prog_keys):
                continue
        # Herencia: subsidiary override gana
        if assignment.client_id and RebateAssignment.objects.filter(
            rebate_program=program, client_subsidiary=subsidiary, is_active=True).exists():
            continue
        
        period_start, period_end = _get_rebate_period(program.period_type, proforma.closed_at.date())
        
        with transaction.atomic():
            ledger, _ = RebateLedger.objects.get_or_create(
                rebate_assignment=assignment, period_start=period_start, period_end=period_end,
                defaults={'status': 'accruing'})
            ledger = RebateLedger.objects.select_for_update().get(id=ledger.id)
            
            eff_value = assignment.custom_rebate_value or program.rebate_value
            q_amount = _calculate_qualifying_amount(proforma, program, assignment)
            q_units = _calculate_qualifying_units(proforma, program)
            accrued = q_amount * eff_value if program.rebate_type == 'percentage' else q_units * eff_value
            
            try:
                RebateAccrualEntry.objects.create(ledger=ledger, proforma=proforma,
                    qualifying_amount=q_amount, qualifying_units=q_units, accrued_rebate=accrued)
            except IntegrityError:
                continue  # Idempotente
            
            # Recalcular desde entries (más seguro que F() incremental)
            totals = ledger.entries.aggregate(
                ta=models.Sum('qualifying_amount'), tu=models.Sum('qualifying_units'), tr=models.Sum('accrued_rebate'))
            ledger.total_qualifying_amount = totals['ta'] or 0
            ledger.total_qualifying_units = totals['tu'] or 0
            ledger.accrued_rebate = totals['tr'] or 0
            ledger.save(update_fields=['total_qualifying_amount', 'total_qualifying_units', 'accrued_rebate'])
            accruals.append({'rebate_assignment_id': str(assignment.id), 'accrued_amount': float(accrued), 'period': f"{period_start} — {period_end}"})
    return accruals

def _get_rebate_period(period_type, ref_date):
    if period_type == 'quarterly':
        q = (ref_date.month - 1) // 3
        ps = date(ref_date.year, q * 3 + 1, 1)
        pe = date(ref_date.year if q < 3 else ref_date.year + 1, (q + 1) * 3 + 1 if q < 3 else 1, 1) - timedelta(days=1)
    else:
        ps, pe = date(ref_date.year, 1, 1), date(ref_date.year, 12, 31)
    return ps, pe

def _calculate_qualifying_amount(proforma, program, assignment):
    """FIX M2-R4: soporta ambos paths de DEC-S23-01 (invoiced vs list_price)."""
    if program.calculation_base is None:
        raise ValueError(f"calculation_base es NULL en RebateProgram {program.id}. Resolver DEC-S23-01 antes de usar.")
    
    lines = proforma.lines.all()
    if not program.applies_to_all_products:
        scope_keys = set(program.product_scope.values_list('product_key', flat=True))
        lines = lines.filter(product__product_key__in=scope_keys)
    
    if program.calculation_base == 'invoiced':
        # Monto que el cliente pagó (post-descuento pronto pago, post-pricing)
        return sum(line.unit_price * line.quantity for line in lines)
    else:  # list_price
        # Precio de lista base (pre-descuento) — requiere acceso a base_price del snapshot
        return sum(line.base_list_price * line.quantity for line in lines)

def _calculate_qualifying_units(proforma, program):
    lines = proforma.lines.all()
    if not program.applies_to_all_products:
        scope_keys = set(program.product_scope.values_list('product_key', flat=True))
        lines = lines.filter(product__product_key__in=scope_keys)
    return sum(line.quantity for line in lines)
```

### S23-07 · liquidate_rebates() — FIX M2 effective threshold

```python
@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def liquidate_rebates(self):
    today = date.today()
    with transaction.atomic():
        for ledger in RebateLedger.objects.filter(status='accruing', period_end__lt=today).select_for_update().select_related('rebate_assignment__rebate_program', 'rebate_assignment'):
            assignment = ledger.rebate_assignment
            program = assignment.rebate_program
            # FIX M2: effective threshold
            meets = True
            if program.threshold_type == 'amount':
                eff = assignment.custom_min_threshold_amount or program.min_threshold_amount
                if eff and ledger.total_qualifying_amount < eff: meets = False
            elif program.threshold_type == 'units':
                eff = assignment.custom_min_threshold_units or program.min_threshold_units
                if eff and ledger.total_qualifying_units < eff: meets = False
            
            if meets and ledger.accrued_rebate > 0:
                ledger.status = 'pending_review'
                ledger.save(update_fields=['status'])
                EventLog.objects.create(event_type='rebate.pending_review', action_source='system_rebate_liquidation',
                    payload={'ledger_id': str(ledger.id), 'accrued_rebate': str(ledger.accrued_rebate), 'period': f"{ledger.period_start} — {ledger.period_end}"})
            elif not meets:
                ledger.status = 'cancelled'
                ledger.save(update_fields=['status'])
                EventLog.objects.create(event_type='rebate.threshold_not_met', action_source='system_rebate_liquidation',
                    payload={'ledger_id': str(ledger.id), 'reason': f"Umbral {program.threshold_type} no alcanzado"})
```

### S23-07b · approve_rebate_liquidation() — FIX M3-R2

```python
def approve_rebate_liquidation(ledger_id, liquidation_type, user):
    """
    CEO aprueba liquidación: pending_review → liquidated.
    Valida status y tipo, setea liquidated_at/by, genera EventLog.
    No genera ConfigChangeLog (esto es operación, no cambio de configuración).
    """
    with transaction.atomic():
        ledger = RebateLedger.objects.select_for_update().get(id=ledger_id)
        if ledger.status != 'pending_review':
            raise ValueError(f"Ledger {ledger_id} status es '{ledger.status}', esperado 'pending_review'")
        if liquidation_type not in ('credit', 'payment'):
            raise ValueError(f"liquidation_type inválido: {liquidation_type}")
        
        ledger.status = 'liquidated'
        ledger.liquidation_type = liquidation_type
        ledger.liquidated_at = timezone.now()
        ledger.liquidated_by = user
        ledger.save(update_fields=['status', 'liquidation_type', 'liquidated_at', 'liquidated_by'])
        
        EventLog.objects.create(
            event_type='rebate.liquidated', action_source='approve_rebate_liquidation',
            user=user,
            payload={'ledger_id': str(ledger.id), 'liquidation_type': liquidation_type,
                     'accrued_rebate': str(ledger.accrued_rebate),
                     'period': f"{ledger.period_start} — {ledger.period_end}"})
    return ledger
```

### S23-08 · resolve_commission() — FIX B4 soporta gross_margin

```python
def resolve_commission(brand_id, client_id, subsidiary_id, product_key, sale_price, quantity, cost_price=None):
    result = resolve_commission_rule(brand_id=brand_id, client_id=client_id, subsidiary_id=subsidiary_id, product_key=product_key)
    if result['rule'] is None:
        return {'commission_amount': Decimal('0'), 'commission_per_unit': Decimal('0'), 'rule_level': 'none', 'source': 'no_rule'}
    rule = result['rule']
    if rule.commission_type == 'percentage':
        # FIX M1-R3: no asumir sale_price si commission_base es NULL
        if rule.commission_base is None:
            raise ValueError(f"commission_base es NULL para regla porcentual. Rule {rule.id}. Resolver DEC-S23-03 antes de usar.")
        if rule.commission_base == 'gross_margin':
            if cost_price is None:
                raise ValueError(f"commission_base='gross_margin' requiere cost_price. Rule {rule.id}")
            base = sale_price - cost_price
        else:
            base = sale_price
        per_unit = base * rule.commission_value
    else:
        per_unit = rule.commission_value
    return {'commission_amount': per_unit * quantity, 'commission_per_unit': per_unit, 'rule_level': result['level'], 'source': f"commission_rule_{rule.id}", 'commission_base': rule.commission_base}
```

### S23-09 · seed_artifact_policy — FIX m1 JSON real

```python
class Command(BaseCommand):
    def handle(self, *args, **options):
        from apps.expedientes.artifact_policy import ARTIFACT_POLICY
        existing = set(BrandArtifactPolicyVersion.objects.filter(is_active=True).values_list('brand_id', flat=True))
        seeded = 0
        for brand in Brand.objects.exclude(id__in=existing):
            with transaction.atomic():
                v = BrandArtifactPolicyVersion.objects.create(brand=brand, version=1, artifact_policy=ARTIFACT_POLICY,
                    is_active=True, created_by=None, change_reason='S23-09: seed desde constante Python')
                ConfigChangeLog.objects.create(model_name='BrandArtifactPolicyVersion', record_id=str(v.id),
                    field_name='artifact_policy', old_value=None, new_value=json.dumps(ARTIFACT_POLICY),
                    changed_by=None, change_reason='S23-09: seed desde constante Python')
                seeded += 1
        self.stdout.write(self.style.SUCCESS(f"Seeded {seeded}, skipped {len(existing)}"))
```

---

## Fase 2 — Endpoints y serializers — FIX M3

### S23-10 · API Rebates

```
POST   /api/v1/commercial/rebate-programs/           — permission: IsCEOOrInternalAgent
GET    /api/v1/commercial/rebate-programs/            — permission: IsCEOOrInternalAgent
PATCH  /api/v1/commercial/rebate-programs/{id}/       — permission: IsCEOOrInternalAgent
POST   /api/v1/commercial/rebate-assignments/         — permission: IsCEOOrInternalAgent
GET    /api/v1/commercial/rebate-ledger/              — permission: IsCEOOrInternalAgent, queryset scoped por brand asignado
POST   /api/v1/commercial/rebate-ledger/{id}/approve/ — permission: IsCEO
GET    /api/v1/portal/rebate-progress/                — permission: IsClientUser, scoped por subsidiary
```

Serializers: RebateProgramInternalSerializer (fields all), RebateLedgerInternalSerializer (fields all + entries_count).

```python
class RebateProgressPortalSerializer(serializers.Serializer):
    """FIX M2: soporta threshold_type"""
    program_name = serializers.CharField()
    period = serializers.CharField()
    threshold_type = serializers.CharField()
    progress_percentage = serializers.FloatField()  # min(qualifying/effective_threshold*100, 100) o 100 si none
    threshold_met = serializers.BooleanField()
    # NO expone: rebate_value, accrued_rebate, threshold values, liquidation_type
```

### S23-11 · API Comisiones (CEO-ONLY)

```
POST/GET/PATCH/DELETE /api/v1/commercial/commission-rules/ — permission: IsCEO (explícito, no is_staff)
```

### S23-12 · API ArtifactPolicy (INTERNAL)

```
GET    /api/v1/commercial/artifact-policy/{brand_id}/         — ver versión activa
PATCH  /api/v1/commercial/artifact-policy/{brand_id}/         — crear nueva versión (append-only)
GET    /api/v1/commercial/artifact-policy/{brand_id}/history/ — historial
POST   /api/v1/commercial/artifact-policy/{brand_id}/preview/ — preview transition+mode
```

---

## Fase 3 — Frontend

### S23-13 · Brand Console — Tab "Reglas Comerciales"
- Sección Rebates: CRUD programas. Lista con filtros.
- Sección Comisiones: solo CEO. Tabla brand × product_key × %.
- Sección ArtifactPolicy: viewer versión activa + historial. PATCH crea nueva versión (modal con change_reason). Botón seed.

### S23-14 · Client Console — Tab "Incentivos"
- Progreso rebates: barra % por período. Soporta threshold_type (amount/units/none).
- Historial ledgers liquidados.
- NO muestra: valores rebate, comisiones, umbrales, accrued amounts.

### S23-15 · Frontend checks manuales

| # | Check |
|---|-------|
| FC-1 | CEO ve tab Reglas Comerciales con 3 secciones |
| FC-2 | CLIENT_* ve Incentivos con progreso sin montos |
| FC-3 | AGENT_* NO ve comisiones ni rebate values |
| FC-4 | CEO aprueba liquidación → liquidated |
| FC-5 | ArtifactPolicy PATCH crea nueva versión (no muta) |
| FC-6 | Override subsidiary no afecta otras subsidiaries |
| FC-7 | CLIENT_* subsidiary A no ve datos subsidiary B (403) |

---

## Fase 4 — Tests (56 estimados)

| Grupo | # | Detalle |
|-------|---|---------|
| T1 · RebateProgram CRUD | 4 | Crear, editar, desactivar, scope productos |
| T2 · RebateProgram constraints | 6 | threshold_type=amount sin valor→error, units sin valor→error, none con valor→error, FIX M3-R4: amount con units poblado→error, units con amount poblado→error, valid_to < valid_from→error |
| T3 · RebateAssignment herencia | 6 | Hereda, override, one_level_only, inactivo no aplica |
| T4 · RebateAssignment constraints | 3 | Duplicado activo→IntegrityError, desactivar+crear→OK |
| T5 · calculate_rebate_accrual | 9 | Accrual correcto, idempotencia DB, scope, umbral, múltiples, quarterly/annual, concurrencia, FIX M2-R4: percentage+invoiced calcula sobre unit_price, percentage+list_price calcula sobre base_list_price |
| T6 · liquidate_rebates | 5 | pending_review, cancelled amount, cancelled units, none→pending, EventLog |
| T7 · approve_rebate_liquidation | 3 | FIX M3-R2: pending→liquidated OK, wrong status→ValueError, invalid type→ValueError |
| T8 · CommissionRule constraints | 4 | one_level_only, 6 scope constraints (brand default dup, client dup, subsidiary dup, product-specific dup) |
| T9 · resolve_commission_rule | 5 | Brand default, client, subsidiary, product-specific, sin regla |
| T10 · resolve_commission | 5 | % sale_price, % gross_margin, fixed, ValueError sin cost, FIX M1-R3: ValueError si commission_base NULL |
| T11 · BrandArtifactPolicyVersion | 6 | Crear, update desactiva-antes-de-crear, UniqueConstraint activa, (brand,version) unique, MultipleObjectsReturned→EventLog, seed idempotente |
| T12 · Serializer security | 4 | Portal no ve rebate_value, no ve accrued, commission 403, policy no filtra |
| T13 · Access control | 4 | Cross-subsidiary 403, agent scoped, CEO todo, portal scoped |
| T14 · EventLog | 2 | rebate.pending_review, rebate.liquidated con action_source |

### action_source nuevos
system_rebate_liquidation, approve_rebate_liquidation, create_rebate_program, create_commission_rule, update_artifact_policy, seed_artifact_policy, system_resolve_artifact_policy

### event_type nuevos
rebate.pending_review, rebate.threshold_not_met, rebate.liquidated, commission.rule_created, artifact_policy.updated, artifact_policy.seeded, artifact_policy.integrity_error

---

## Notas de auditoría

1. **Resolvers específicos (FIX B3).** resolve_rebate_assignment() y resolve_commission_rule() con lógica propia. Sin abstracción genérica.
2. **ArtifactPolicy append-only (FIX B1+B1-R2).** BrandArtifactPolicyVersion separada. UniqueConstraint activa + (brand,version). PATCH desactiva current ANTES de crear nueva — sin colisión con constraint.
3. **Idempotencia via DB (FIX M1).** transaction.atomic + select_for_update + IntegrityError catch. Totales recalculados desde entries.
4. **CommissionRule CEO-ONLY, no-temporal MVP (FIX B1-R3).** permission_classes=[IsCEO]. 6 constraints separadas por scope. Sin valid_from/to — una regla activa por scope. Temporalidad real en v2. Historial via ConfigChangeLog.
5. **Liquidación requiere aprobación CEO.** Celery solo pending_review. approve_rebate_liquidation() solo genera EventLog, no ConfigChangeLog (operación, no config — FIX M3-R3).
6. **Effective threshold (FIX M2).** assignment custom > program default. threshold_type con 6 CheckConstraints de consistencia total (FIX M2-R3: cross-field exclusion).
7. **ConfigChangeLog con JSON real (FIX m1).** old_value/new_value = json.dumps(policy).
8. **DEC-S23-03 soporta ambas opciones (FIX B4).** commission_base enum. resolve_commission() lanza ValueError si NULL en regla porcentual — no asume sale_price silenciosamente (FIX M1-R3).
9. **Constraints determinísticas.** UniqueConstraints condicionales por scope en CommissionRule (6 constraints). order_by explícito en resolvers.
10. **Multitenancy operativizada (FIX M3).** Permission classes, scoping subsidiary, tests 403.
11. **Integrity alerts (FIX m1-R2).** MultipleObjectsReturned en resolve_artifact_policy emite EventLog artifact_policy.integrity_error.
12. **Excepción MVP al versionado inmutable (FIX M1-R4).** RebateProgram y CommissionRule se editan PATCH in-place con ConfigChangeLog audit trail, no append-only. Declarado explícitamente como excepción aprobada. Migración a append-only diferida a v2 junto con temporalidad en CommissionRule.

---

## Gate Sprint 23

- [ ] Rebate accrual concurrency-safe al cierre de proforma
- [ ] Liquidación trimestral con effective threshold → pending_review
- [ ] CEO aprueba → liquidated
- [ ] Override subsidiary no afecta otras subsidiaries
- [ ] Constraints previenen duplicados activos (DB-level)
- [ ] Comisión soporta sale_price Y gross_margin
- [ ] ArtifactPolicy append-only con fallback constante
- [ ] Herencia brand>client>subsidiary en rebates Y comisiones
- [ ] Portal no expone valores sensibles
- [ ] Portal scoped por subsidiary (403 cross-access)
- [ ] Tests verdes (56+)
- [ ] Seed idempotente

---

## Archivos backend

| Archivo | Acción |
|---------|--------|
| backend/apps/commercial/__init__.py | NUEVO |
| backend/apps/commercial/models.py | NUEVO — 7 modelos |
| backend/apps/commercial/services/rebates.py | NUEVO — resolver + accrual |
| backend/apps/commercial/services/commissions.py | NUEVO — resolver + commission calc |
| backend/apps/commercial/services/artifact_policy.py | NUEVO — resolve + update |
| backend/apps/commercial/tasks.py | NUEVO — liquidate_rebates |
| backend/apps/commercial/serializers.py | NUEVO — Internal + Portal |
| backend/apps/commercial/views.py | NUEVO — ViewSets con permissions |
| backend/apps/commercial/permissions.py | NUEVO — IsCEO, IsCEOOrInternalAgent, IsClientUser |
| backend/apps/commercial/urls.py | NUEVO |
| backend/apps/commercial/management/commands/seed_artifact_policy.py | NUEVO |
| backend/apps/commercial/tests/ | NUEVO — 56+ tests |
| backend/apps/expedientes/services/artifact_resolution.py | MODIFICADO |
| backend/apps/commercial/migrations/ | NUEVO |
| backend/config/celery.py | MODIFICADO — schedule |
| backend/config/urls.py | MODIFICADO — include |
