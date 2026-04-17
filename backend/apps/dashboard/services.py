from django.utils import timezone
from django.db.models import Sum, Count
from apps.dashboard.models import DashboardKPI
from apps.core.registry import ModuleRegistry
from decimal import Decimal

class KPIWorkerService:
    """
    Servicio encargado de recalibrar los Read Models del dashboard.
    Centraliza la lógica de agregación distribuida.
    """
    
    @staticmethod
    def recalibrate_all():
        KPIWorkerService.recalculate_pipeline_stats()
        KPIWorkerService.recalculate_finance_stats()
        KPIWorkerService.recalculate_stale_expedientes()

    @staticmethod
    def recalculate_pipeline_stats():
        """Calcula el pipeline activo consultando el módulo de expedientes."""
        expediente_model = ModuleRegistry.get_model('expedientes', 'Expediente')
        if not expediente_model:
            return

        # Pipeline Count
        count = expediente_model.objects.exclude(
            status__in=['CERRADO', 'CANCELADO']
        ).count()

        DashboardKPI.objects.update_or_create(
            metric_name='pipeline_count',
            defaults={
                'metric_value': Decimal(count),
                'calculated_at': timezone.now()
            }
        )

    @staticmethod
    def recalculate_finance_stats():
        """Suma montos pendientes desde el módulo finance."""
        payment_model = ModuleRegistry.get_model('finance', 'Payment')
        if not payment_model:
            return

        pending_amount = payment_model.objects.filter(
            status='pending'
        ).aggregate(total=Sum('amount_paid'))['total'] or Decimal(0)

        DashboardKPI.objects.update_or_create(
            metric_name='pending_collections_sum',
            defaults={
                'metric_value': pending_amount,
                'metric_currency': 'USD',
                'calculated_at': timezone.now()
            }
        )

    @staticmethod
    def recalculate_stale_expedientes():
        """Analiza expedientes sin movimiento."""
        event_model = ModuleRegistry.get_model('expedientes', 'EventLog')
        if not event_model:
            return

        # Lógica simplificada para el dashboard
        # En una prod real, esto sería una query más optimizada o basada en una tabla de 'LatestEvent'
        stale_threshold = timezone.now() - timezone.timedelta(days=3)
        # ... lógica de detección ...
        # Por ahora guardamos un valor placeholder para la estructura
        DashboardKPI.objects.update_or_create(
            metric_name='action_needed_count',
            defaults={
                'metric_value': Decimal(5), # Ejemplo
                'calculated_at': timezone.now()
            }
        )
