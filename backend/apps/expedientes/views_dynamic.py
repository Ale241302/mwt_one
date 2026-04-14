import uuid
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from apps.expedientes.models import Expediente, ArtifactInstance, EventLog
from apps.expedientes.enums_exp import AggregateType

class GenericArtifactCreateView(APIView):
    """
    POST /api/expedientes/<pk>/artifacts/dynamic/
    Creates a new generic artifact for the given expediente.
    Expected payload: {"artifact_type": "ART-18", "payload": { ... }}
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        exp = get_object_or_404(Expediente, pk=pk)
        artifact_type = request.data.get("artifact_type")
        payload = request.data.get("payload", {})

        if not artifact_type:
            return Response({"detail": "Falta artifact_type"}, status=400)

        art = ArtifactInstance.objects.create(
            expediente=exp,
            artifact_type=str(artifact_type),  # Podría ser número (ID del builder) pero el modelo exige string
            status='COMPLETED',  # Asumimos estado final al crear generic
            payload=payload
        )

        EventLog.objects.create(
            aggregate_id=exp.expediente_id,
            aggregate_type=AggregateType.EXPEDIENTE,
            event_type='artifact_dynamics.created',
            emitted_by=request.user.email,
            payload={'artifact_id': str(art.artifact_id), 'artifact_type': art.artifact_type},
            occurred_at=timezone.now(),
            correlation_id=uuid.uuid4(),
        )

        return Response({
            "detail": "Created",
            "artifact_id": str(art.artifact_id)
        }, status=201)

class GenericArtifactUpdateView(APIView):
    """
    PUT /api/expedientes/<pk>/artifacts/dynamic/<artifact_id>/
    Updates the payload of an existing instance.
    Expected payload: {"payload": { ... }}
    """
    permission_classes = [IsAuthenticated]

    def put(self, request, pk, artifact_id):
        art = get_object_or_404(ArtifactInstance, pk=artifact_id, expediente_id=pk)
        payload = request.data.get("payload")

        if payload is not None:
            art.payload = payload
            art.save(update_fields=['payload'])

            EventLog.objects.create(
                aggregate_id=pk,
                aggregate_type=AggregateType.EXPEDIENTE,
                event_type='artifact_dynamics.updated',
                emitted_by=request.user.email,
                payload={'artifact_id': str(art.artifact_id), 'artifact_type': art.artifact_type},
                occurred_at=timezone.now(),
                correlation_id=uuid.uuid4(),
            )

        return Response({
            "detail": "Updated",
            "artifact_id": str(art.artifact_id)
        }, status=200)

