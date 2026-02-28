import pytest
from rest_framework.test import APIClient
from rest_framework import status
from django.urls import reverse
import uuid

from apps.expedientes.models import Expediente, ArtifactInstance, EventLog, LegalEntity

@pytest.fixture
def auth_client():
    client = APIClient()
    from django.contrib.auth.models import User
    user = User.objects.create_superuser('ceo', 'ceo@mwt.com', 'password')
    client.force_authenticate(user=user)
    return client

@pytest.fixture
def regular_user_client():
    client = APIClient()
    from django.contrib.auth.models import User
    user = User.objects.create_user('regular', 'regular@mwt.com', 'password')
    client.force_authenticate(user=user)
    return client

@pytest.fixture
def make_entities():
    le = LegalEntity.objects.create(entity_id="MWT-1", legal_name="MWT", country="CR", role="OPERATOR", relationship_to_mwt="INTERNAL", frontend="APP", visibility_level="PUBLIC", pricing_visibility="ALL")
    client = LegalEntity.objects.create(entity_id="CLI-1", legal_name="Client", country="CR", role="CLIENT", relationship_to_mwt="EXTERNAL", frontend="NONE", visibility_level="PRIVATE", pricing_visibility="NONE")
    return le, client

@pytest.mark.django_db
def test_supersede_artifact_api(auth_client, make_entities):
    le, client = make_entities
    exp = Expediente.objects.create(expediente_id=uuid.uuid4(), legal_entity=le, client=client, status="PRODUCCION")
    artifact = ArtifactInstance.objects.create(expediente=exp, artifact_type="ART-01", status="COMPLETED", payload={"dummy": "data"})
    
    url = reverse("expedientes:supersede-artifact", kwargs={"pk": str(exp.expediente_id), "artifact_id": str(artifact.artifact_id)})
    payload = {
        "payload": {"new_dummy": "new_data"},
        "reason": "Test replacement"
    }
    
    response = auth_client.post(url, payload, format="json")
    
    assert response.status_code == status.HTTP_201_CREATED
    assert "artifact" in response.data
    
    artifact.refresh_from_db()
    new_artifact = ArtifactInstance.objects.get(artifact_id=response.data["artifact"]["artifact_id"])
    
    # Check old artifact
    assert artifact.status == "SUPERSEDED"
    assert artifact.superseded_by == new_artifact
    
    # Check new artifact
    assert new_artifact.status == "COMPLETED"
    assert new_artifact.supersedes == artifact
    assert new_artifact.payload == {"new_dummy": "new_data"}
    
    # Check events
    superseded_event = EventLog.objects.filter(event_type="artifact.superseded").first()
    assert superseded_event is not None
    assert str(superseded_event.aggregate_id) == str(exp.expediente_id)

@pytest.mark.django_db
def test_supersede_artifact_fails_if_not_completed(auth_client, make_entities):
    le, client = make_entities
    exp = Expediente.objects.create(expediente_id=uuid.uuid4(), legal_entity=le, client=client, status="PRODUCCION")
    
    artifact = ArtifactInstance.objects.create(
        expediente=exp,
        artifact_type="ART-01",
        status="PENDING", # Not completed
        payload={"dummy": "data"}
    )
    
    url = reverse("expedientes:supersede-artifact", kwargs={"pk": str(exp.expediente_id), "artifact_id": str(artifact.artifact_id)})
    payload = {
        "payload": {"new_dummy": "new_data"},
        "reason": "Test replacement"
    }
    
    response = auth_client.post(url, payload, format="json")
    
    assert response.status_code == status.HTTP_400_BAD_REQUEST

@pytest.mark.django_db
def test_void_artifact_api(auth_client, make_entities):
    le, client = make_entities
    exp = Expediente.objects.create(expediente_id=uuid.uuid4(), legal_entity=le, client=client, status="PRODUCCION")
    
    artifact = ArtifactInstance.objects.create(
        expediente=exp,
        artifact_type="ART-09", # Only ART-09 is allowed in MVP
        status="COMPLETED",
        payload={"dummy": "data"}
    )
    
    url = reverse("expedientes:void-artifact", kwargs={"pk": str(exp.expediente_id), "artifact_id": str(artifact.artifact_id)})
    payload = {
        "reason": "Voiding bill of lading"
    }
    
    response = auth_client.post(url, payload, format="json")
    
    assert response.status_code == status.HTTP_200_OK
    
    artifact.refresh_from_db()
    assert artifact.status == "VOID"
    
    # Check events
    void_event = EventLog.objects.filter(event_type="artifact.voided").first()
    assert void_event is not None
    assert str(void_event.aggregate_id) == str(exp.expediente_id)

