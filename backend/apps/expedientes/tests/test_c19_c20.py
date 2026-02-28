import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.base')
django.setup()

from apps.expedientes.models import Expediente, ArtifactInstance, EventLog, LegalEntity
from apps.expedientes.services import supersede_artifact, void_artifact
from apps.expedientes.enums import ExpedienteStatus, LegalEntityRole, LegalEntityRelationship, LegalEntityFrontend, LegalEntityVisibility, PricingVisibility, LegalEntityStatus

def main():
    print("Testing C19 (Supersede) and C20 (Void)")

    expediente = Expediente.objects.first()
    if not expediente:
        print("No Expediente found. Creating mock LegalEntity and Expediente...")
        legal_entity = LegalEntity.objects.create(
            entity_id="MOCK-TEST-123",
            legal_name="Mock Legal Entity",
            country="US",
            role=LegalEntityRole.DISTRIBUTOR,
            relationship_to_mwt=LegalEntityRelationship.DISTRIBUTION,
            frontend=LegalEntityFrontend.MWT_ONE,
            visibility_level=LegalEntityVisibility.FULL,
            pricing_visibility=PricingVisibility.CLIENT,
            status=LegalEntityStatus.ACTIVE
        )
        expediente = Expediente.objects.create(
            legal_entity=legal_entity,
            client=legal_entity,
            status=ExpedienteStatus.REGISTRO
        )
    class MockUser:
        def __init__(self, pk):
            self.pk = pk
    user = MockUser(1)

    print(f"Using Expediente: {expediente.expediente_id}")

    # 2. Add an ART-09 artifact (Voidable)
    art_09 = ArtifactInstance.objects.create(
        expediente=expediente,
        artifact_type="ART-09",
        status="COMPLETED",
        payload={"amount": 100}
    )
    print(f"Created ART-09: {art_09.artifact_id}, status: {art_09.status}")

    # 3. Void the ART-09 artifact
    print("Voiding ART-09...")
    try:
        exp_updated, voided_art, event = void_artifact(
            old_artifact_id=art_09.artifact_id,
            user=user
        )
        print(f"Success! Voided artifact status: {voided_art.status}")
        print(f"Event logged: {event.event_type}")
    except Exception as e:
        print(f"Failed to void: {e}")

    # 4. Add an ART-01 artifact (Supersedable since it's COMPLETED by default)
    art_01 = ArtifactInstance.objects.create(
        expediente=expediente,
        artifact_type="ART-01",
        status="COMPLETED",
        payload={"data": "original"}
    )
    print(f"\nCreated ART-01: {art_01.artifact_id}, status: {art_01.status}")

    # 5. Supersede the ART-01 artifact
    print("Superseding ART-01...")
    try:
        new_payload = {"data": "superseded version"}
        exp_updated, new_art, event = supersede_artifact(
            old_artifact_id=art_01.artifact_id,
            new_payload=new_payload,
            user=user
        )
        # Refresh old artifact
        art_01.refresh_from_db()
        print(f"Success! Old artifact status: {art_01.status}")
        print(f"New artifact ID: {new_art.artifact_id}, status: {new_art.status}, payload: {new_art.payload}")
        print(f"Event logged: {event.event_type}")
    except Exception as e:
        print(f"Failed to supersede: {e}")

if __name__ == "__main__":
    main()
