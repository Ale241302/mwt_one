from rest_framework import serializers
from .models import Producto
from apps.brands.serializers import BrandSerializer

class ProductoSerializer(serializers.ModelSerializer):
    brand_name = serializers.ReadOnlyField(source='brand.name')
    
    class Meta:
        model = Producto
        fields = ['id', 'name', 'sku_base', 'brand', 'brand_name', 'category', 'description', 'created_at', 'updated_at']
