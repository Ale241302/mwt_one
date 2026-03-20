from rest_framework import serializers
from apps.qr.models import QRRoute, QRScan

class QRRouteSerializer(serializers.ModelSerializer):
    class Meta:
        model = QRRoute
        fields = '__all__'

class QRScanSerializer(serializers.ModelSerializer):
    class Meta:
        model = QRScan
        fields = '__all__'
