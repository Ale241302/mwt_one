from django.contrib import admin
from .models import QRRoute, QRScan

@admin.register(QRRoute)
class QRRouteAdmin(admin.ModelAdmin):
    list_display = ('slug', 'product_name', 'is_active', 'override_url', 'created_at')
    search_fields = ('slug', 'product_name', 'product_slug')
    list_filter = ('is_active',)

@admin.register(QRScan)
class QRScanAdmin(admin.ModelAdmin):
    list_display = ('route', 'detected_lang', 'country_code', 'scanned_at')
    search_fields = ('route__slug', 'ip_hash')
    list_filter = ('detected_lang', 'country_code')
    readonly_fields = ('ip_hash', 'user_agent', 'scanned_at')
