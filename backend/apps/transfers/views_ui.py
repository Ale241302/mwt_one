from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from apps.transfers.models import Transfer, Node
from apps.transfers.serializers import TransferListSerializer, NodeSerializer


class TransfersUIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # El filtro 'estado' del frontend viene en minusc. (planned, in_transit, etc.)
        estado = request.query_params.get('estado', '').strip().lower()
        qs = (
            Transfer.objects
            .select_related(
                'from_node', 'to_node',
                'from_node__legal_entity',
                'to_node__legal_entity',
            )
            .order_by('-created_at')
        )
        if estado and estado != 'todos':
            qs = qs.filter(status=estado)

        transfers = qs[:100]
        nodes = (
            Node.objects
            .select_related('legal_entity')
            .filter(status='active')
            .order_by('name')
        )
        return Response({
            'transfers': TransferListSerializer(transfers, many=True).data,
            'nodes': NodeSerializer(nodes, many=True).data,
        })
