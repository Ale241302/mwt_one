import uuid
from django.db import models
from django.db.models import Q, UniqueConstraint, CheckConstraint
from apps.core.models import TimestampMixin


# ---------------------------------------------------------------------------
# S23-01 — RebateProgram + RebateProgramProduct
# ---------------------------------------------------------------------------

class PeriodType(models.TextChoices):
    MONTHLY = 'monthly', 'Monthly'
    QUARTERLY = 'quarterly', 'Quarterly'
    SEMI_ANNUAL = 'semi_annual', 'Semi-Annual'
    ANNUAL = 'annual', 'Annual'


class RebateType(models.TextChoices):
    PERCENTAGE = 'percentage', 'Percentage'
    FIXED_AMOUNT = 'fixed_amount', 'Fixed Amount'


class ThresholdType(models.TextChoices):
    AMOUNT = 'amount', 'Amount'
    UNITS = 'units', 'Units'
    NONE = 'none', 'None'


class CalculationBase(models.TextChoices):
    INVOICED = 'invoiced', 'Invoiced Price'
    LIST_PRICE = 'list_price', 'List Price'


class RebateProgram(TimestampMixin):
    """
    S23-01: Programa de rebate por volumen para una marca.
    Las decisiones DEC-S23-01 (calculation_base) quedan nullable
    hasta que el CEO las resuelva.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    brand = models.ForeignKey(
        'brands.Brand',
        on_delete=models.CASCADE,
        related_name='rebate_programs',
    )
    name = models.CharField(max_length=255)
    period_type = models.CharField(max_length=20, choices=PeriodType.choices)
    valid_from = models.DateField()
    valid_to = models.DateField(null=True, blank=True)
    rebate_type = models.CharField(max_length=20, choices=RebateType.choices)
    rebate_value = models.DecimalField(max_digits=10, decimal_places=4)
    # DEC-S23-01 pendiente — nullable hasta decisión CEO
    calculation_base = models.CharField(
        max_length=20,
        choices=CalculationBase.choices,
        null=True,
        blank=True,
    )
    threshold_type = models.CharField(max_length=10, choices=ThresholdType.choices)
    # Thresholds — solo aplican cuando threshold_type != 'none'
    threshold_amount = models.DecimalField(
        max_digits=14, decimal_places=2, null=True, blank=True,
        help_text='Aplica solo cuando threshold_type=amount',
    )
    threshold_units = models.PositiveIntegerField(
        null=True, blank=True,
        help_text='Aplica solo cuando threshold_type=units',
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'commercial_rebate_program'
        ordering = ['-valid_from']
        constraints = [
            # C1 — valid_to >= valid_from
            CheckConstraint(
                check=Q(valid_to__isnull=True) | Q(valid_to__gte=models.F('valid_from')),
                name='rebate_program_valid_to_gte_valid_from',
            ),
            # C2 — threshold_amount solo si threshold_type=amount
            CheckConstraint(
                check=(
                    Q(threshold_type='amount', threshold_amount__isnull=False) |
                    Q(threshold_type='amount', threshold_amount__isnull=True) |
                    Q(threshold_type__in=['units', 'none'], threshold_amount__isnull=True)
                ),
                name='rebate_program_amount_only_when_type_amount',
            ),
            # C3 — threshold_units solo si threshold_type=units
            CheckConstraint(
                check=(
                    Q(threshold_type='units', threshold_units__isnull=False) |
                    Q(threshold_type='units', threshold_units__isnull=True) |
                    Q(threshold_type__in=['amount', 'none'], threshold_units__isnull=True)
                ),
                name='rebate_program_units_only_when_type_units',
            ),
            # C4 — threshold_none implica ambos threshold null
            CheckConstraint(
                check=(
                    ~Q(threshold_type='none') |
                    Q(threshold_type='none', threshold_amount__isnull=True, threshold_units__isnull=True)
                ),
                name='rebate_program_none_no_thresholds',
            ),
            # C5 — si threshold_type=amount, threshold_units debe ser null
            CheckConstraint(
                check=(
                    ~Q(threshold_type='amount') |
                    Q(threshold_type='amount', threshold_units__isnull=True)
                ),
                name='rebate_program_amount_excludes_units',
            ),
            # C6 — si threshold_type=units, threshold_amount debe ser null
            CheckConstraint(
                check=(
                    ~Q(threshold_type='units') |
                    Q(threshold_type='units', threshold_amount__isnull=True)
                ),
                name='rebate_program_units_excludes_amount',
            ),
            # C7 — rebate_value > 0
            CheckConstraint(
                check=Q(rebate_value__gt=0),
                name='rebate_program_value_positive',
            ),
        ]

    def __str__(self):
        return f"{self.brand_id} — {self.name} ({self.period_type})"


class RebateProgramProduct(TimestampMixin):
    """
    S23-01: Productos incluidos en un programa de rebate.
    Si no hay filas, el programa aplica a todos los productos de la marca.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    rebate_program = models.ForeignKey(
        RebateProgram,
        on_delete=models.CASCADE,
        related_name='product_inclusions',
    )
    product_key = models.CharField(max_length=50)

    class Meta:
        db_table = 'commercial_rebate_program_product'
        unique_together = [['rebate_program', 'product_key']]

    def __str__(self):
        return f"{self.rebate_program_id} / {self.product_key}"


