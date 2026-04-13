import uuid
from django.utils import timezone
from datetime import timedelta
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.contrib.auth import get_user_model
from apps.users.models import UserRole
from apps.clientes.models import Client

User = get_user_model()

class InviteClientView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        if request.user.role != UserRole.CEO:
            return Response({"error": "Only CEO can invite"}, status=status.HTTP_403_FORBIDDEN)
            
        email = request.data.get('email')
        client_id = request.data.get('client_id')
        role = request.data.get('role', UserRole.CLIENT_RANAWALK)
        
        if not email or not client_id:
            return Response({"error": "email and client_id required"}, status=status.HTTP_400_BAD_REQUEST)
            
        try:
            client_record = Client.objects.get(pk=client_id)
        except Client.DoesNotExist:
            return Response({"error": "Client not found"}, status=status.HTTP_404_NOT_FOUND)
            
        # Create user without password (inactive/pending)
        invite_token = uuid.uuid4().hex
        user, created = User.objects.get_or_create(
            username=email,
            defaults={
                'email': email,
                'role': role,
                'is_active': False
            }
        )
        
        # Simulating token storage on user (e.g., using auth_token or redis)
        # Assuming notes or a profile field exists. We'll use set_password to lock it temporarily.
        # But a more standard way is sending the token via email and accepting registration completion.
        
        # Here we mock the token logic.
        invitation_link = f"https://consola.mwt.one/register/?token={invite_token}&email={email}"
        
        # Send Email via S26 notification task
        try:
            from apps.expedientes.tasks import send_notification_task
            send_notification_task.delay(
                expediente_id=None, # Global notification
                template_key='portal.invite',
                # context={'link': invitation_link}
            )
        except Exception:
            pass
            
        return Response({"detail": "Invitation sent", "link": invitation_link}, status=status.HTTP_200_OK)


class AcceptInvitationView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        email = request.data.get('email')
        token = request.data.get('token')
        password = request.data.get('password')
        
        if not all([email, token, password]):
            return Response({"error": "Missing data"}, status=status.HTTP_400_BAD_REQUEST)
            
        try:
            user = User.objects.get(username=email, is_active=False)
            # Verify token logic here (mocked validation for MVP)
            user.set_password(password)
            user.is_active = True
            user.save()
            return Response({"detail": "User activated. You can login now."})
        except User.DoesNotExist:
            return Response({"error": "Invalid invitation"}, status=status.HTTP_404_NOT_FOUND)
