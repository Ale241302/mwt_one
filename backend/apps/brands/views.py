from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import Brand
from .serializers import BrandSerializer


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def brand_list_create(request):
    if request.method == 'GET':
        qs = Brand.objects.all().order_by('name')
        data = BrandSerializer(qs, many=True).data
        return Response({'results': data, 'count': len(data)})

    ser = BrandSerializer(data=request.data)
    if ser.is_valid():
        ser.save()
        return Response(ser.data, status=status.HTTP_201_CREATED)
    return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def brand_detail(request, slug):
    try:
        brand = Brand.objects.get(slug=slug)
    except Brand.DoesNotExist:
        return Response({'detail': 'No encontrado.'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        return Response(BrandSerializer(brand).data)

    if request.method in ('PUT', 'PATCH'):
        ser = BrandSerializer(brand, data=request.data, partial=(request.method == 'PATCH'))
        if ser.is_valid():
            ser.save()
            return Response(ser.data)
        return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)

    brand.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)
