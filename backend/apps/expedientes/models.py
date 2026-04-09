import uuid
from django.conf import settings
from django.db import models
from django.core.exceptions import ValidationError


from apps.core.models import TimestampMixin, AppendOnlyModel, LegalEntity
from .enums_artifacts import ArtifactStatusEnum
from .enums_exp import (
    ExpedienteStatus, BlockedByType, DispatchMode, PaymentStatus,
    CreditClockStartRule, AggregateType,
    RegisteredByType, CostLineVisibility, LogisticsMode, LogisticsSource,
    CostCategory, CostBehavior, AforoType,
)



class Expediente(TimestampMixin):
    expediente_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    legal_entity = models.ForeignKey(LegalEntity, on_delete=models.PROTECT, related_name='expedientes_emitidos', help_text='Entidad emisora')
    brand = models.ForeignKey('brands.Brand', on_delete=models.PROTECT, null=True, blank=True, db_index=True)
    destination = models.CharField(max_length=10, choices=[('CR', 'Costa Rica'), ('USA', 'United States')], default='CR')
    client = models.ForeignKey(LegalEntity, on_delete=models.PROTECT, related_name='expedientes_como_cliente', help_text='Cliente', db_index=True)
    status = models.CharField(max_length=20, choices=ExpedienteStatus.choices, default=ExpedienteStatus.REGISTRO, db_index=True)
    is_blocked = models.BooleanField(default=False)
    blocked_reason = models.TextField(blank=True, null=True)
    blocked_at = models.DateTimeField(blank=True, null=True)
    blocked_by_type = models.CharField(max_length=10, choices=BlockedByType.choices, blank=True, null=True)
    blocked_by_id = models.CharField(max_length=255, blank=True, null=True, help_text='user_id if CEO, rule_name if SYSTEM')
    mode = models.CharField(max_length=50, blank=True, help_text='Modalidad operativa')
    freight_mode = models.CharField(max_length=50, blank=True)
    transport_mode = models.CharField(max_length=50, blank=True)
    dispatch_mode = models.CharField(max_length=10, choices=DispatchMode.choices, default=DispatchMode.MWT)
    price_basis = models.CharField(max_length=50, blank=True)
    credit_clock_start_rule = models.CharField(max_length=20, choices=CreditClockStartRule.choices, default=CreditClockStartRule.ON_CREATION)
    credit_clock_started_at = models.DateTimeField(blank=True, null=True, help_text='Timestamp when credit clock started (FIX-7)')
    payment_status = models.CharField(max_length=10, choices=PaymentStatus.choices, default=PaymentStatus.PENDING)
    payment_registered_at = models.DateTimeField(blank=True, null=True)
    payment_registered_by_type = models.CharField(max_length=10, choices=BlockedByType.choices, blank=True, null=True)
    payment_registered_by_id = models.CharField(max_length=255, blank=True, null=True)
    nodo_destino = models.ForeignKey(
        'transfers.Node',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='expedientes_destino',
        help_text='Target node (triggers transfer suggestion on close)'
    )
    external_fiscal_refs = models.JSONField(
        default=list, blank=True,
        help_text='DANFE, DU-E, etc. (H5)'
    )
    aforo_type = models.CharField(
        max_length=10, choices=AforoType.choices,
        blank=True, null=True, help_text='H9'
    )
    aforo_date = models.DateField(blank=True, null=True, help_text='H9')
    snapshot_commercial = models.JSONField(
        default=dict, blank=True,
        help_text='Immutable snapshot of pricing, incoterms, payment terms, and agreements (S14-05)'
    )

    # S16: Credit Management
    credit_blocked = models.BooleanField(
        default=False,
        help_text="Flag indicating if the expediente is currently blocked due to credit clock"
    )
    credit_warning = models.BooleanField(
        default=False,
        help_text="Warning flag for credit threshold"
    )

    # Reopen tracking (Sprint 16)
    reopen_count = models.PositiveIntegerField(default=0, help_text="Number of times reopened")
    reopened_at = models.DateTimeField(blank=True, null=True)
    reopen_justification = models.TextField(blank=True, null=True)

    # === S17-08: GENERALES ===
    purchase_order_number = models.CharField(
        max_length=100, null=True, blank=True,
        help_text='Número de orden de compra del cliente'
    )
    operado_por = models.CharField(
        max_length=20,
        choices=[('CLIENTE', 'Cliente'), ('MWT', 'Muito Work Limitada')],
        null=True, blank=True,
        help_text='Quién opera logísticamente este expediente'
    )
    url_orden_compra = models.URLField(
        max_length=500, null=True, blank=True,
        help_text='URL del documento de orden de compra'
    )

    # === S17-08: REGISTRO ===
    ref_number = models.CharField(
        max_length=100, null=True, blank=True,
        help_text='Número de referencia interna del expediente'
    )
    credit_days_client = models.IntegerField(
        null=True, blank=True,
        help_text='Días de crédito acordados con el cliente'
    )
    credit_days_mwt = models.IntegerField(
        null=True, blank=True,
        help_text='Días de crédito acordados con MWT'
    )
    credit_limit_client = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True,
        help_text='Snapshot del límite de crédito del cliente (DEC-EXP-03) al momento de creación'
    )
    credit_limit_mwt = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True,
        help_text='Snapshot del límite de crédito MWT (DEC-EXP-03) al momento de creación'
    )
    order_value = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True,
        help_text='Valor total del pedido en moneda del expediente'
    )

    # === S17-08: PRODUCCION ===
    factory_order_number = models.CharField(
        max_length=100, null=True, blank=True,
        help_text='Número de orden en sistema del fabricante (DEC-EXP-01). Campo flat para queries rápidos; detalle en FactoryOrder.'
    )
    proforma_client_number = models.CharField(
        max_length=100, null=True, blank=True,
        help_text='Número de proforma emitida al cliente'
    )
    proforma_mwt_number = models.CharField(
        max_length=100, null=True, blank=True,
        help_text='Número de proforma emitida a MWT'
    )
    fabrication_start_date = models.DateField(
        null=True, blank=True,
        help_text='Fecha de inicio de fabricación'
    )
    fabrication_end_date = models.DateField(
        null=True, blank=True,
        help_text='Fecha de fin de fabricación'
    )
    url_proforma_cliente = models.URLField(
        max_length=500, null=True, blank=True,
        help_text='URL del documento de proforma del cliente'
    )
    url_proforma_muito_work = models.URLField(
        max_length=500, null=True, blank=True,
        help_text='URL del documento de proforma MWT'
    )
    master_expediente = models.ForeignKey(
        'self', null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='merged_followers',
        help_text='Expediente master cuando éste fue fusionado (DEC-EXP-02). El merge lo decide el CEO manualmente en Sprint 18.'
    )

    # === S17-08: PREPARACION ===
    shipping_method = models.CharField(
        max_length=100, null=True, blank=True,
        help_text='Método de envío (aéreo, marítimo, terrestre, courier)'
    )
    # === S18-04: Campos aditivos ===
    credit_released = models.BooleanField(
        default=False,
        help_text='True cuando credit_exposure <= 0. SOLO lo setea recalculate_expediente_credit().'
    )
    credit_exposure = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True,
        help_text='Exposure calculado = total_lines - total_pagos_confirmados'
    )
    incoterms = models.CharField(
        max_length=32, null=True, blank=True,
        choices=[('EXW', 'Ex Works'), ('FOB', 'Free On Board'), ('CIF', 'Cost, Insurance and Freight'), ('DDP', 'Delivered Duty Paid')],
        help_text='Incoterm pactado (Sprint 18)'
    )
    cargo_manager = models.CharField(
        max_length=20,
        choices=[('CLIENTE', 'Cliente'), ('FABRICA', 'Fábrica')],
        null=True, blank=True,
        help_text='Quién gestiona la carga y envío'
    )
    shipping_value = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True,
        help_text='Valor del flete de envío'
    )
    payment_mode_shipping = models.CharField(
        max_length=20,
        choices=[('PREPAGO', 'Prepago'), ('CONTRAENTREGA', 'Contraentrega')],
        null=True, blank=True,
        help_text='Modalidad de pago del flete'
    )
    url_list_empaque = models.URLField(
        max_length=500, null=True, blank=True,
        help_text='URL del documento lista de empaque'
    )
    url_cotizacion_envio = models.URLField(
        max_length=500, null=True, blank=True,
        help_text='URL de la cotización de envío'
    )

    # === S17-08: DESPACHO ===
    airline_or_shipping_company = models.CharField(
        max_length=200, null=True, blank=True,
        help_text='Nombre de la aerolínea o naviera utilizada'
    )
    awb_bl_number = models.CharField(
        max_length=100, null=True, blank=True,
        help_text='Número Air Waybill (aéreo) o Bill of Lading (marítimo)'
    )
    origin_location = models.CharField(
        max_length=200, null=True, blank=True,
        help_text='Puerto o aeropuerto de origen del envío'
    )
    arrival_location = models.CharField(
        max_length=200, null=True, blank=True,
        help_text='Puerto o aeropuerto de llegada del envío'
    )
    shipment_date = models.DateField(
        null=True, blank=True,
        help_text='Fecha efectiva de despacho / embarque'
    )
    payment_date_dispatch = models.DateField(
        null=True, blank=True,
        help_text='Fecha en que se realiza el pago en el estado DESPACHO'
    )
    invoice_client_number = models.CharField(
        max_length=100, null=True, blank=True,
        help_text='Número de factura emitida al cliente'
    )
    invoice_mwt_number = models.CharField(
        max_length=100, null=True, blank=True,
        help_text='Número de factura interna MWT'
    )
    dispatch_additional_info = models.TextField(
        null=True, blank=True,
        help_text='Información adicional libre sobre el despacho'
    )
    url_certificado_origen = models.URLField(
        max_length=500, null=True, blank=True,
        help_text='URL del certificado de origen'
    )
    url_factura_cliente = models.URLField(
        max_length=500, null=True, blank=True,
        help_text='URL de la factura del cliente'
    )
    url_factura_muito_work = models.URLField(
        max_length=500, null=True, blank=True,
        help_text='URL de la factura interna MWT'
    )
    url_awb_bl = models.URLField(
        max_length=500, null=True, blank=True,
        help_text='URL del AWB o BL escaneado'
    )
    tracking_url = models.URLField(
        max_length=500, null=True, blank=True,
        help_text='Link clicable de tracking (DHL, FedEx, naviera, etc.)'
    )

    # === S17-08: TRANSITO ===
    intermediate_airport_or_port = models.CharField(
        max_length=200, null=True, blank=True,
        help_text='Aeropuerto o puerto de escala intermedia'
    )
    transit_arrival_date = models.DateField(
        null=True, blank=True,
        help_text='Fecha estimada o real de llegada en tránsito'
    )
    url_packing_list_detallado = models.URLField(
        max_length=500, null=True, blank=True,
        help_text='URL del packing list detallado para aduana'
    )

    # === S21: Custom Artifact Policy — overrides per-expediente ===
    custom_artifact_policy = models.JSONField(
        default=dict,
        blank=True,
        help_text=(
            'S21: Overrides de política de artefactos específicos de este expediente. '
            'Estructura: {"ESTADO": {"add": ["ART-XX"], "remove": ["ART-YY"]}}. '
            'Solo modificable por superusers vía Admin Panel.'
        )
    )

    # === S25-02: Precio diferido + parent/child ===
    deferred_total_price = models.DecimalField(
        max_digits=14, decimal_places=2,
        null=True, blank=True,
        help_text=(
            "Precio diferido del expediente. Uso interno CEO. "
            "Equivale a 'order_full_price_diferido' del sistema viejo. "
            "NULL = no definido. Editable solo por CEO."
        )
    )
    deferred_visible = models.BooleanField(
        default=False,
        help_text=(
            "Si True, el precio diferido es visible en el portal del cliente. "
            "Por default invisible (solo CEO). Toggle manual."
        )
    )
    parent_expediente = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='child_expedientes',
        help_text="Expediente padre (origen de un split). NULL = expediente original."
    )
    is_inverted_child = models.BooleanField(
        default=False,
        help_text=(
            "True si este expediente fue creado por split con inversión: "
            "el 'nuevo' expediente tomó el rol de padre y el 'original' se convirtió en hijo. "
            "Informativo para el CEO — no afecta lógica de negocio."
        )
    )

    class Meta:
        verbose_name = 'Expediente'
        verbose_name_plural = 'Expedientes'
        ordering = ['-created_at']

    def __str__(self):
        return f'EXP-{str(self.expediente_id)[:8]}'


