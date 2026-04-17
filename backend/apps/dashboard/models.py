import uuid
from django.db import models
from apps.core.models import BaseModel

class DashboardKPI(BaseModel):
    """
    Read Model materializado para KPIs.
    Se actualiza de forma asíncrona mediante el procesamiento de eventos del bus.
    Evita joins complejos entre módulos en tiempo de ejecución.
    """
    metric_name = models.CharField(max_length=100, db_index=True)
    metric_value = models.DecimalField(max_digits=20, decimal_places=4)
    metric_currency = models.CharField(max_length=3, null=True, blank=True)
    dimensions = models.JSONField(default=dict, help_text="Dimensiones para filtrado (e.g., brand_id, client_id, node_id)")
    calculated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'dashboard_kpi'
        verbose_name = 'KPI de Dashboard'
        verbose_name_plural = 'KPIs de Dashboard'
        ordering = ['-calculated_at']

    def __str__(self):
        return f"{self.metric_name}: {self.metric_value} ({self.dimensions})"

class DashboardWidget(BaseModel):
    """
    Configuración personalizada de widgets para los tableros de los usuarios.
    """
    user_id = models.UUIDField(null=True, blank=True, db_index=True, help_text="Referencia al usuario (módulo users)")
    widget_type = models.CharField(max_length=50)
    config = models.JSONField(default=dict, help_text="Configuración específica del widget")
    position = models.IntegerField(default=0)
    is_visible = models.BooleanField(default=True)

    class Meta:
        db_table = 'dashboard_widget'
        ordering = ['position']

    def __str__(self):
        return f"Widget {self.widget_type} (Pos: {self.position})"
