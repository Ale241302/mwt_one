from rest_framework import serializers
from .models import SizeSystem, SizeDimension, SizeEntry, SizeEquivalence


class SizeDimensionSerializer(serializers.ModelSerializer):
    class Meta:
        model = SizeDimension
        fields = ['id', 'code', 'display_name', 'unit', 'display_order', 'is_primary']


class SizeEquivalenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = SizeEquivalence
        fields = ['standard_system', 'value', 'display_order', 'is_primary']


class SizeEntrySerializer(serializers.ModelSerializer):
    equivalences = SizeEquivalenceSerializer(many=True, read_only=True)

    class Meta:
        model = SizeEntry
        fields = ['id', 'label', 'display_order', 'is_active', 'equivalences']


class SizeSystemSerializer(serializers.ModelSerializer):
    dimensions = SizeDimensionSerializer(many=True, read_only=True)
    entries = SizeEntrySerializer(many=True, read_only=True)

    class Meta:
        model = SizeSystem
        fields = ['id', 'code', 'category', 'description', 'is_active', 'dimensions', 'entries']
