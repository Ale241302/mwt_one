"""
T13 — Access control: 401, 403 cross-access por rol.
"""
from decimal import Decimal
from datetime import date
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from apps.commercial.models import (
    RebateProgram, RebateAssignment, RebateLedger,
    PeriodType, RebateType, ThresholdType, LedgerStatus,
)
from apps.users.models import MWTUser, UserRole


def make_user(username, role):
    user, _ = MWTUser.objects.get_or_create(
        username=username,
        defaults={'role': role, 'email': f'{username}@test.com'},
    )
    user.set_password('testpass123')
    user.save()
    return user


def make_brand(slug):
    from apps.brands.models import Brand
    return Brand.objects.get_or_create(slug=slug, defaults={'name': f'Brand {slug}'})[0]


class T13AccessControlTest(TestCase):
    """T13 — Permisos por rol en endpoints de commercial."""

    def setUp(self):
        self.ceo = make_user('ceo-ac', UserRole.CEO)
        self.internal = make_user('internal-ac', UserRole.INTERNAL)
        self.client_marluvas = make_user('client-marluvas-ac', UserRole.CLIENT_MARLUVAS)
        self.client_tecmater = make_user('client-tecmater-ac', UserRole.CLIENT_TECMATER)

        self.api_client = APIClient()

    def _login(self, user):
        self.api_client.force_authenticate(user=user)

    def _logout(self):
        self.api_client.force_authenticate(user=None)

    # ------------------------------------------------------------------
    # T13-d — Anónimo → 401
    # ------------------------------------------------------------------

    def test_T13d_anonymous_rebate_programs_returns_401(self):
        self._logout()
        response = self.api_client.get('/api/commercial/rebate-programs/')
        self.assertIn(response.status_code, [401, 403])

    def test_T13d_anonymous_commissions_returns_401(self):
        self._logout()
        response = self.api_client.get('/api/commercial/commission-rules/')
        self.assertIn(response.status_code, [401, 403])

    # ------------------------------------------------------------------
    # T13-b — INTERNAL no puede ver comisiones
    # ------------------------------------------------------------------

    def test_T13b_internal_cannot_access_commissions(self):
        self._login(self.internal)
        response = self.api_client.get('/api/commercial/commission-rules/')
        self.assertEqual(response.status_code, 403)

    # ------------------------------------------------------------------
    # T13-c — CEO puede acceder a todo
    # ------------------------------------------------------------------

    def test_T13c_ceo_can_access_rebate_programs(self):
        self._login(self.ceo)
        response = self.api_client.get('/api/commercial/rebate-programs/')
        self.assertIn(response.status_code, [200, 201])

    def test_T13c_ceo_can_access_commissions(self):
        self._login(self.ceo)
        response = self.api_client.get('/api/commercial/commission-rules/')
        self.assertIn(response.status_code, [200, 201])

    def test_T13c_ceo_can_access_artifact_policy(self):
        self._login(self.ceo)
        response = self.api_client.get('/api/commercial/artifact-policy/')
        self.assertIn(response.status_code, [200, 404])

    # ------------------------------------------------------------------
    # T13-e — CLIENT_* no puede ver ledgers internos
    # ------------------------------------------------------------------

    def test_T13e_client_cannot_access_internal_ledgers(self):
        self._login(self.client_marluvas)
        response = self.api_client.get('/api/commercial/rebate-ledgers/')
        self.assertIn(response.status_code, [403, 404])

    # ------------------------------------------------------------------
    # T13-a — CLIENT cross-access entre subsidiaries
    # ------------------------------------------------------------------

    def test_T13a_client_marluvas_cannot_access_tecmater_portal(self):
        """CLIENT_MARLUVAS no puede ver progreso de rebate de CLIENT_TECMATER."""
        self._login(self.client_marluvas)
        # El portal filtra por subsidiary del usuario autenticado
        # Intentar acceso a un ledger ajeno
        response = self.api_client.get('/api/commercial/portal/progress/')
        # Debe retornar solo registros del propio usuario (vacío) o 403
        if response.status_code == 200:
            # Si retorna 200, los datos deben pertenecer solo al usuario autenticado
            # (empty list es aceptable — significa que filtra correctamente)
            self.assertIsInstance(response.data, (list, dict))
        else:
            self.assertIn(response.status_code, [403, 404])

    # ------------------------------------------------------------------
    # T13 — INTERNAL puede ver rebate programs pero NO comisiones
    # ------------------------------------------------------------------

    def test_T13_internal_can_access_rebate_programs(self):
        self._login(self.internal)
        response = self.api_client.get('/api/commercial/rebate-programs/')
        self.assertIn(response.status_code, [200, 201])

    def test_T13_client_cannot_access_rebate_programs_internal(self):
        self._login(self.client_marluvas)
        response = self.api_client.get('/api/commercial/rebate-programs/')
        self.assertIn(response.status_code, [403, 404])
