from rest_framework import serializers
from .models import Product
from apps.brands.serializers import BrandSerializer

class ProductSerializer(serializers.ModelSerializer):
    brand_name = serializers.ReadOnlyField(source='brand.name')
    
    class Meta:
        model = Product
        fields = ['id', 'name', 'sku_base', 'brand_id', 'brand_name', 'category', 'description', 'created_at', 'updated_at']
