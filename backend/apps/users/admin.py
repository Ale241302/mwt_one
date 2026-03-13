from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import MWTUser, UserPermission


@admin.register(MWTUser)
class MWTUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'role', 'is_api_user', 'is_active')
    list_filter  = ('role', 'is_api_user', 'is_active')
    fieldsets = UserAdmin.fieldsets + (
        ('MWT', {'fields': ('role', 'legal_entity', 'whatsapp_number', 'is_api_user', 'created_by')}),
    )


@admin.register(UserPermission)
class UserPermissionAdmin(admin.ModelAdmin):
    list_display = ('user', 'permission', 'granted_by', 'granted_at')
    list_filter  = ('permission',)
