from apps.agreements.models import BrandWorkflowPolicy
from apps.expedientes.services.constants import COMMAND_SPEC
from django.utils import timezone

def can_transition_to(expediente, cmd_id, user):
    """
    MODO LIBRE: Siempre permite transicionar.
    Ignora BrandWorkflowPolicy, requisitos de estado, bloqueos y privilegios CEO.
    """
    return True, ""
