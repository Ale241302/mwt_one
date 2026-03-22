from apps.agreements.models import BrandWorkflowPolicy
from apps.expedientes.services.constants import COMMAND_SPEC
from django.utils import timezone

def can_transition_to(expediente, cmd_id, user):
    """
    S14-07: Refactor to check BrandWorkflowPolicy if available.
    """
    spec = COMMAND_SPEC.get(cmd_id)
    if not spec:
        return False, "Unknown command"

    # 1. Custom Policy check if available
    if expediente.brand:
        now = timezone.now()
        policy = BrandWorkflowPolicy.objects.filter(
            brand=expediente.brand,
            status='active',
            valid_daterange__contains=now
        ).first()

        if policy:
            transition = policy.transition_policies.filter(
                from_state=expediente.status,
                command=cmd_id
            ).first()

            if not transition:
                return False, f"Workflow policy prohibits command {cmd_id} from state {expediente.status}"
    
    # Fallback to COMMAND_SPEC if no transition policy or no brand
    requires = spec.get('requires_status')
    if requires and expediente.status not in requires:
        return False, f"Command {cmd_id} requires status {requires}. Current: {expediente.status}"

    # 2. Block rule
    if expediente.is_blocked and not spec.get('bypass_block', False):
        return False, f"Expediente {expediente.expediente_id} is blocked."
    
    # 3. Permissions rule (CEO)
    if spec.get('requires_ceo') and not user.is_superuser:
        return False, "This command requires CEO privileges."
        
    return True, ""
