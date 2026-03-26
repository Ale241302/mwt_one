from rest_framework import serializers
from .models import Supplier, SupplierContact, SupplierPerformanceKPI
from apps.agreements.models import BrandSupplierAgreement


class BrandSupplierAgreementSerializer(serializers.ModelSerializer):
    brand_name = serializers.CharField(source='brand.name', read_only=True)

    class Meta:
        model = BrandSupplierAgreement
        fields = ['id', 'brand', 'brand_name', 'version', 'valid_daterange', 'status']


class SupplierContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = SupplierContact
        fields = '__all__'


class SupplierPerformanceKPISerializer(serializers.ModelSerializer):
    class Meta:
        model = SupplierPerformanceKPI
        fields = '__all__'


class SupplierSerializer(serializers.ModelSerializer):
    primary_contact = serializers.SerializerMethodField()
    latest_rating = serializers.SerializerMethodField()
    active_agreements_count = serializers.SerializerMethodField()

    class Meta:
        model = Supplier
        fields = [
            'id', 'name', 'tax_id', 'country', 'address', 'website',
            'is_active', 'primary_contact', 'latest_rating', 
            'active_agreements_count', 'created_at'
        ]

    def get_primary_contact(self, obj):
        contact = obj.contacts.filter(is_primary=True).first()
        if contact:
            return SupplierContactSerializer(contact).data
        return None

    def get_latest_rating(self, obj):
        kpi = obj.performance_kpis.order_by('-year', '-month').first()
        if kpi:
            return float(kpi.on_time_delivery_score)
        return None

    def get_active_agreements_count(self, obj):
        return BrandSupplierAgreement.objects.filter(supplier_id=obj.id, status='active').count()