# === S17-09: ExpedienteProductLine ===
class ExpedienteProductLine(models.Model):
    """Line item linking an Expediente to a ProductMaster SKU."""
    expediente = models.ForeignKey(
        Expediente, on_delete=models.CASCADE, related_name='product_lines'
    )
    product = models.ForeignKey(
        'productos.ProductMaster',
        on_delete=models.PROTECT,
        related_name='expediente_lines',
        help_text='SKU from ProductMaster — never free text'
    )
    quantity = models.PositiveIntegerField(
        help_text='Cantidad original pedida'
    )
    unit_price = models.DecimalField(
        max_digits=12, decimal_places=2,
        help_text='Precio unitario editable por expediente. Inicializado desde resolve_client_price() si disponible.'
    )
    price_source = models.CharField(
        max_length=30,
        default='manual',
        choices=[
            ('pricelist', 'Lista de precios activa'),
            ('manual', 'Ingresado manualmente'),
            ('override', 'Override por expediente'),
        ],
        help_text='Origen del precio: lista activa, manual, u override CEO'
    )
    quantity_modified = models.PositiveIntegerField(
        null=True, blank=True,
        help_text='Cantidad modificada post-creación (si aplica)'
    )
    unit_price_modified = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True,
        help_text='Precio modificado post-creación (si aplica)'
    )
    modification_reason = models.CharField(
        max_length=200, null=True, blank=True,
        help_text='Razón del cambio de cantidad o precio'
    )
    separated_to_expediente = models.ForeignKey(
        Expediente,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='received_lines',
        help_text='Expediente destino si esta línea fue separada (split)'
    )
    factory_order = models.ForeignKey(
        'FactoryOrder',
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='product_lines',
        help_text='Orden de fábrica a la que pertenece esta línea'
    )
    # === S18-04: Campos aditivos ===
    brand_sku = models.ForeignKey(
        'brands.BrandSKU', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='expediente_lines',
        help_text="SKU específico con talla. Nullable para backward compat."
    )
    pricelist_used = models.ForeignKey(
        'pricing.PriceList', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='product_lines_snapshot',
        help_text='Snapshot de la lista de precios usada al crear la linea'
    )
    base_price = models.DecimalField(
        max_digits=12, decimal_places=2,
        null=True, blank=True,
        help_text='Snapshot del precio base de la lista de precios'
    )
    proforma = models.ForeignKey(
        'ArtifactInstance',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='proforma_lines',
        limit_choices_to={'artifact_type': 'ART-02'},
        help_text='S20-01: Proforma (ART-02) a la que pertenece esta línea. NULL en líneas legacy pre-S20.'
    )

    @property
    def size_display(self):
        if self.brand_sku and self.brand_sku.size:
            return self.brand_sku.size
        return '—'

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['created_at']
        verbose_name = 'Expediente Product Line'
        verbose_name_plural = 'Expediente Product Lines'

    def __str__(self):
        return f'{self.expediente} — {self.product} x{self.quantity}'


