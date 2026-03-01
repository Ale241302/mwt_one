from django.contrib import admin
from .models import LegalEntity, Expediente, ArtifactInstance, EventLog, CostLine, PaymentLine

@admin.register(LegalEntity)
class LegalEntityAdmin(admin.ModelAdmin):
    list_display = ('entity_id', 'legal_name', 'tax_id', 'role', 'country')
    search_fields = ('legal_name', 'tax_id', 'entity_id')
    list_filter = ('role', 'country')

@admin.register(Expediente)
class ExpedienteAdmin(admin.ModelAdmin):
    list_display = ('expediente_id', 'client', 'brand', 'mode', 'status', 'created_at', 'is_blocked')
    search_fields = ('brand', 'mode')
    list_filter = ('status', 'is_blocked')

@admin.register(ArtifactInstance)
class ArtifactInstanceAdmin(admin.ModelAdmin):
    list_display = ('artifact_id', 'expediente', 'artifact_type', 'status')
    search_fields = ('artifact_type',)
    list_filter = ('artifact_type', 'status')

@admin.register(EventLog)
class EventLogAdmin(admin.ModelAdmin):
    list_display = ('event_id', 'aggregate_type', 'aggregate_id', 'event_type', 'occurred_at')
    search_fields = ('event_type', 'aggregate_id')
    list_filter = ('aggregate_type', 'event_type')

@admin.register(CostLine)
class CostLineAdmin(admin.ModelAdmin):
    list_display = ('cost_line_id', 'expediente', 'cost_type', 'amount', 'currency', 'phase')
    search_fields = ('cost_type', 'description')
    list_filter = ('cost_type', 'currency', 'phase')

@admin.register(PaymentLine)
class PaymentLineAdmin(admin.ModelAdmin):
    list_display = ('payment_line_id', 'expediente', 'amount', 'currency', 'registered_at', 'method')
    search_fields = ('reference', 'method')
    list_filter = ('currency', 'method')
