from django.db.models import Sum
from apps.expedientes.models import CostLine

def get_costs(expediente, view='internal'):
    qs = expediente.cost_lines.all()
    if view == 'client':
        qs = qs.filter(visibility='client')
    return qs

def get_costs_summary(expediente):
    # Sum internal vs client costs
    internal = expediente.cost_lines.aggregate(total=Sum('amount'))['total'] or 0
    client = expediente.cost_lines.filter(visibility='client').aggregate(total=Sum('amount'))['total'] or 0
    return {
        'internal_total': float(internal),
        'client_total': float(client),
        'margin': float(client - internal)
    }

def get_invoice_suggestion(expediente):
    # Logic for ART-09 suggestion
    return {'suggested_items': []}

def get_invoice(expediente, view='internal'):
    art09 = expediente.artifacts.filter(artifact_type='ART-09', status='completed').first()
    if not art09:
        return None
    return art09.payload

def calculate_financial_comparison(expediente):
    return {'actual': {}, 'estimated': {}}

def can_execute_command(expediente, cmd_id, user):
    from .constants import COMMAND_SPEC
    if cmd_id not in COMMAND_SPEC:
        return False
    
    cmd_config = COMMAND_SPEC[cmd_id]
    req_status = cmd_config.get('requires_status')
    if req_status and expediente.status != req_status:
        return False
    
    # Blocked check
    if expediente.is_blocked and cmd_id not in ['C18', 'C19', 'C20']:
        return False
        
    return True

def get_available_commands(expediente, user):
    from .constants import COMMAND_SPEC
    available = []
    for cmd_id in COMMAND_SPEC:
        if can_execute_command(expediente, cmd_id, user):
            available.append(cmd_id)
    return available
