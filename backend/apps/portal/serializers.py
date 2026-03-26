from rest_framework import serializers
from apps.expedientes.models import Expediente, ArtifactInstance

class ExpedientePortalSerializer(serializers.ModelSerializer):
    brand_name = serializers.ReadOnlyField(source='brand.name')
    
    class Meta:
        model = Expediente
        fields = [
            'expediente_id', 'brand', 'brand_name', 'status', 
            'created_at', 'updated_at'
        ]

class ArtifactPortalSerializer(serializers.ModelSerializer):
    class Meta:
        model = ArtifactInstance
        fields = ['artifact_id', 'artifact_type', 'status', 'created_at', 'updated_at']
