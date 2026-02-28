from django.contrib import admin
from .models import LegalEntity, Expediente, ArtifactInstance, EventLog, CostLine, PaymentLine

@admin.register(LegalEntity)
class LegalEntityAdmin(admin.ModelAdmin):
    list_display = ('id', 'legal_name', 'tax_id', 'entity_type', 'domain', 'country')
    search_fields = ('legal_name', 'tax_id', 'domain')
    list_filter = ('entity_type', 'country')

@admin.register(Expediente)
class ExpedienteAdmin(admin.ModelAdmin):
    list_display = ('id', 'client', 'brand', 'service_type', 'status', 'created_at', 'is_blocked')
    search_fields = ('brand', 'service_type')
    list_filter = ('status', 'is_blocked')

@admin.register(ArtifactInstance)
class ArtifactInstanceAdmin(admin.ModelAdmin):
    list_display = ('id', 'expediente', 'artifact_type', 'title', 'version', 'status')
    search_fields = ('title', 'artifact_type')
    list_filter = ('artifact_type', 'status')

@admin.register(EventLog)
class EventLogAdmin(admin.ModelAdmin):
    list_display = ('id', 'aggregate_type', 'aggregate_id', 'event_type', 'occurred_at')
    search_fields = ('event_type', 'aggregate_id')
    list_filter = ('aggregate_type', 'event_type')

@admin.register(CostLine)
class CostLineAdmin(admin.ModelAdmin):
    list_display = ('id', 'expediente', 'category', 'amount', 'currency', 'status')
    search_fields = ('category', 'description')
    list_filter = ('category', 'status', 'currency')

@admin.register(PaymentLine)
class PaymentLineAdmin(admin.ModelAdmin):
    list_display = ('id', 'cost_line', 'amount', 'currency', 'paid_at', 'reference')
    search_fields = ('reference',)
    list_filter = ('currency',)