# === S17-10: FactoryOrder ===
class FactoryOrder(models.Model):
    expediente = models.ForeignKey(
        Expediente, on_delete=models.CASCADE, related_name='factory_orders'
    )
    order_number = models.CharField(
        max_length=100,
        help_text='Número en sistema del fabricante'
    )
    proforma_client_number = models.CharField(max_length=100, null=True, blank=True)
    proforma_mwt_number = models.CharField(max_length=100, null=True, blank=True)
    purchase_number = models.CharField(
        max_length=100, null=True, blank=True,
        help_text='Número de orden de compra al fabricante'
    )
    url_proforma_client = models.URLField(max_length=500, null=True, blank=True)
    url_proforma_mwt = models.URLField(max_length=500, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['created_at']
        verbose_name = 'Factory Order'
        verbose_name_plural = 'Factory Orders'

    def save(self, *args, **kwargs):
        is_new = self._state.adding
        super().save(*args, **kwargs)
        if is_new and not self.expediente.factory_order_number:
            self.expediente.factory_order_number = self.order_number
            self.expediente.save(update_fields=['factory_order_number'])

    def __str__(self):
        return f'FO-{self.order_number} → {self.expediente}'


# === S17-11: ExpedientePago ===
class ExpedientePago(models.Model):
    expediente = models.ForeignKey(
        Expediente, on_delete=models.CASCADE, related_name='pagos'
    )
    tipo_pago = models.CharField(
        max_length=20,
        choices=[('COMPLETO', 'Pago Completo'), ('PARCIAL', 'Pago Parcial')],
    )
    metodo_pago = models.CharField(
        max_length=30,
        choices=[
            ('TRANSFERENCIA', 'Transferencia Bancaria'),
            ('NOTA_CREDITO', 'Nota de Crédito'),
        ],
    )
    payment_date = models.DateField()
    amount_paid = models.DecimalField(max_digits=12, decimal_places=2)
    additional_info = models.TextField(null=True, blank=True)
    url_comprobante = models.URLField(max_length=500, null=True, blank=True)
    credit_status = models.CharField(
        max_length=20, null=True, blank=True,
        choices=[
            ('PENDING', 'Pending'),
            ('CONFIRMED', 'Confirmed'),
            ('REJECTED', 'Rejected'),
        ],
        default='PENDING',
    )

    # === S25-01: Payment Status Machine ===
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pendiente verificación'),
        ('verified', 'Verificado'),
        ('credit_released', 'Crédito liberado'),
        ('rejected', 'Rechazado'),
    ]
    payment_status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default='pending',
        help_text=(
            "Estado del pago dentro de su ciclo de vida. "
            "pending → verificado por CEO → crédito liberado. "
            "Pagos legacy (pre-S25) migrados según regla C2."
        )
    )
    verified_at = models.DateTimeField(
        null=True, blank=True,
        help_text="Timestamp de verificación por CEO."
    )
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='verified_payments',
        help_text="Usuario que verificó el pago."
    )
    credit_released_at = models.DateTimeField(
        null=True, blank=True,
        help_text="Timestamp de liberación de crédito."
    )
    credit_released_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='released_payments',
        help_text="Usuario que liberó el crédito."
    )
    rejection_reason = models.TextField(
        blank=True, default='',
        help_text="Motivo de rechazo si payment_status='rejected'."
    )

    # S26-02b: FK proforma — para resolve_collection_recipient()
    proforma = models.ForeignKey(
        'ArtifactInstance',
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='payments',
        limit_choices_to={'artifact_type': 'ART-02'},
        help_text='S26-02b: Proforma (ART-02) del pago. Null para pagos legacy pre-S26.'
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-payment_date']
        verbose_name = 'Expediente Pago'
        verbose_name_plural = 'Expediente Pagos'

    def __str__(self):
        return f'Pago {self.tipo_pago} {self.amount_paid} — {self.expediente}'


class ArtifactInstance(TimestampMixin):
    artifact_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    expediente = models.ForeignKey(Expediente, on_delete=models.CASCADE, related_name='artifacts')
    artifact_type = models.CharField(max_length=20, help_text='ART-01 to ART-19')
    status = models.CharField(max_length=20, choices=ArtifactStatusEnum.choices(), default=ArtifactStatusEnum.DRAFT)
    payload = models.JSONField(default=dict)
    supersedes = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        blank=True, null=True,
        related_name='superseded_by_set',
    )
    superseded_by = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        blank=True, null=True,
        related_name='supersedes_set',
    )
    parent_proforma = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='child_artifacts',
        limit_choices_to={'artifact_type': 'ART-02'},
        help_text='S20-02 HR-11: Proforma (ART-02) a la que pertenece este artefacto.'
    )

    class Meta:
        verbose_name = 'Artifact Instance'
        verbose_name_plural = 'Artifact Instances'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.artifact_type} – {self.get_status_display()}'


