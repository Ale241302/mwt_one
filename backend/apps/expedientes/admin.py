"""S21: Admin configuration — agrega UserNotificationState y EventLog con campos S21."""
from django.contrib import admin
from .models import (
    Expediente, ArtifactInstance, EventLog, CostLine, PaymentLine, LogisticsOption,
    ExpedienteProductLine, FactoryOrder, ExpedientePago,
    UserNotificationState,  # S21-02
)


class ArtifactInstanceInline(admin.TabularInline):
    model = ArtifactInstance
    extra = 0
    readonly_fields = ('artifact_id', 'created_at', 'updated_at')
    show_change_link = True


class CostLineInline(admin.TabularInline):
    model = CostLine
    extra = 0
    readonly_fields = ('cost_line_id', 'created_at')


class PaymentLineInline(admin.TabularInline):
    model = PaymentLine
    extra = 0
    readonly_fields = ('payment_line_id', 'created_at')


class ExpedienteProductLineInline(admin.TabularInline):
    model = ExpedienteProductLine
    fk_name = 'expediente'
    extra = 0
    readonly_fields = ('created_at', 'updated_at')
    fields = (
        'product', 'quantity', 'unit_price', 'price_source',
        'proforma',
        'brand_sku', 'pricelist_used', 'base_price',
        'quantity_modified', 'unit_price_modified', 'modification_reason',
        'factory_order', 'separated_to_expediente',
        'created_at', 'updated_at',
    )
    show_change_link = True


class FactoryOrderInline(admin.TabularInline):
    model = FactoryOrder
    extra = 0
    readonly_fields = ('created_at', 'updated_at')
    show_change_link = True


class ExpedientePagoInline(admin.TabularInline):
    model = ExpedientePago
    extra = 0
    readonly_fields = ('created_at', 'verified_by', 'credit_released_by')
    show_change_link = True


@admin.register(Expediente)
class ExpedienteAdmin(admin.ModelAdmin):
    list_display = ('expediente_id', 'status', 'destination', 'client', 'is_blocked', 'created_at')
    list_filter = ('status', 'destination', 'is_blocked', 'operado_por')
    search_fields = ('expediente_id', 'ref_number', 'factory_order_number', 'awb_bl_number')
    readonly_fields = ('expediente_id', 'created_at', 'updated_at', 'parent_expediente', 'is_inverted_child')  # S25-02
    inlines = [
        ArtifactInstanceInline,
        CostLineInline,
        PaymentLineInline,
        ExpedienteProductLineInline,
        FactoryOrderInline,
        ExpedientePagoInline,
    ]
    fieldsets = (
        ('Core', {
            'fields': ('expediente_id', 'legal_entity', 'client', 'brand', 'destination', 'status', 'mode')
        }),
        ('Blocking', {
            'fields': ('is_blocked', 'blocked_reason', 'blocked_at', 'blocked_by_type', 'blocked_by_id'),
            'classes': ('collapse',)
        }),
        ('Credit', {
            'fields': ('credit_blocked', 'credit_warning', 'credit_clock_start_rule', 'credit_clock_started_at'),
            'classes': ('collapse',)
        }),
        ('Reopen', {
            'fields': ('reopen_count', 'reopened_at', 'reopen_justification'),
            'classes': ('collapse',)
        }),
        ('S17 — Generales', {
            'fields': ('purchase_order_number', 'operado_por', 'url_orden_compra', 'ref_number',
                       'credit_days_client', 'credit_days_mwt', 'credit_limit_client', 'credit_limit_mwt', 'order_value'),
            'classes': ('collapse',)
        }),
        ('S17 — Producción', {
            'fields': ('factory_order_number', 'proforma_client_number', 'proforma_mwt_number',
                       'fabrication_start_date', 'fabrication_end_date',
                       'url_proforma_cliente', 'url_proforma_muito_work', 'master_expediente'),
            'classes': ('collapse',)
        }),
        ('S17 — Preparación', {
            'fields': ('shipping_method', 'incoterms', 'cargo_manager', 'shipping_value',
                       'payment_mode_shipping', 'url_list_empaque', 'url_cotizacion_envio'),
            'classes': ('collapse',)
        }),
        ('S17 — Despacho', {
            'fields': ('airline_or_shipping_company', 'awb_bl_number', 'origin_location', 'arrival_location',
                       'shipment_date', 'payment_date_dispatch', 'invoice_client_number', 'invoice_mwt_number',
                       'dispatch_additional_info', 'url_certificado_origen', 'url_factura_cliente',
                       'url_factura_muito_work', 'url_awb_bl', 'tracking_url'),
            'classes': ('collapse',)
        }),
        ('S17 — Tránsito', {
            'fields': ('intermediate_airport_or_port', 'transit_arrival_date', 'url_packing_list_detallado'),
            'classes': ('collapse',)
        }),
        ('S25-02 — Precio diferido', {
            'fields': ('deferred_total_price', 'deferred_visible'),
            'classes': ('collapse',),
            'description': 'Precio diferido editable solo por CEO. NULL = no definido.',
        }),
        ('S25-02 — Parent/Child (read-only)', {
            'fields': ('parent_expediente', 'is_inverted_child'),
            'classes': ('collapse',),
            'description': 'Relación genealógica entre expedientes (split). Informativo.',
        }),
    )