# ---------------------------------------------------------------------------
# S23-02 — RebateAssignment + RebateLedger + RebateAccrualEntry
# ---------------------------------------------------------------------------

class RebateAssignment(TimestampMixin):
    """
    S23-02: Asigna un programa de rebate a un cliente o subsidiary (exclusivo).
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    rebate_program = models.ForeignKey(
        RebateProgram,
        on_delete=models.CASCADE,
        related_name='assignments',
    )
    # Exactamente uno de los dos debe tener valor (CheckConstraint one_level_only)
    client = models.ForeignKey(
        'clientes.Cliente',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='rebate_assignments',
    )
    subsidiary = models.ForeignKey(
        'clientes.ClientSubsidiary',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='rebate_assignments',
    )
    # Threshold override por asignación (si es None, usa el del programa)
    custom_threshold_amount = models.DecimalField(
        max_digits=14, decimal_places=2, null=True, blank=True,
    )
    custom_threshold_units = models.PositiveIntegerField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'commercial_rebate_assignment'
        constraints = [
            # C1 — XOR: exactamente uno de client / subsidiary
            CheckConstraint(
                check=(
                    Q(client__isnull=False, subsidiary__isnull=True) |
                    Q(client__isnull=True, subsidiary__isnull=False)
                ),
                name='rebate_assignment_one_level_only',
            ),
            # C2 — UniqueConstraint condicional: solo un assignment activo por program×client
            UniqueConstraint(
                fields=['rebate_program', 'client'],
                condition=Q(is_active=True, client__isnull=False),
                name='rebate_assignment_unique_active_program_client',
            ),
            # C3 — UniqueConstraint condicional: solo un assignment activo por program×subsidiary
            UniqueConstraint(
                fields=['rebate_program', 'subsidiary'],
                condition=Q(is_active=True, subsidiary__isnull=False),
                name='rebate_assignment_unique_active_program_subsidiary',
            ),
        ]

    def __str__(self):
        target = self.client or self.subsidiary
        return f"{self.rebate_program_id} → {target}"


class LedgerStatus(models.TextChoices):
    ACCRUING = 'accruing', 'Accruing'
    PENDING_REVIEW = 'pending_review', 'Pending Review'
    LIQUIDATED = 'liquidated', 'Liquidated'
    CANCELLED = 'cancelled', 'Cancelled'


class LiquidationType(models.TextChoices):
    CREDIT_NOTE = 'credit_note', 'Credit Note'
    BANK_TRANSFER = 'bank_transfer', 'Bank Transfer'
    PRODUCT_CREDIT = 'product_credit', 'Product Credit'


class RebateLedger(TimestampMixin):
    """
    S23-02: Libro contable de accrual para un período de rebate.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    rebate_assignment = models.ForeignKey(
        RebateAssignment,
        on_delete=models.CASCADE,
        related_name='ledgers',
    )
    period_start = models.DateField()
    period_end = models.DateField()
    status = models.CharField(
        max_length=20,
        choices=LedgerStatus.choices,
        default=LedgerStatus.ACCRUING,
    )
    accrued_amount = models.DecimalField(
        max_digits=14, decimal_places=4, default=0,
    )
    qualifying_amount = models.DecimalField(
        max_digits=14, decimal_places=4, default=0,
    )
    qualifying_units = models.PositiveIntegerField(default=0)
    threshold_met = models.BooleanField(default=False)
    # DEC-S23-02 pendiente — nullable hasta decisión CEO
    liquidation_type = models.CharField(
        max_length=20,
        choices=LiquidationType.choices,
        null=True,
        blank=True,
    )
    liquidated_at = models.DateTimeField(null=True, blank=True)
    liquidated_by = models.ForeignKey(
        'users.MWTUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='liquidated_ledgers',
    )

    class Meta:
        db_table = 'commercial_rebate_ledger'
        unique_together = [['rebate_assignment', 'period_start', 'period_end']]
        ordering = ['-period_start']

    def __str__(self):
        return f"Ledger {self.rebate_assignment_id} {self.period_start}→{self.period_end} [{self.status}]"


