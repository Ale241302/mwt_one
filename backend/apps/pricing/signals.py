from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from apps.pricing.models import ClientProductAssignment
from apps.expedientes.models import Expediente
import logging
from apps.audit.models import ConfigChangeLog


logger = logging.getLogger(__name__)

@receiver([post_save, post_delete], sender=ClientProductAssignment)
def trigger_cpa_recalculate(sender, instance, **kwargs):
    """
    S32: CPA Auto-recalculate
    When a PriceAssignment changes, flag or trigger recalculation of open Expedientes
    that rely on this price.
    """
    created = kwargs.get('created', False)
    if not created:
        # S31: History of changes per client/SKU (audited)
        ConfigChangeLog.objects.create(
            user=kwargs.get('user'), # Conceptually, if passed via session or thread-local
            model_name='ClientProductAssignment',
            record_id=str(instance.id),
            action='update',
            changes={
                "old_price": float(instance._old_price) if hasattr(instance, '_old_price') else None,
                "new_price": float(instance.cached_client_price) if instance.cached_client_price else 0.0
            }
        )

    # Find active expedientes for this brand and SKU that might need recalcs
    brand_sku = instance.brand_sku
    client_subsidiary = instance.client_subsidiary
    sku = instance.brand_sku

    if brand_sku and sku:
        # Simplification: we trigger recalculate for active ones based on pricing fields
        active_expedientes = Expediente.objects.filter(
            brand=brand_sku.brand,
            client=client_subsidiary,
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
