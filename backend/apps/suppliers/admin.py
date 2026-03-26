from django.contrib import admin
from .models import Supplier, SupplierContact, SupplierPerformanceKPI


class SupplierContactInline(admin.TabularInline):
    model = SupplierContact
    extra = 1


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ('name', 'tax_id', 'country', 'is_active')
    search_fields = ('name', 'tax_id')
    inlines = [SupplierContactInline]


@admin.register(SupplierPerformanceKPI)
class SupplierPerformanceKPIAdmin(admin.ModelAdmin):
    list_display = ('supplier', 'year', 'month', 'overall_rating')
    list_filter = ('year', 'month')