class RebateAccrualEntry(TimestampMixin):
    """
    S23-02: Entrada individual de accrual ligada a una proforma.
    unique_together garantiza idempotencia al procesar la misma proforma dos veces.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    ledger = models.ForeignKey(
        RebateLedger,
        on_delete=models.CASCADE,
        related_name='accrual_entries',
    )
    # FK a proforma — usamos CharField para no acoplar a la app expedientes aquí;
    # la FK real se puede añadir con una migración posterior si se desea.
    proforma_id = models.CharField(max_length=100)
    qualifying_amount = models.DecimalField(max_digits=14, decimal_places=4)
    qualifying_units = models.PositiveIntegerField(default=0)
    accrued_amount = models.DecimalField(max_digits=14, decimal_places=4)
    proforma_date = models.DateField()

    class Meta:
        db_table = 'commercial_rebate_accrual_entry'
        unique_together = [['ledger', 'proforma_id']]
        ordering = ['-proforma_date']

    def __str__(self):
        return f"Entry ledger={self.ledger_id} proforma={self.proforma_id}"


# ---------------------------------------------------------------------------
# S23-03 — CommissionRule
# ---------------------------------------------------------------------------

class CommissionRuleType(models.TextChoices):
    PERCENTAGE = 'percentage', 'Percentage'
    FIXED_AMOUNT = 'fixed_amount', 'Fixed Amount'


class CommissionBase(models.TextChoices):
    SALE_PRICE = 'sale_price', 'Sale Price'
    GROSS_MARGIN = 'gross_margin', 'Gross Margin'


class CommissionRule(TimestampMixin):
    """
    S23-03: Regla de comisión para agentes MWT.
    Scope exclusivo: brand / client / subsidiary.
    Sin valid_from/valid_to — no temporal en MVP.
    DEC-S23-03: commission_base nullable hasta decisión CEO.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    # Scope — exactamente uno (CheckConstraint one_level_only)
    brand = models.ForeignKey(
        'brands.Brand',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='commission_rules',
    )
    client = models.ForeignKey(
        'clientes.Cliente',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='commission_rules',
    )
    subsidiary = models.ForeignKey(
        'clientes.ClientSubsidiary',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='commission_rules',
    )
    # product_key nullable = regla default para todo el scope
    product_key = models.CharField(max_length=50, null=True, blank=True)
    rule_type = models.CharField(max_length=20, choices=CommissionRuleType.choices)
    rule_value = models.DecimalField(max_digits=10, decimal_places=4)
    # DEC-S23-03 pendiente — nullable hasta decisión CEO
    commission_base = models.CharField(
        max_length=20,
        choices=CommissionBase.choices,
        null=True,
        blank=True,
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'commercial_commission_rule'
        constraints = [
            # C1 — exactamente uno de brand/client/subsidiary
            CheckConstraint(
                check=(
                    Q(brand__isnull=False, client__isnull=True, subsidiary__isnull=True) |
                    Q(brand__isnull=True, client__isnull=False, subsidiary__isnull=True) |
                    Q(brand__isnull=True, client__isnull=True, subsidiary__isnull=False)
                ),
                name='commission_rule_one_level_only',
            ),
            # C2 — rule_value > 0
            CheckConstraint(
                check=Q(rule_value__gt=0),
                name='commission_rule_value_positive',
            ),
            # ---------------------------------------------------------------
            # 6 UniqueConstraints separadas por scope
            # (PG NULLs no previenen duplicados con una sola constraint genérica)
            # ---------------------------------------------------------------
            # UC1 — brand default (sin product_key)
            UniqueConstraint(
                fields=['brand'],
                condition=Q(is_active=True, brand__isnull=False, product_key__isnull=True),
                name='commission_rule_unique_active_brand_default',
            ),
            # UC2 — brand + product
            UniqueConstraint(
                fields=['brand', 'product_key'],
                condition=Q(is_active=True, brand__isnull=False, product_key__isnull=False),
                name='commission_rule_unique_active_brand_product',
            ),
            # UC3 — client default (sin product_key)
            UniqueConstraint(
                fields=['client'],
                condition=Q(is_active=True, client__isnull=False, product_key__isnull=True),
                name='commission_rule_unique_active_client_default',
            ),
            # UC4 — client + product
            UniqueConstraint(
                fields=['client', 'product_key'],
                condition=Q(is_active=True, client__isnull=False, product_key__isnull=False),
                name='commission_rule_unique_active_client_product',
            ),
            # UC5 — subsidiary default (sin product_key)
            UniqueConstraint(
                fields=['subsidiary'],
                condition=Q(is_active=True, subsidiary__isnull=False, product_key__isnull=True),
                name='commission_rule_unique_active_subsidiary_default',
            ),
            # UC6 — subsidiary + product
            UniqueConstraint(
                fields=['subsidiary', 'product_key'],
                condition=Q(is_active=True, subsidiary__isnull=False, product_key__isnull=False),
                name='commission_rule_unique_active_subsidiary_product',
            ),
        ]

    def __str__(self):
        scope = self.brand or self.client or self.subsidiary
        product_part = f" / {self.product_key}" if self.product_key else " (default)"
        return f"CommissionRule {scope}{product_part} [{self.rule_type}]"


# ---------------------------------------------------------------------------
# S23-04 — BrandArtifactPolicyVersion
# ---------------------------------------------------------------------------

class BrandArtifactPolicyVersion(TimestampMixin):
    """
    S23-04: Versión append-only de la política de artefactos por marca.
    Migra ARTIFACT_POLICY de constante Python a tabla versionada.
    Regla: NO editar in-place — cada cambio crea una nueva versión.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    brand = models.ForeignKey(
        'brands.Brand',
        on_delete=models.CASCADE,
        related_name='artifact_policy_versions',
    )
    version = models.PositiveIntegerField()
    artifact_policy = models.JSONField(
        help_text='Snapshot completo de la política de artefactos para esta versión.',
    )
    is_active = models.BooleanField(default=False)
    superseded_by = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='supersedes',
        help_text='Versión que reemplazó a esta.',
    )
    notes = models.TextField(
        blank=True,
        help_text='Notas opcionales sobre el cambio realizado en esta versión.',
    )

    class Meta:
        db_table = 'commercial_brand_artifact_policy_version'
        ordering = ['-version']
        constraints = [
            # UC1 — solo una versión activa por brand
            UniqueConstraint(
                fields=['brand'],
                condition=Q(is_active=True),
                name='artifact_policy_unique_active_per_brand',
            ),
            # UC2 — unicidad de version por brand
            UniqueConstraint(
                fields=['brand', 'version'],
                name='artifact_policy_unique_version_per_brand',
            ),
        ]

    def __str__(self):
        return f"{self.brand_id} ArtifactPolicy v{self.version} [active={self.is_active}]"
