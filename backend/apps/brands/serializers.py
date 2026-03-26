from django.utils.text import slugify
from rest_framework import serializers
from .models import Brand, BrandSKU


class SKUSerializer(serializers.ModelSerializer):
    class Meta:
        model = BrandSKU
        fields = ['product_key', 'arch', 'size', 'sku_code']


class BrandSerializer(serializers.ModelSerializer):
    # Frontend sends 'code' but we don't store it — accept and ignore
    code = serializers.CharField(required=False, write_only=True, allow_blank=True)
    markets = serializers.SerializerMethodField()
    expedientes_count = serializers.SerializerMethodField()

    class Meta:
        model = Brand
        fields = ['slug', 'name', 'brand_type', 'code', 'is_active', 'markets', 'expedientes_count']
        extra_kwargs = {
            'slug': {'required': False},
        }

    def get_markets(self, obj):
        return []

    def get_expedientes_count(self, obj):
        return 0

    def validate(self, attrs):
        attrs.pop('code', None)
        if not attrs.get('slug') and attrs.get('name'):
            attrs['slug'] = slugify(attrs['name'])[:50]
        return attrs
