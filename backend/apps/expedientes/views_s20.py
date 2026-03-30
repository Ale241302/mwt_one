"""
S20-07 — ProformaCreateView
POST /api/expedientes/<pk>/artifacts/proforma/

Crea un ART-02 (Proforma) para un expediente, validando:
- Expediente en estado REGISTRO o PREPARACION
- mode válido para el brand (via BRAND_ALLOWED_MODES)
- payload validado por ART02PayloadSerializer
- Solo una proforma ACTIVE por mode por expediente (no duplicar)
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from apps.expedientes.models import Expediente, ArtifactInstance
from apps.expedientes.serializers_s20 import ART02PayloadSerializer
from apps.expedientes.services.artifact_policy import BRAND_ALLOWED_MODES


# Estados del expediente en que se permite crear una proforma
ALLOWED_STATES_FOR_PROFORMA = ('REGISTRO', 'PREPARACION')


class ProformaCreateView(APIView):
    """
    S20-07: POST /api/expedientes/<pk>/artifacts/proforma/

    Body:
        {
            "mode": "mode_b" | "mode_c" | "default",
            "operated_by": "...",       # opcional, default: muito_work_limitada
            "proforma_number": "..."    # opcional
        }

    Respuesta 201:
        {
            "artifact_id": "<uuid>",
            "artifact_type": "ART-02",
            "status": "PENDING",
            "mode": "mode_b",
            "expediente_id": "<uuid>"
        }
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        # 1. Obtener expediente
        try:
            exp = Expediente.objects.select_related('brand').get(pk=pk)
        except Expediente.DoesNotExist:
            return Response({'detail': 'Expediente no encontrado.'}, status=status.HTTP_404_NOT_FOUND)

        # 2. Verificar estado del expediente
        if exp.status not in ALLOWED_STATES_FOR_PROFORMA:
            return Response(
                {'detail': f'No se puede crear una proforma en estado {exp.status}. '
                            f'Estados permitidos: {ALLOWED_STATES_FOR_PROFORMA}'},
                status=status.HTTP_409_CONFLICT
            )

        # 3. Validar payload con ART02PayloadSerializer
        payload_serializer = ART02PayloadSerializer(data=request.data)
        if not payload_serializer.is_valid():
            return Response(payload_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        validated = payload_serializer.validated_data
        mode = validated['mode']

        # 4. Verificar que el mode es válido para el brand del expediente
        brand_slug = ''
        try:
            brand_slug = exp.brand.slug
        except Exception:
            pass

        allowed_modes = BRAND_ALLOWED_MODES.get(brand_slug, ('mode_b', 'mode_c', 'default'))
        if mode not in allowed_modes:
            return Response(
                {'detail': f'El mode "{mode}" no está permitido para la marca "{brand_slug}". '
                            f'Modos permitidos: {allowed_modes}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 5. Verificar duplicado: no crear dos proformas PENDING/COMPLETED con el mismo mode
        existing = ArtifactInstance.objects.filter(
            expediente=exp,
            artifact_type='ART-02',
            status__in=['PENDING', 'COMPLETED'],
        ).filter(payload__mode=mode).first()

        if existing:
            return Response(
                {'detail': f'Ya existe una proforma activa con mode="{mode}" '
                            f'para este expediente (artifact_id={existing.artifact_id}).'},
                status=status.HTTP_409_CONFLICT
            )

        # 6. Crear el ArtifactInstance ART-02
        artifact = ArtifactInstance.objects.create(
            expediente=exp,
            artifact_type='ART-02',
            status='PENDING',
            payload={
                'mode': mode,
                'operated_by': validated.get('operated_by', 'muito_work_limitada'),
                'proforma_number': validated.get('proforma_number', ''),
            },
            created_by=request.user.email if request.user else 'system',
        )

        return Response(
            {
                'artifact_id': str(artifact.artifact_id),
                'artifact_type': artifact.artifact_type,
                'status': artifact.status,
                'mode': mode,
                'expediente_id': str(exp.expediente_id),
            },
            status=status.HTTP_201_CREATED
        )
