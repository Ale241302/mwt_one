from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from .models import Brand
from .serializers import BrandSerializer


class BrandListView(generics.ListCreateAPIView):
    queryset = Brand.objects.all()
    serializer_class = BrandSerializer
    permission_classes = [IsAuthenticated]
