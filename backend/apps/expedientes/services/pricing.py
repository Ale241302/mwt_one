from apps.agreements.models import BrandClientAgreement

def assign_agreement_defaults(expediente):
    """S16-04: Assign standard cost and commission based on active agreement."""
    # Logic: find active agreement for Brand + Subsidiary
    agreement = BrandClientAgreement.objects.filter(
        brand=expediente.brand,
        party_type='subsidiary',
        party_id=expediente.subsidiary_id,
        status='active'
    ).first()
    
    if not agreement:
        # Fallback to Group agreement if needed
        pass
        
    if agreement:
        expediente.standard_cost_estimated = agreement.standard_cost
        expediente.commission_estimated = agreement.commission
        expediente.save(update_fields=['standard_cost_estimated', 'commission_estimated'])
        return True
    return False
