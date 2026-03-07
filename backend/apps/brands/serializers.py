from rest_framework import serializers
from .models import Brand, BrandSKU

class SKUSerializer(serializers.ModelSerializer):
    class Meta:
        model = BrandSKU
        fields = ['product_key', 'arch', 'size', 'sku_code']

class BrandSerializer(serializers.ModelSerializer):
    class Meta:
        model = Brand
        fields = ['slug', 'name', 'brand_type', 'is_active']
