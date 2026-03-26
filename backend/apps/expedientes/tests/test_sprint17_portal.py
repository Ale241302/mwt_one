"""
S17-14: Tests for Sprint 17 Portal B2B security.
New file — does NOT modify existing tests.
"""
from django.test import TestCase, RequestFactory
from unittest.mock import MagicMock, patch


class TestPortalTenantIsolation(TestCase):
    """
    S17-04: Portal endpoints must enforce strict tenant isolation.
    Tests use mock objects to avoid DB dependency.
    """

    def setUp(self):
        self.factory = RequestFactory()

    def test_get_expediente_for_user_returns_none_for_wrong_tenant(self):
        """
        _get_expediente_for_user must return None when exp.client != user.legal_entity.
        Same 404 must be returned whether exp doesn't exist or belongs to another tenant.
        """
        from apps.expedientes.views_portal import _get_expediente_for_user

        mock_exp = MagicMock()
        mock_exp.client = MagicMock()
        mock_user = MagicMock()
        # Different legal_entity than exp.client
        mock_user.legal_entity = MagicMock()

        with patch('apps.expedientes.views_portal.Expediente.objects.get', return_value=mock_exp):
            result = _get_expediente_for_user('some-pk', mock_user)
            self.assertIsNone(result, "Cross-tenant access must return None")

    def test_get_expediente_for_user_returns_none_when_not_exists(self):
        """Non-existent expediente must return None (same as cross-tenant)."""
        from apps.expedientes.views_portal import _get_expediente_for_user
        from apps.expedientes.models import Expediente

        mock_user = MagicMock()
        with patch('apps.expedientes.views_portal.Expediente.objects.get',
                   side_effect=Expediente.DoesNotExist):
            result = _get_expediente_for_user('nonexistent-pk', mock_user)
            self.assertIsNone(result)

    def test_portal_detail_view_returns_404_for_cross_tenant(self):
        """PortalExpedienteDetailView must return 404 for cross-tenant access."""
        from apps.expedientes.views_portal import PortalExpedienteDetailView

        request = self.factory.get('/api/portal/expedientes/fake-pk/')
        request.user = MagicMock()
        request.user.is_authenticated = True

        view = PortalExpedienteDetailView.as_view()
        with patch('apps.expedientes.views_portal._get_expediente_for_user', return_value=None):
            response = view(request, pk='fake-pk')
            self.assertEqual(response.status_code, 404)

    def test_portal_artifacts_view_returns_404_for_cross_tenant(self):
        """PortalExpedienteArtifactsView must return 404 for cross-tenant access."""
        from apps.expedientes.views_portal import PortalExpedienteArtifactsView

        request = self.factory.get('/api/portal/expedientes/fake-pk/artifacts/')
        request.user = MagicMock()
        request.user.is_authenticated = True

        view = PortalExpedienteArtifactsView.as_view()
        with patch('apps.expedientes.views_portal._get_expediente_for_user', return_value=None):
            response = view(request, pk='fake-pk')
            self.assertEqual(response.status_code, 404)

    def test_detail_404_and_cross_tenant_404_same_body(self):
        """
        Uniform 404 — both not-found and cross-tenant must return {'detail': 'Not found.'}
        This prevents tenant enumeration attacks.
        """
        import json
        from apps.expedientes.views_portal import PortalExpedienteDetailView

        request = self.factory.get('/api/portal/expedientes/fake-pk/')
        request.user = MagicMock()
        request.user.is_authenticated = True

        view = PortalExpedienteDetailView.as_view()
        with patch('apps.expedientes.views_portal._get_expediente_for_user', return_value=None):
            response = view(request, pk='fake-pk')
            self.assertEqual(response.status_code, 404)
            self.assertEqual(response.data.get('detail'), 'Not found.')


class TestPortalSerializerExcludesCEOFields(TestCase):
    """
    S17-04: Portal serializers must exclude CEO-ONLY fields.
    """

    def test_list_serializer_does_not_expose_ceo_fields(self):
        from apps.expedientes.serializers_portal import PortalExpedienteListSerializer
        fields = PortalExpedienteListSerializer.Meta.fields
        ceo_only = ['fob_unit', 'margin_pct', 'commission_pct', 'landed_cost', 'dai_amount']
        for f in ceo_only:
            self.assertNotIn(f, fields, f"'{f}' must NOT be in portal list serializer")

    def test_detail_serializer_does_not_expose_ceo_fields(self):
        from apps.expedientes.serializers_portal import PortalExpedienteDetailSerializer
        fields = PortalExpedienteDetailSerializer.Meta.fields
        ceo_only = ['fob_unit', 'margin_pct', 'commission_pct', 'landed_cost', 'dai_amount']
        for f in ceo_only:
            self.assertNotIn(f, fields, f"'{f}' must NOT be in portal detail serializer")
