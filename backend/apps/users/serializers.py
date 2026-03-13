from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.exceptions import AuthenticationFailed


class MWTTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Sprint 8 S8-03: Extiende JWT con role, legal_entity_id y permissions[].
    Guardia is_api_user: si False → 401 AuthenticationFailed.
    NO crea nuevo endpoint — extiende el existente de Sprint 0.
    """

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)  # incluye user_id de Sprint 0
        token['role'] = user.role
        token['legal_entity_id'] = user.legal_entity_id  # puede ser None
        token['permissions'] = list(
            user.permissions_set.values_list('permission', flat=True)
        )
        return token

    def validate(self, attrs):
        data = super().validate(attrs)  # autenticación estándar primero
        user = self.user
        if not user.is_api_user:
            raise AuthenticationFailed(
                detail='Acceso API no habilitado para este usuario.',
                code='is_api_user_false',
            )
        return data
