"""S17-05: handle_c1 signature fixed to (payload, user) — consistent with dispatcher."""
from django.db import transaction
from apps.expedientes.models import Expediente
from apps.expedientes.enums_exp import ExpedienteStatus


def handle_c1(payload, user):
    """
    S17-05 FIX: Signature is (payload, user) — matches how the dispatcher calls all handlers.
    Previously was (user, payload) which caused argument order bugs.

    Creates a new Expediente in REGISTRO status.
    payload keys: legal_entity_id, client_id, destination, brand_id (optional)
    """
    legal_entity_id = payload.get('legal_entity_id')
    client_id = payload.get('client_id')
    destination = payload.get('destination', 'CR')
    brand_id = payload.get('brand_id')

    with transaction.atomic():
        expediente = Expediente.objects.create(
            legal_entity_id=legal_entity_id,
            client_id=client_id,
            destination=destination,
            brand_id=brand_id,
            status=ExpedienteStatus.REGISTRO,
        )
    return expediente