# === S21-01: EventLog extendido con 5 campos nuevos ===
class EventLog(models.Model):
    event_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event_type = models.CharField(max_length=100, help_text='e.g. "expediente.state_changed"')
    aggregate_type = models.CharField(max_length=20, choices=AggregateType.choices)
    aggregate_id = models.UUIDField()
    payload = models.JSONField(default=dict)
    occurred_at = models.DateTimeField()
    emitted_by = models.CharField(max_length=100, help_text='e.g. "C5:RegisterSAPConfirmation"')
    processed_at = models.DateTimeField(blank=True, null=True, help_text='null until dispatcher consumes')
    retry_count = models.IntegerField(default=0)
    correlation_id = models.UUIDField()
    # === S18-04: Campos aditivos ===
    previous_status = models.CharField(max_length=30, null=True, blank=True)
    new_status = models.CharField(max_length=30, null=True, blank=True)

    # === S21-01: 5 campos nuevos — todos null=True (backward compat absoluto) ===
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='event_logs',
        help_text='S21: Usuario que disparó el evento. NULL para eventos de sistema/Celery.'
    )
    proforma = models.ForeignKey(
        'ArtifactInstance',
        null=True, blank=True,
        on_delete=models.SET_NULL,
        limit_choices_to={'artifact_type': 'ART-02'},
        related_name='event_logs_proforma',
        help_text='S21: Proforma (ART-02) relacionada con el evento. NULL si no aplica.'
    )
    expediente = models.ForeignKey(
        'Expediente',
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='event_logs',
        help_text='S21: Expediente relacionado con el evento.'
    )
    action_source = models.CharField(
        max_length=32, null=True, blank=True,
        help_text='S21: Origen del comando. Contrato cerrado: C1..C22, create_proforma, reassign_line, change_mode, patch_{estado}, system_*.'
    )

    class Meta:
        verbose_name = 'Event Log'
        verbose_name_plural = 'Event Logs'
        ordering = ['-occurred_at']
        indexes = [
            models.Index(fields=['aggregate_type', 'aggregate_id'], name='idx_eventlog_aggregate'),
            models.Index(fields=['processed_at'], name='idx_eventlog_processed'),
            models.Index(fields=['correlation_id'], name='idx_eventlog_correlation'),
            # S21-01: índices de feed
            models.Index(fields=['aggregate_id', '-event_id'], name='idx_eventlog_exp_id_desc'),
            models.Index(fields=['proforma', '-event_id'], name='idx_eventlog_pf_id_desc'),
        ]

    def __str__(self):
        return f'{self.event_type} @ {self.occurred_at}'


