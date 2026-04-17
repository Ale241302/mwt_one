from django.contrib import admin
from .models import Invoice, Payment

class PaymentInline(admin.TabularInline):
    model = Payment
    extra = 0
    readonly_fields = ('id', 'created_at', 'verified_at')

@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('invoice_number', 'expediente_id', 'amount', 'currency', 'status', 'created_at')
    list_filter = ('status', 'currency')
    search_fields = ('invoice_number', 'expediente_id')
    inlines = [PaymentInline]

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('expediente_id', 'tipo_pago', 'metodo_pago', 'amount_paid', 'status', 'payment_date', 'created_at')
    list_filter = ('status', 'tipo_pago', 'metodo_pago')
    search_fields = ('expediente_id', 'id')
    readonly_fields = ('id', 'created_at', 'verified_at')
