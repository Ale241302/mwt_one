import os
from django.db import transaction
from django.utils import timezone
from apps.expedientes.models import ArtifactInstance, PaymentLine, CostLine
from apps.expedientes.exceptions import CommandValidationError, ArtifactMissingError

def _has_artifact(expediente, art_type, status='completed'):
    return expediente.artifacts.filter(
        artifact_type=art_type, 
        status=status
    ).exists()

def _get_rule_count(expediente):
    from apps.brands.services import BrandService
    # Sprint 12: Fixed logic to handle missing rules
    rules = BrandService.get_artifact_flow(expediente.brand)
    if rules is None:
        return 4 # Default baseline
    return len(rules)

def _update_payment_status(expediente):
    total_paid = sum(p.amount for p in expediente.payments.all())
    # This logic might be simplified later
    if total_paid > 0:
        expediente.payment_status = 'partial'
    # ... more complex logic from services.py if needed
    expediente.save(update_fields=['payment_status'])
