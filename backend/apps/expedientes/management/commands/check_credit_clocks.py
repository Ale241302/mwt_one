import logging
from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.expedientes.models import Expediente
from apps.expedientes.enums_exp import ExpedienteStatus, PaymentStatus, BlockedByType

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Check credit clocks and apply warnings/blocks (S16-02)'

    def handle(self, *args, **options):
        now = timezone.now()
        # Only active expedientes that are not already closed or cancelled
        # and are not yet fully paid
        expedientes = Expediente.objects.filter(
            status__in=[
                ExpedienteStatus.REGISTRO,
                ExpedienteStatus.PRODUCCION,
                ExpedienteStatus.PREPARACION,
                ExpedienteStatus.DESPACHO,
                ExpedienteStatus.TRANSITO,
                ExpedienteStatus.EN_DESTINO
            ],
            credit_clock_started_at__isnull=False
        ).exclude(payment_status=PaymentStatus.PAID)

        updated_count = 0
        blocked_count = 0
        warning_count = 0

        for exp in expedientes:
            delta = now - exp.credit_clock_started_at
            days = delta.days
            
            changed = False
            
            # 90 Days: Block
            if days >= 90:
                if not exp.is_blocked or not exp.credit_blocked:
                    exp.is_blocked = True
                    exp.credit_blocked = True
                    exp.blocked_reason = f"Credit clock: {days} days elapsed without full payment."
                    exp.blocked_at = now
                    exp.blocked_by_type = BlockedByType.SYSTEM
                    exp.blocked_by_id = "credit_clock_90"
                    changed = True
                    blocked_count += 1
            
            # 75 Days: Warning
            elif days >= 75:
                if not exp.credit_warning:
                    exp.credit_warning = True
                    changed = True
                    warning_count += 1
            
            if changed:
                exp.save()
                updated_count += 1

        self.stdout.write(self.style.SUCCESS(
            f"Processed {expedientes.count()} expedientes. "
            f"Updated: {updated_count} (Blocked: {blocked_count}, Warning: {warning_count})"
        ))