@admin.register(ExpedienteProductLine)
class ExpedienteProductLineAdmin(admin.ModelAdmin):
    list_display = ('expediente', 'product', 'quantity', 'unit_price', 'price_source', 'proforma', 'created_at')
    list_filter = ('price_source',)
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Datos principales', {
            'fields': ('expediente', 'product', 'quantity', 'unit_price', 'price_source')
        }),
        ('S20 — Proforma', {
            'fields': ('proforma',),
            'description': 'S20-01: ART-02 al que pertenece esta línea. NULL = línea legacy pre-S20.'
        }),
        ('SKU / Precio', {
            'fields': ('brand_sku', 'pricelist_used', 'base_price'),
            'classes': ('collapse',)
        }),
        ('Modificaciones', {
            'fields': ('quantity_modified', 'unit_price_modified', 'modification_reason'),
            'classes': ('collapse',)
        }),
        ('Trazabilidad', {
            'fields': ('factory_order', 'separated_to_expediente', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(FactoryOrder)
class FactoryOrderAdmin(admin.ModelAdmin):
    list_display = ('expediente', 'order_number', 'purchase_number', 'created_at')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(ExpedientePago)
class ExpedientePagoAdmin(admin.ModelAdmin):
    list_display = (
        'expediente', 'tipo_pago', 'metodo_pago', 'amount_paid',
        'payment_status', 'payment_date', 'created_at',
    )
    list_filter = ('tipo_pago', 'metodo_pago', 'payment_status')  # S25-01: filtrable
    search_fields = ('expediente__expediente_id',)
    readonly_fields = (
        'created_at',
        'verified_by', 'credit_released_by',   # S25-01: read-only (auditoria)
    )
    fieldsets = (
        ('Datos del pago', {
            'fields': (
                'expediente', 'tipo_pago', 'metodo_pago', 'amount_paid',
                'payment_date', 'additional_info', 'url_comprobante', 'credit_status',
            )
        }),
        ('S25-01 — Payment Status Machine', {
            'fields': (
                'payment_status', 'rejection_reason',
                'verified_at', 'verified_by',
                'credit_released_at', 'credit_released_by',
            ),
            'classes': ('collapse',),
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',),
        }),
    )


# === S21-02: EventLog admin extendido con campos S21 ===
@admin.register(EventLog)
class EventLogAdmin(admin.ModelAdmin):
    list_display = (
        'event_type', 'action_source', 'user', 'previous_status', 'new_status',
        'aggregate_id', 'occurred_at',
    )
    list_filter = ('event_type', 'action_source', 'previous_status', 'new_status')
    search_fields = ('event_type', 'action_source', 'aggregate_id')
    readonly_fields = ('event_id', 'correlation_id', 'occurred_at', 'processed_at')
    fieldsets = (
        ('Core', {
            'fields': ('event_id', 'event_type', 'aggregate_type', 'aggregate_id', 'correlation_id')
        }),
        ('S21 — Trazabilidad', {
            'fields': ('user', 'proforma', 'action_source', 'previous_status', 'new_status'),
        }),
        ('Meta', {
            'fields': ('occurred_at', 'processed_at', 'retry_count', 'emitted_by'),
            'classes': ('collapse',)
        }),
    )


# === S21-02: UserNotificationState admin ===
@admin.register(UserNotificationState)
class UserNotificationStateAdmin(admin.ModelAdmin):
    list_display = ('user', 'last_seen_at', 'updated_at')
    search_fields = ('user__username', 'user__email')
    readonly_fields = ('updated_at',)
