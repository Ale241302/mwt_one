# Sprint 18 - T0.1 Paso 5: Admin de sizing
from django.contrib import admin
from .models import (
    SizeSystem, SizeDimension, SizeEntry,
    SizeEntryValue, SizeEquivalence, BrandSizeSystemAssignment,
)
from .services import validate_entry_completeness


class SizeDimensionInline(admin.TabularInline):
    model = SizeDimension
    extra = 1


class SizeEntryInline(admin.TabularInline):
    model = SizeEntry
    extra = 1
    show_change_link = True


@admin.register(SizeSystem)
class SizeSystemAdmin(admin.ModelAdmin):
    list_display = ['code', 'category', 'is_active']
    inlines = [SizeDimensionInline, SizeEntryInline]


class SizeEntryValueInline(admin.TabularInline):
    model = SizeEntryValue
    extra = 1


class SizeEquivalenceInline(admin.TabularInline):
    model = SizeEquivalence
    extra = 1


@admin.register(SizeEntry)
class SizeEntryAdmin(admin.ModelAdmin):
    list_display = ['system', 'label', 'display_order', 'is_active']
    inlines = [SizeEntryValueInline, SizeEquivalenceInline]

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        if obj.is_active:
            validate_entry_completeness(obj)


@admin.register(BrandSizeSystemAssignment)
class BrandSizeSystemAssignmentAdmin(admin.ModelAdmin):
    list_display = ['brand', 'size_system', 'is_default', 'assigned_at']
