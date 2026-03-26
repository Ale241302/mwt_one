from django.contrib import admin
from apps.clientes.models import Cliente

@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'country', 'legal_entity', 'is_active']
    list_filter = ['is_active', 'country']
    search_fields = ['name', 'email']
