from rest_framework import serializers
from django.contrib.auth import get_user_model
from apps.core.models import LegalEntity

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    role = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'role']

    def get_role(self, obj):
        return 'CEO' if obj.is_superuser else 'User'


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()


class LegalEntitySerializer(serializers.ModelSerializer):
    # Frontend expects 'name' field (maps to legal_name)
    name = serializers.CharField(source='legal_name')

    class Meta:
        model = LegalEntity
        fields = ['id', 'name', 'entity_id', 'country', 'role', 'status']
