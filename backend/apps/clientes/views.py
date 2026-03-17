from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.clientes.models import Cliente
from apps.clientes.serializers import ClienteSerializer


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def clientes_list_create(request):
    if request.method == 'GET':
        qs = Cliente.objects.select_related('legal_entity').order_by('name')
        data = ClienteSerializer(qs, many=True).data
        return Response({'results': data, 'count': len(data)})

    ser = ClienteSerializer(data=request.data)
    if ser.is_valid():
        ser.save()
        return Response(ser.data, status=status.HTTP_201_CREATED)
    return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def clientes_detail(request, pk):
    try:
3        cliente = Cliente.objects.select_related('legal_entity').get(pk=pk)
    except Cliente.DoesNotExist:
        return Response({'detail': 'No encontrado.'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        return Response(ClienteSerializer(cliente).data)

    if request.method in ('PUT', 'PATCH'):
        ser = ClienteSerializer(cliente, data=request.data, partial=(request.method == 'PATCH'))
        if ser.is_valid():
            ser.save()
            return Response(ser.data)
        return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)

    cliente.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)
