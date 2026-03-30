"""S20 Serializers — validación de ART-02 (mode requerido, S20-04) y ART-05 (linked_proformas, S20-03)."""
from rest_framework import serializers
from .models import ArtifactInstance


# Valores válidos para mode en ART-02 (S20-04)
VALID_MODES = ('mode_b', 'mode_c', 'default')


class ART02PayloadSerializer(serializers.Serializer):
    """
    S20-04: Valida el payload de ART-02 (Proforma).
    - mode es REQUERIDO
    - operated_by siempre presente (default 'muito_work_limitada')
    - NO almacena 'lines' — la relación línea→proforma vive en EPL.proforma FK
    """
    mode = serializers.ChoiceField(
        choices=VALID_MODES,
        error_messages={
            'required': 'El campo mode es requerido para ART-02.',
            'invalid_choice': 'mode debe ser uno de: mode_b, mode_c, default. Recibido: {input}'
        }
    )
    operated_by = serializers.CharField(
        default='muito_work_limitada',
        required=False,
        max_length=100,
        help_text='Siempre presente para trazabilidad. Default: muito_work_limitada'
    )
    proforma_number = serializers.CharField(required=False, allow_blank=True, max_length=100)

    def validate(self, data):
        # Asegurar operated_by siempre presente
        if not data.get('operated_by'):
            data['operated_by'] = 'muito_work_limitada'
        # S20-04: ART-02 NO debe almacenar 'lines'
        if 'lines' in self.initial_data:
            raise serializers.ValidationError(
                {'lines': 'ART-02 no acepta campo lines en el payload. '
                           'La relación línea→proforma se gestiona via EPL.proforma FK (S20-01).'}
            )
        return data


class ART05PayloadSerializer(serializers.Serializer):
    """
    S20-03: Valida el payload de ART-05 (Embarque).
    - parent_proforma_id: FK a la proforma principal (ART-02)
    - linked_proformas: array de IDs de ART-02 adicionales
    - Todos los IDs deben ser ART-02 del mismo expediente
    - parent_proforma_id debe estar en linked_proformas
    """
    parent_proforma_id = serializers.UUIDField(
        required=False,
        allow_null=True,
        help_text='UUID del ArtifactInstance ART-02 principal'
    )
    linked_proformas = serializers.ListField(
        child=serializers.UUIDField(),
        required=False,
        default=list,
        help_text='Lista de UUIDs de ART-02 adicionales vinculados a este embarque'
    )

    def validate(self, data):
        parent_id = data.get('parent_proforma_id')
        linked = data.get('linked_proformas', [])

        # Si hay parent_proforma, debe estar en linked_proformas
        if parent_id and linked:
            if str(parent_id) not in [str(x) for x in linked]:
                raise serializers.ValidationError(
                    {'parent_proforma_id': 'parent_proforma_id debe ser uno de los IDs en linked_proformas.'}
                )
        return data

    def validate_linked_proformas_against_expediente(self, linked_ids, expediente):
        """
        Validación externa: llamar desde la view/service con el expediente ya cargado.
        Verifica que todos los IDs en linked_proformas son ART-02 del mismo expediente.
        Retorna lista de ArtifactInstances válidos.
        """
        if not linked_ids:
            return []

        valid_proformas = ArtifactInstance.objects.filter(
            artifact_id__in=linked_ids,
            artifact_type='ART-02',
            expediente=expediente,
        )
        valid_ids = set(str(p.artifact_id) for p in valid_proformas)
        requested_ids = set(str(i) for i in linked_ids)
        invalid_ids = requested_ids - valid_ids

        if invalid_ids:
            raise serializers.ValidationError(
                {'linked_proformas': f'Los siguientes IDs no son ART-02 válidos del expediente: {list(invalid_ids)}'}
            )
        return list(valid_proformas)