@pytest.mark.django_db
def test_void_artifact_not_allowed_type(auth_client, make_entities):
    le, client = make_entities
    exp = Expediente.objects.create(expediente_id=uuid.uuid4(), legal_entity=le, client=client, status="PRODUCCION")
    
    artifact = ArtifactInstance.objects.create(
        expediente=exp,
        artifact_type="ART-01", # Not ART-09
        status="COMPLETED",
        payload={"dummy": "data"}
    )
    
    url = reverse("expedientes:void-artifact", kwargs={"pk": str(exp.expediente_id), "artifact_id": str(artifact.artifact_id)})
    payload = {
        "reason": "Voiding non-allowed artifact"
    }
    
    response = auth_client.post(url, payload, format="json")
    
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Solo ART-09" in str(response.data) or "not allowed" in str(response.data).lower() or "only art-09" in str(response.data).lower()

@pytest.mark.django_db
def test_supersede_artifact_permission_fails_for_regular_user(regular_user_client, make_entities):
    le, client = make_entities
    exp = Expediente.objects.create(expediente_id=uuid.uuid4(), legal_entity=le, client=client, status="PRODUCCION")
    art = ArtifactInstance.objects.create(expediente=exp, artifact_type="ART-01", status="COMPLETED")
    url = reverse("expedientes:supersede-artifact", kwargs={"pk": str(exp.expediente_id), "artifact_id": str(art.artifact_id)})
    response = regular_user_client.post(url, {"payload": {}, "reason": "test"}, format="json")
    assert response.status_code == status.HTTP_403_FORBIDDEN

@pytest.mark.django_db
def test_supersede_artifact_fails_in_terminal_state(auth_client, make_entities):
    le, client = make_entities
    exp = Expediente.objects.create(expediente_id=uuid.uuid4(), legal_entity=le, client=client, status="CERRADO")
    art = ArtifactInstance.objects.create(expediente=exp, artifact_type="ART-01", status="COMPLETED")
    url = reverse("expedientes:supersede-artifact", kwargs={"pk": str(exp.expediente_id), "artifact_id": str(art.artifact_id)})
    response = auth_client.post(url, {"payload": {}, "reason": "test"}, format="json")
    assert response.status_code == status.HTTP_400_BAD_REQUEST

@pytest.mark.django_db
def test_supersede_artifact_post_transition_blocks(auth_client, make_entities):
    le, client = make_entities
    # Expediente in PRODUCCION means ART-01 (created in REGISTRO) is from a past state
    exp = Expediente.objects.create(expediente_id=uuid.uuid4(), legal_entity=le, client=client, status="PRODUCCION", is_blocked=False)
    art = ArtifactInstance.objects.create(expediente=exp, artifact_type="ART-01", status="COMPLETED")
    
    url = reverse("expedientes:supersede-artifact", kwargs={"pk": str(exp.expediente_id), "artifact_id": str(art.artifact_id)})
    response = auth_client.post(url, {"payload": {"new": "data"}, "reason": "fix error"}, format="json")
    
    assert response.status_code == status.HTTP_201_CREATED
    exp.refresh_from_db()
    assert exp.is_blocked is True
    assert EventLog.objects.filter(event_type="BLOCKED_POR_CAMBIO_PRECONDICION", aggregate_id=str(exp.expediente_id)).exists()

@pytest.mark.django_db
def test_void_artifact_blocks_close_expediente(auth_client, make_entities):
    le, client = make_entities
    exp = Expediente.objects.create(expediente_id=uuid.uuid4(), legal_entity=le, client=client, status="EN_DESTINO")
    art_09 = ArtifactInstance.objects.create(expediente=exp, artifact_type="ART-09", status="COMPLETED")
    
    # Void the artifact
    url_void = reverse("expedientes:void-artifact", kwargs={"pk": str(exp.expediente_id), "artifact_id": str(art_09.artifact_id)})
    auth_client.post(url_void, {"reason": "test void"}, format="json")
    
    # Attempt C14 (Close Expediente) which requires ART-09 COMPLETED
    url_close = reverse("expedientes:close", kwargs={"pk": str(exp.expediente_id)})
    response = auth_client.post(url_close, {"payload": {}}, format="json")
    
    assert response.status_code == status.HTTP_409_CONFLICT
    assert "precondition" in str(response.data).lower() or "missing" in str(response.data).lower() or "artifact" in str(response.data).lower()
