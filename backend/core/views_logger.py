from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

class FrontendLoggerView(APIView):
    """
    Simulated endpoint for frontend logs.
    POST /api/logs/
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        level = request.data.get('level', 'INFO')
        message = request.data.get('message', '')
        context = request.data.get('context', {})
        
        # In a real app, this would go to Sentry, ELK, etc.
        # For now, we simulate by printing to stdout.
        print(f"[FRONTEND {level}] {message} | Context: {context}")
        
        return Response({'status': 'ok'})
