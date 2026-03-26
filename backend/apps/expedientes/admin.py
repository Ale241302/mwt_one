"""S17-13: Admin configuration with inlines for Sprint 17 new models."""
from django.contrib import admin
from .models import (
    Expediente, ArtifactInstance, EventLog, CostLine, PaymentLine, LogisticsOption,
    ExpedienteProductLine, FactoryOrder, ExpedientePago,
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


# S17-13: New inlines for Sprint 17 models
class ExpedienteProductLineInline(admin.TabularInline):
    model = ExpedienteProductLine
    extra = 0
    readonly_fields = ('created_at', 'updated_at')
    show_change_link = True


class FactoryOrderInline(admin.TabularInline):
    model = FactoryOrder
    extra = 0
    readonly_fields = ('created_at', 'updated_at')
    show_change_link = True


class ExpedientePagoInline(admin.TabularInline):
    model = ExpedientePago
    extra = 0
    readonly_fields = ('created_at',)
    show_change_link = True


@admin.register(Expediente)
class ExpedienteAdmin(admin.ModelAdmin):
    list_display = ('expediente_id', 'status', 'destination', 'client', 'is_blocked', 'created_at')
    list_filter = ('status', 'destination', 'is_blocked', 'operado_por')
    search_fields = ('expediente_id', 'ref_number', 'factory_order_number', 'awb_bl_number')
    readonly_fields = ('expediente_id', 'created_at', 'updated_at')
    inlines = [
        ArtifactInstanceInline,
        CostLineInline,
        PaymentLineInline,
        # S17-13: New inlines
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
    )


@admin.register(ExpedienteProductLine)
class ExpedienteProductLineAdmin(admin.ModelAdmin):
    list_display = ('expediente', 'product', 'quantity', 'unit_price', 'price_source', 'created_at')
    list_filter = ('price_source',)
    readonly_fields = ('created_at', 'updated_at')


@admin.register(FactoryOrder)
class FactoryOrderAdmin(admin.ModelAdmin):
    list_display = ('expediente', 'order_number', 'purchase_number', 'created_at')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(ExpedientePago)
class ExpedientePagoAdmin(admin.ModelAdmin):
    list_display = ('expediente', 'tipo_pago', 'metodo_pago', 'amount_paid', 'payment_date', 'created_at')
    list_filter = ('tipo_pago', 'metodo_pago')
    readonly_fields = ('created_at',)