# === S21-02: Modelo UserNotificationState ===
class UserNotificationState(models.Model):
    """
    High-water mark por usuario para calcular eventos no leídos.
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notification_state',
        primary_key=True,
    )
    last_seen_at = models.DateTimeField(
        null=True, blank=True,
        help_text='Timestamp del último EventLog visto. NULL = nunca visto. Se actualiza en mark-seen.'
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'User Notification State'
        verbose_name_plural = 'User Notification States'

    def __str__(self):
        return f'NotifState({self.user}) — last_seen={self.last_seen_at}'


class CostLine(AppendOnlyModel):
    cost_line_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    expediente = models.ForeignKey(
        Expediente,
        on_delete=models.PROTECT,
        related_name='cost_lines',
        null=True, blank=True,
    )
    transfer = models.ForeignKey(
        'transfers.Transfer',
        on_delete=models.PROTECT,
        null=True, blank=True,
        related_name='cost_lines',
        help_text='XOR with expediente – use one or the other'
    )
    cost_type = models.CharField(max_length=50)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, help_text='ISO 4217')
    phase = models.CharField(max_length=50)
    description = models.TextField(blank=True)
    visibility = models.CharField(
        max_length=10,
        choices=CostLineVisibility.choices,
        default=CostLineVisibility.INTERNAL,
    )
    cost_category = models.CharField(
        max_length=20, choices=CostCategory.choices,
        default=CostCategory.LANDED_COST,
    )
    cost_behavior = models.CharField(
        max_length=25, choices=CostBehavior.choices,
        blank=True, null=True,
    )
    exchange_rate = models.DecimalField(
        max_digits=12, decimal_places=6,
        blank=True, null=True,
    )
    amount_base_currency = models.DecimalField(
        max_digits=12, decimal_places=2,
        blank=True, null=True,
    )
    base_currency = models.CharField(max_length=3, default='USD')

    class Meta:
        verbose_name = 'Cost Line'
        verbose_name_plural = 'Cost Lines'
        ordering = ['-created_at']

    def __str__(self):
        return f'Cost {self.cost_type}: {self.amount} {self.currency}'


class PaymentLine(AppendOnlyModel):
    payment_line_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    expediente = models.ForeignKey(Expediente, on_delete=models.PROTECT, related_name='payment_lines')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, help_text='ISO 4217')
    method = models.CharField(max_length=50)
    reference = models.CharField(max_length=100)
    registered_at = models.DateTimeField()
    registered_by_type = models.CharField(max_length=10, choices=RegisteredByType.choices)
    registered_by_id = models.CharField(max_length=255)

    class Meta:
        verbose_name = 'Payment Line'
        verbose_name_plural = 'Payment Lines'
        ordering = ['-created_at']

    def __str__(self):
        return f'Payment {self.method}: {self.amount} {self.currency}'


class LogisticsOption(TimestampMixin):
    logistics_option_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    artifact_instance = models.ForeignKey(ArtifactInstance, on_delete=models.CASCADE, related_name='logistics_options')
    option_id = models.CharField(max_length=50)
    mode = models.CharField(max_length=20, choices=LogisticsMode.choices)
    carrier = models.CharField(max_length=100)
    route = models.CharField(max_length=200)
    estimated_days = models.IntegerField()
    estimated_cost = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, help_text='ISO 4217')
    valid_until = models.DateField(null=True, blank=True)
    source = models.CharField(max_length=20, choices=LogisticsSource.choices, default=LogisticsSource.MANUAL)
    is_selected = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'Logistics Option'
        verbose_name_plural = 'Logistics Options'
        ordering = ['-created_at']

    def __str__(self):
        return f'Option {self.option_id}: {self.mode} via {self.carrier}'
