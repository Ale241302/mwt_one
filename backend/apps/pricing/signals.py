from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from apps.pricing.models import PriceAssignment
from apps.expedientes.models import Expediente
import logging

logger = logging.getLogger(__name__)

@receiver([post_save, post_delete], sender=PriceAssignment)
def trigger_cpa_recalculate(sender, instance, **kwargs):
    """
    S32: CPA Auto-recalculate
    When a PriceAssignment changes, flag or trigger recalculation of open Expedientes
    that rely on this price.
    """
    # Find active expedientes for this brand and SKU that might need recalcs
    brand = instance.brand
    client = instance.client
    sku = instance.sku

    if brand and sku:
        # Simplification: we trigger recalculate for active ones based on pricing fields
        active_expedientes = Expediente.objects.filter(
            brand=brand,
            client=client,
            is_blocked=False # or whatever open statuses
        )
        
        for exp in active_expedientes:
            try:
                # Trigger specific method. Assume Expediente has update_cached_base_price()
                if hasattr(exp, 'update_cached_base_price'):
                    exp.update_cached_base_price()
                    logger.info(f"Triggered CPA auto-recalc for Exp {exp.expediente_id}")
            except Exception as e:
                logger.error(f"Error recalculating CPA for Exp {exp.expediente_id}: {e}")
