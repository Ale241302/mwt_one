from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from apps.transfers.models import Transfer
from apps.nodos.models import Node
from apps.transfers.serializers import TransferListSerializer, NodeSerializer


class TransfersUIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # El filtro 'estado' del frontend viene en minusc. (planned, in_transit, etc.)
        estado = request.query_params.get('estado', '').strip().lower()
        qs = (
            Transfer.objects.all()
            .order_by('-created_at')
        )
        if estado and estado != 'todos':
            qs = qs.filter(status=estado)

        from core.pagination import StandardPagination
        paginator = StandardPagination()
        page = paginator.paginate_queryset(qs, request)
        
        nodes = (
            Node.objects
            .filter(status='active')
            .order_by('name')
        )
        return paginator.get_paginated_response({
            'transfers': TransferListSerializer(page, many=True).data,
            'nodes': NodeSerializer(nodes, many=True).data,
        })
