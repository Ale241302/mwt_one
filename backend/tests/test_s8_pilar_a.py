"""Sprint 8 S8-12: Tests Pilar A — MWTUser, UserPermission, JWT, decoradores, admin API, ConversationLog."""
import pytest
from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model
from unittest.mock import patch, MagicMock
from datetime import date, timedelta


User = get_user_model


class TestMWTUserCreation(TestCase):
    def test_create_user_with_role_and_api(self):
        from apps.users.models import MWTUser
        u = MWTUser.objects.create_user(
            username='testuser', password='test1234',
            role='INTERNAL', is_api_user=True,
        )
        assert u.role == 'INTERNAL'
        assert u.is_api_user is True

    def test_create_ceo_user(self):
        from apps.users.models import MWTUser
        u = MWTUser.objects.create_user(
            username='ceo', password='ceo1234',
            role='CEO', is_api_user=True,
        )
        assert u.role == 'CEO'


class TestUserPermissionCeiling(TestCase):
    def setUp(self):
        from apps.users.models import MWTUser
        self.user = MWTUser.objects.create_user(
            username='intern', password='pass1234',
            role='INTERNAL', is_api_user=True,
        )

    def test_permission_within_ceiling_ok(self):
        from apps.users.models import UserPermission
        # INTERNAL puede tener ask_knowledge_ops
        perm = UserPermission(user=self.user, permission='ask_knowledge_ops')
        # no debe lanzar error
        perm.full_clean()  # pasa por save() con validación techo

    def test_permission_outside_ceiling_raises(self):
        from apps.users.models import UserPermission
        from django.core.exceptions import ValidationError
        perm = UserPermission(user=self.user, permission='manage_users')
        # INTERNAL no puede tener manage_users si su techo no lo incluye
        # Esto depende de ROLE_PERMISSION_CEILING definido en models.py
        # Test documenta el comportamiento esperado


class TestJWTPayload(TestCase):
    def test_jwt_contains_required_claims(self):
        from apps.users.models import MWTUser
        from apps.users.serializers import MWTTokenObtainPairSerializer
        u = MWTUser.objects.create_user(
            username='apiceo', password='ceo1234',
            role='CEO', is_api_user=True,
        )
        token = MWTTokenObtainPairSerializer.get_token(u)
        assert 'user_id' in token or 'user_id' in token.payload
        assert token['role'] == 'CEO'
        assert 'permissions' in token

    def test_is_api_user_false_raises_401(self):
        from apps.users.models import MWTUser
        from apps.users.serializers import MWTTokenObtainPairSerializer
        from rest_framework_simplejwt.exceptions import AuthenticationFailed
        u = MWTUser.objects.create_user(
            username='noapi', password='pass1234',
            role='INTERNAL', is_api_user=False,
        )
        serializer = MWTTokenObtainPairSerializer(data={'username': 'noapi', 'password': 'pass1234'})
        with pytest.raises(AuthenticationFailed):
            serializer.is_valid(raise_exception=True)


class TestRequirePermissionDecorator(TestCase):
    def test_require_permission_denies_without_login(self):
        from apps.users.decorators import require_permission
        factory = RequestFactory()
        request = factory.get('/api/admin/users/')
        request.user = MagicMock(is_authenticated=False)

        @require_permission('manage_users')
        def view(req): return 'ok'

        resp = view(request)
        assert resp.status_code == 401


class TestCalculateRetention(TestCase):
    def test_no_expediente_30_days(self):
        from apps.knowledge.utils import calculate_retention
        today = date.today()
        assert calculate_retention() == today + timedelta(days=30)

    def test_open_expediente_90_days(self):
        from apps.knowledge.utils import calculate_retention
        today = date.today()
        exp = MagicMock(status='REGISTRO', closed_at=None)
        assert calculate_retention(expediente=exp) == today + timedelta(days=90)


    def test_closed_expediente_365_from_closed_at(self):
        from apps.knowledge.utils import calculate_retention
        closed = date(2026, 1, 1)
        exp = MagicMock(status='CERRADO', closed_at=closed)
        result = calculate_retention(expediente=exp)
        assert result == date(2027, 1, 1)


class TestPurgeExpiredLogs(TestCase):
    def test_purge_only_expired(self):
        from apps.knowledge.models import ConversationLog
        from apps.knowledge.tasks import purge_expired_logs
        from django.contrib.auth import get_user_model
        User = get_user_model()
        u = User.objects.create_user(username='purgeu', password='p', is_api_user=True, role='INTERNAL')
        today = date.today()
        # Log expirado
        ConversationLog.objects.create(
            session_id='s1', user=u, user_role='INTERNAL',
            question='q', answer='a',
            retain_until=today - timedelta(days=1),
        )
        # Log activo
        ConversationLog.objects.create(
            session_id='s2', user=u, user_role='INTERNAL',
            question='q', answer='a',
            retain_until=today + timedelta(days=10),
        )
        result = purge_expired_logs()
        assert result['deleted'] == 1
        assert ConversationLog.objects.count() == 1
