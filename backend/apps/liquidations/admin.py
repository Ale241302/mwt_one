from django.contrib import admin
from apps.liquidations.models import Liquidation, LiquidationLine


class LiquidationLineInline(admin.TabularInline):
    model = LiquidationLine
    extra = 0


@admin.register(Liquidation)
class LiquidationAdmin(admin.ModelAdmin):
    list_display = [
        "liquidation_id", "period", "brand", "status",
        "total_lines", "created_at"
    ]
    list_filter = ["status", "brand"]
    inlines = [LiquidationLineInline]
