from django.contrib import admin
from apps.transfers.models import Transfer, TransferLine
from apps.nodos.models import Node


@admin.register(Node)
class NodeAdmin(admin.ModelAdmin):
    list_display = ["name", "node_type", "legal_entity", "status"]
    list_filter = ["node_type", "status"]


class TransferLineInline(admin.TabularInline):
    model = TransferLine
    extra = 0


@admin.register(Transfer)
class TransferAdmin(admin.ModelAdmin):
    list_display = ["transfer_id", "from_node", "to_node", "status", "created_at"]
    list_filter = ["status", "legal_context", "ownership_changes"]
    inlines = [TransferLineInline]
