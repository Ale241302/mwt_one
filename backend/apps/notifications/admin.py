"""
S26: Django Admin para modelos de notificaciones.
Todos los modelos de audit trail (Attempt, Log, CollectionEmailLog) son read-only.
"""
from django.contrib import admin
from .models import (
    NotificationTemplate, NotificationAttempt,
    NotificationLog, CollectionEmailLog,
)


@admin.register(NotificationTemplate)
class NotificationTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'template_key', 'language', 'brand', 'is_active', 'created_at']
    list_filter = ['is_active', 'language', 'brand']
    search_fields = ['name', 'template_key']
    readonly_fields = ['id', 'created_at', 'updated_at', 'created_by']
    ordering = ['template_key', 'language']


@admin.register(NotificationAttempt)
class NotificationAttemptAdmin(admin.ModelAdmin):
    list_display = ['id', 'template_key', 'status', 'recipient_email', 'attempted_at']
    list_filter = ['status']
    search_fields = ['recipient_email', 'template_key']
    readonly_fields = [f.name for f in NotificationAttempt._meta.get_fields()
                       if hasattr(f, 'name')]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(NotificationLog)
class NotificationLogAdmin(admin.ModelAdmin):
    list_display = ['id', 'template_key', 'status', 'recipient_email', 'created_at', 'completed_at']
    list_filter = ['status']
    search_fields = ['recipient_email', 'template_key']
    readonly_fields = [f.name for f in NotificationLog._meta.get_fields()
                       if hasattr(f, 'name')]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(CollectionEmailLog)
class CollectionEmailLogAdmin(admin.ModelAdmin):
    list_display = ['id', 'expediente', 'status', 'recipient_email', 'amount_overdue', 'created_at']
    list_filter = ['status']
    search_fields = ['recipient_email']
    readonly_fields = [f.name for f in CollectionEmailLog._meta.get_fields()
                       if hasattr(f, 'name')]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
