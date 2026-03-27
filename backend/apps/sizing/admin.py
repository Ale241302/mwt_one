from django.contrib import admin
from .models import (
    SizeSystem, SizeDimension, SizeEntry,
    SizeEntryValue, SizeEquivalence, BrandSizeSystemAssignment,
)
from .services import validate_entry_completeness


class SizeDimensionInline(admin.TabularInline):
    model = SizeDimension
    extra = 1
    fields = ('code', 'display_name', 'unit', 'display_order', 'is_primary')


class SizeEntryInline(admin.TabularInline):
    model = SizeEntry
    extra = 1
    fields = ('label', 'display_order', 'is_active')


@admin.register(SizeSystem)
class SizeSystemAdmin(admin.ModelAdmin):
    list_display = ('code', 'category', 'is_active', 'created_at')
    list_filter = ('category', 'is_active')
    search_fields = ('code',)
    inlines = [SizeDimensionInline, SizeEntryInline]


class SizeEntryValueInline(admin.TabularInline):
    model = SizeEntryValue
    extra = 1
    fields = ('dimension', 'value')


class SizeEquivalenceInline(admin.TabularInline):
    model = SizeEquivalence
    extra = 1
    fields = ('standard_system', 'value', 'display_order', 'is_primary')


@admin.register(SizeEntry)
class SizeEntryAdmin(admin.ModelAdmin):
    list_display = ('label', 'system', 'display_order', 'is_active')
    list_filter = ('system', 'is_active')
    search_fields = ('label', 'system__code')
    inlines = [SizeEntryValueInline, SizeEquivalenceInline]

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        if obj.is_active:
            try:
                validate_entry_completeness(obj)
            except Exception as e:
                self.message_user(request, str(e), level='warning')


@admin.register(BrandSizeSystemAssignment)
class BrandSizeSystemAssignmentAdmin(admin.ModelAdmin):
    list_display = ('brand', 'size_system', 'is_default', 'assigned_at')
    list_filter = ('is_default', 'size_system__category')
    search_fields = ('brand__code', 'size_system__code')
