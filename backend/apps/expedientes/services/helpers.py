import os
from django.db import transaction
from django.utils import timezone
from apps.expedientes.models import ArtifactInstance, PaymentLine, CostLine
from apps.expedientes.exceptions import (
    CommandValidationError, 
    ArtifactMissingError,
    CreditBlockedError
)

def _check_credit_gate(expediente, command_code):
    """S16-02: Block execution of status commands if credit is blocked.
    
    Checks if 'credit_blocked' flag is True and if a CEO override exists.
    """
    if expediente.credit_blocked:
        from apps.agreements.models import CreditOverride
        has_override = CreditOverride.objects.filter(
            expediente=expediente,
            command_code=command_code
        ).exists()
        
        if not has_override:
            raise CreditBlockedError(
                f"Expediente blocked due to credit issues. "
                f"CEO must issue a CreditOverride for command '{command_code}' to continue."
            )

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
