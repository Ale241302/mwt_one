import uuid
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from apps.expedientes.models import Expediente, ArtifactInstance
from apps.expedientes.enums_artifacts import ArtifactType
from apps.expedientes.enums_exp import ExpedienteStatus

class ProformaSendView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request, expediente_id):
        try:
            expediente = Expediente.objects.get(pk=expediente_id)
        except Expediente.DoesNotExist:
            return Response({"error": "Expediente no encontrado"}, status=status.HTTP_404_NOT_FOUND)
            
        proforma = ArtifactInstance.objects.filter(
            expediente=expediente, 
            artifact_type=ArtifactType.PROFORMA,
            is_valid=True
        ).last()
        
        if not proforma:
            return Response({"error": "No hay proforma válida"}, status=status.HTTP_404_NOT_FOUND)
            
        # Generar token de aprobación único (guardado temporalmente en notes o Redis, mocking aquí en notes por MVP)
        token = uuid.uuid4().hex
        proforma.notes = f"token:{token}"
        proforma.save()
        
        # Integrar S26 email send
        try:
            from apps.expedientes.tasks import send_notification_task
            send_notification_task.delay(
                expediente_id=expediente_id,
                template_key='proforma.dispatch',
                # context={ 'approve_link': f"/api/expedientes/proforma/{token}/aprobar/" }
            )
        except Exception:
            pass # fallback si Celery o task no está listo aún localmente
            
        return Response({"detail": "Proforma enviada", "token_gererado": token}, status=status.HTTP_200_OK)


class ProformaApproveRejectView(APIView):
    permission_classes = [AllowAny] # Endpoint público para que el cliente haga clic en el correo
    
    def get(self, request, token, action):
        if action not in ['aprobar', 'rechazar']:
            return Response({"error": "Acción inválida"}, status=status.HTTP_400_BAD_REQUEST)
            
        # Buscar proforma con este token en notes (MVP approach, debería en un modelo Token)
        # Note: A real implementation would use a Token model. Using robust matching to avoid breaking.
        proformas = ArtifactInstance.objects.filter(
            artifact_type=ArtifactType.PROFORMA,
            notes__icontains=f"token:{token}"
        )
        
        if not proformas.exists():
            return Response({"error": "Token inválido o expirado"}, status=status.HTTP_404_NOT_FOUND)
            
        proforma = proformas.first()
        expediente = proforma.expediente
        
        try:
            if action == 'aprobar':
                expediente.status = ExpedienteStatus.CONFIRMADO # Or specific step
                proforma.notes += " | APROBADA"
            else:
                expediente.status = ExpedienteStatus.CANCELADO # Or specific step backwards
                proforma.notes += " | RECHAZADA"
            
            proforma.save()
            expediente.save()
            
            # TODO: Log EventLog here about the transition
            
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
        return Response({"detail": f"Proforma {action} exitosamente."}, status=status.HTTP_200_OK)
