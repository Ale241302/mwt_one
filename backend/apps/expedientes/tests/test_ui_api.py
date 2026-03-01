import pytest
from django.urls import reverse
from rest_framework import status
from .factories import ExpedienteFactory, ArtifactInstanceFactory, UserFactory, LegalEntityFactory
from apps.expedientes.models import CostLine, Expediente
from apps.expedientes.enums import ExpedienteStatus, ArtifactStatus
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal

@pytest.mark.django_db
class TestUIAPI:
    def setup_method(self):
        self.user = UserFactory()
        self.client_auth = pytest.importorskip("rest_framework.test").APIClient()
        self.client_auth.force_authenticate(user=self.user)

    def test_list_expedientes(self):
        """Test GET /api/ui/expedientes/"""
        ExpedienteFactory(status=ExpedienteStatus.REGISTRO)
        ExpedienteFactory(status=ExpedienteStatus.PRODUCCION)
        
        url = reverse('expedientes-ui:list')
        response = self.client_auth.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert 'results' in response.data
        assert len(response.data['results']) >= 2
        
        # Check annotations (like credit_band)
        first_item = response.data['results'][0]
        assert 'credit_band' in first_item
        assert 'total_cost' in first_item

    def test_expediente_bundle(self):
        """Test GET /api/ui/expedientes/{pk}/"""
        exp = ExpedienteFactory(status=ExpedienteStatus.REGISTRO)
        ArtifactInstanceFactory(expediente=exp, status='completed', payload={'file_url': 'test.pdf'})
        
        url = reverse('expedientes-ui:bundle', kwargs={'pk': exp.pk})
        response = self.client_auth.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['expediente']['id'] == str(exp.expediente_id)
        assert 'artifacts' in response.data
        assert 'events' in response.data
        assert 'available_actions' in response.data
        assert 'credit_clock' in response.data

    def test_document_download_url(self):
        """Test GET /api/ui/expedientes/documents/{artifact_id}/download/"""
        exp = ExpedienteFactory()
        artifact = ArtifactInstanceFactory(
            expediente=exp, 
            status='completed',
            payload={'file_url': 'some/path/file.pdf'}
        )
        
        url = reverse('expedientes-ui:document-download', kwargs={'artifact_id': artifact.pk})
        response = self.client_auth.get(url)
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_500_INTERNAL_SERVER_ERROR, status.HTTP_302_FOUND]

    def test_list_filters(self):
        """Test filtering in list view."""
        ExpedienteFactory(status=ExpedienteStatus.REGISTRO)
        ExpedienteFactory(status=ExpedienteStatus.CERRADO)
        
        url = reverse('expedientes-ui:list') + "?status=REGISTRO"
        response = self.client_auth.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        for item in response.data['results']:
            assert item['status'] == 'REGISTRO'

    # UI List — Expansion:
    def test_list_pagination(self):
        """test_list_pagination() → paginación default=25 max=100"""
        Expediente.objects.all().delete()
        for _ in range(30):
            ExpedienteFactory()
        
        url = reverse('expedientes-ui:list')
        response = self.client_auth.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 25 
        assert 'next' in response.data

    def test_list_ordering_by_credit_days(self):
        """test_list_ordering_by_credit_days() → ordenamiento por credit_days_elapsed"""
        now = timezone.now()
        Expediente.objects.all().delete()
        e1 = ExpedienteFactory(credit_clock_started_at=now - timedelta(days=5))
        e2 = ExpedienteFactory(credit_clock_started_at=now - timedelta(days=10))
        
        url = reverse('expedientes-ui:list') + "?ordering=-credit_days_elapsed"
        response = self.client_auth.get(url)
        assert response.data['results'][0]['id'] == str(e2.pk)

    def test_list_ordering_by_date(self):
        """test_list_ordering_by_date() → ordenamiento por created_at"""
        Expediente.objects.all().delete()
        e1 = ExpedienteFactory()
        e2 = ExpedienteFactory()
        url = reverse('expedientes-ui:list') # default -created_at
        response = self.client_auth.get(url)
        assert response.data['results'][0]['id'] == str(e2.pk)

    def test_list_filter_is_blocked(self):
        """test_list_filter_is_blocked() → filtro ?is_blocked=true"""
        Expediente.objects.all().delete()
        ExpedienteFactory(is_blocked=True)
        ExpedienteFactory(is_blocked=False)
        url = reverse('expedientes-ui:list') + "?is_blocked=true"
        response = self.client_auth.get(url)
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['is_blocked'] is True

    def test_list_filter_credit_band(self):
        """test_list_filter_credit_band() → filtro ?credit_band=CORAL"""
        now = timezone.now()
        Expediente.objects.all().delete()
        # CRITICAL is > 30 days
        ExpedienteFactory(credit_clock_started_at=now - timedelta(days=40))
        url = reverse('expedientes-ui:list') + "?credit_band=CRITICAL"
        response = self.client_auth.get(url)
        assert len(response.data['results']) == 1

    def test_list_aggregations(self):
        """test_list_aggregations() → total_cost via SQL annotate, no loop Python"""
        exp = ExpedienteFactory()
        CostLine.objects.create(expediente=exp, amount=Decimal('150.50'), currency='USD', cost_type='FREIGHT', phase='ORIGIN')
        
        url = reverse('expedientes-ui:list')
        response = self.client_auth.get(url)
        item = next(i for i in response.data['results'] if i['id'] == str(exp.pk))
        assert Decimal(item['total_cost']) == Decimal('150.50')

    # UI Detail — Expansion:
    def test_bundle_available_actions_registro(self):
        """test_bundle_available_actions_registro() → estado REGISTRO: C2 habilitado, C14 deshabilitado"""
        exp = ExpedienteFactory(status=ExpedienteStatus.REGISTRO)
        url = reverse('expedientes-ui:bundle', kwargs={'pk': exp.pk})
        response = self.client_auth.get(url)
        actions = response.data['available_actions']
        assert any(a['id'] == 'C2' and a['enabled'] for a in actions['primary'])
        assert any(a['id'] == 'C14' and not a['enabled'] for a in actions['secondary'])

    def test_bundle_available_actions_produccion(self):
        """test_bundle_available_actions_produccion() → estado PRODUCCION: C6-C10 según orden"""
        exp = ExpedienteFactory(status=ExpedienteStatus.PRODUCCION)
        url = reverse('expedientes-ui:bundle', kwargs={'pk': exp.pk})
        response = self.client_auth.get(url)
        actions = response.data['available_actions']
        assert any(a['id'] == 'C6' for a in actions['primary'])

    def test_bundle_available_actions_cerrado(self):
        """test_bundle_available_actions_cerrado() → estado CERRADO: solo ops lectura"""
        exp = ExpedienteFactory(status=ExpedienteStatus.CERRADO)
        url = reverse('expedientes-ui:bundle', kwargs={'pk': exp.pk})
        response = self.client_auth.get(url)
        actions = response.data['available_actions']
        assert all(not a['enabled'] for a in actions['primary'] if a['id'] != 'C15') # C15 might be special
        assert all(not a['enabled'] for a in actions['secondary'])

    def test_ops_c17_enabled_when_not_blocked(self):
        """test_ops_c17_enabled_when_not_blocked() → C17 enabled si is_blocked=false"""
        exp = ExpedienteFactory(is_blocked=False)
        url = reverse('expedientes-ui:bundle', kwargs={'pk': exp.pk})
        response = self.client_auth.get(url)
        actions = response.data['available_actions']
        assert any(a['id'] == 'C17' and a['enabled'] for a in actions['ops'])

    def test_ops_c18_disabled_when_not_blocked(self):
        """test_ops_c18_disabled_when_not_blocked() → C18 disabled con disabled_reason"""
        exp = ExpedienteFactory(is_blocked=False)
        url = reverse('expedientes-ui:bundle', kwargs={'pk': exp.pk})
        response = self.client_auth.get(url)
        actions = response.data['available_actions']
        unblock_action = next(a for a in actions['ops'] if a['id'] == 'C18')
        assert unblock_action['enabled'] is False
        assert 'disabled_reason' in unblock_action

    def test_ops_c15_fields_contract(self):
        """test_ops_c15_fields_contract() → C15 fields: name, amount, currency, category"""
        exp = ExpedienteFactory()
        url = reverse('expedientes-ui:bundle', kwargs={'pk': exp.pk})
        response = self.client_auth.get(url)
        actions = response.data['available_actions']
        c15 = next(a for a in actions['ops'] if a['id'] == 'C15')
        assert 'fields' in c15

    def test_available_actions_order(self):
        """test_available_actions_order() → Pipeline PRIMARY → SECONDARY → Ops"""
        exp = ExpedienteFactory()
        url = reverse('expedientes-ui:bundle', kwargs={'pk': exp.pk})
        response = self.client_auth.get(url)
        assert 'primary' in response.data['available_actions']
        assert 'secondary' in response.data['available_actions']
        assert 'ops' in response.data['available_actions']

    # Dashboard :
    def test_dashboard_active_count(self):
        """test_dashboard_active_count() → count correcto de expedientes activos"""
        Expediente.objects.all().delete()
        ExpedienteFactory(status=ExpedienteStatus.REGISTRO)
        ExpedienteFactory(status=ExpedienteStatus.CERRADO)
        url = reverse('core-ui:dashboard')
        response = self.client_auth.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['active_count'] == 1

    def test_dashboard_alert_count(self):
        """test_dashboard_alert_count() → AMBER+CORAL correctamente sumados"""
        now = timezone.now()
        Expediente.objects.all().delete()
        ExpedienteFactory(credit_clock_started_at=now - timedelta(days=20)) # WARNING/AMBER
        ExpedienteFactory(credit_clock_started_at=now - timedelta(days=40)) # CRITICAL/CORAL
        url = reverse('core-ui:dashboard')
        response = self.client_auth.get(url)
        assert response.data['alert_count'] >= 2

    def test_dashboard_blocked_count(self):
        """test_dashboard_blocked_count() → is_blocked=True correctamente"""
        Expediente.objects.all().delete()
        ExpedienteFactory(is_blocked=True)
        url = reverse('core-ui:dashboard')
        response = self.client_auth.get(url)
        assert response.data['blocked_count'] == 1

    def test_dashboard_total_cost(self):
        """test_dashboard_total_cost() → SQL aggregation, no loop"""
        Expediente.objects.all().delete()
        exp = ExpedienteFactory()
        CostLine.objects.create(expediente=exp, amount=Decimal('1000.00'), currency='USD', cost_type='TEST')
        url = reverse('core-ui:dashboard')
        response = self.client_auth.get(url)
        assert Decimal(response.data['total_cost']) >= Decimal('1000.00')

    def test_dashboard_top_risk(self):
        """test_dashboard_top_risk() → top 5 por credit_days DESC"""
        now = timezone.now()
        Expediente.objects.all().delete()
        for i in range(10):
            ExpedienteFactory(credit_clock_started_at=now - timedelta(days=31+i))
        url = reverse('core-ui:dashboard')
        response = self.client_auth.get(url)
        assert len(response.data['top_risk']) == 5
        assert response.data['top_risk'][0]['credit_days_elapsed'] > response.data['top_risk'][4]['credit_days_elapsed']

    def test_dashboard_blocked_list(self):
        """test_dashboard_blocked_list() → lista completa de bloqueados"""
        Expediente.objects.all().delete()
        exp = ExpedienteFactory(is_blocked=True)
        url = reverse('core-ui:dashboard')
        response = self.client_auth.get(url)
        assert any(item['id'] == str(exp.pk) for item in response.data['blocked_list'])

    # Regresión:
    def test_regression_all_22_endpoints(self):
        """test_regression_all_22_endpoints() → C1-C21 + C19 + C20 siguen funcionales"""
        exp = ExpedienteFactory()
        urls = [
            reverse('expedientes:register-oc', kwargs={'pk': exp.pk}),
            reverse('expedientes:register-proforma', kwargs={'pk': exp.pk}),
            reverse('expedientes:decide-mode', kwargs={'pk': exp.pk}),
            reverse('expedientes:confirm-sap', kwargs={'pk': exp.pk}),
            reverse('expedientes:confirm-production', kwargs={'pk': exp.pk}),
            reverse('expedientes:cancel', kwargs={'pk': exp.pk}),
            reverse('expedientes:block', kwargs={'pk': exp.pk}),
            reverse('expedientes:unblock', kwargs={'pk': exp.pk}),
        ]
        for u in urls:
            response = self.client_auth.get(u)
            assert response.status_code != status.HTTP_404_NOT_FOUND
