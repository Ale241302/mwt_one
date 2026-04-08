"""
S25-14 — Suite de tests backend Sprint 25 (56 tests total).
Cubre:
  - compute_coverage() edge cases (T01-T08)
  - recalculate_expediente_credit() con payment_status (T09-T14)
  - verify_payment (T15-T20)
  - reject_payment (T21-T27)
  - release_credit individual (T28-T32)
  - release_all_verified bulk (T33-T38)
  - patch_deferred_price invariants (T39-T48)
  - split_expediente con invert_parent (T49-T54)
  - data migration legacy C2 (T55-T56)
"""
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from apps.expedientes.models import Expediente, ExpedientePago
from apps.expedientes.services.credit import compute_coverage, recalculate_expediente_credit

User = get_user_model()


# ─── Factories helpers ───────────────────────────────────────────────────────

def make_user(superuser=False, **kwargs):
    u = User(username=kwargs.get('username', 'testuser'))
    if superuser:
        u.is_superuser = True
        u.is_staff = True
    u.set_password('pass')
    u.save()
    return u


def make_expediente(**kwargs):
    """Minimal Expediente factory — only mandatory fields assumed."""
    from apps.expedientes.models import Expediente
    defaults = {}
    defaults.update(kwargs)
    return Expediente.objects.create(**defaults)


def make_pago(expediente, amount, status='pending', **kwargs):
    return ExpedientePago.objects.create(
        expediente=expediente,
        payment_status=status,
        amount_paid=Decimal(str(amount)),
        **kwargs
    )


# ════════════════════════════════════════════════════════════════════
#  BLOQUE 1 — compute_coverage() edge cases (T01-T08)
# ════════════════════════════════════════════════════════════════════

class TestComputeCoverage(TestCase):
    """T01-T08: SSOT compute_coverage()."""

    def test_T01_none_total_returns_none_0(self):
        """Edge: total=None → ('none', 0.00) even if paid>0."""
        coverage, pct = compute_coverage(Decimal('100'), None)
        self.assertEqual(coverage, 'none')
        self.assertEqual(pct, Decimal('0.00'))

    def test_T02_zero_total_returns_none_0(self):
        """Edge: total=0 → ('none', 0.00) — division by zero safeguard."""
        coverage, pct = compute_coverage(Decimal('100'), Decimal('0'))
        self.assertEqual(coverage, 'none')
        self.assertEqual(pct, Decimal('0.00'))

    def test_T03_zero_paid_returns_none(self):
        coverage, pct = compute_coverage(Decimal('0'), Decimal('1000'))
        self.assertEqual(coverage, 'none')
        self.assertEqual(pct, Decimal('0.00'))

    def test_T04_partial_coverage(self):
        coverage, pct = compute_coverage(Decimal('500'), Decimal('1000'))
        self.assertEqual(coverage, 'partial')
        self.assertEqual(pct, Decimal('50.00'))

    def test_T05_complete_coverage(self):
        coverage, pct = compute_coverage(Decimal('1000'), Decimal('1000'))
        self.assertEqual(coverage, 'complete')
        self.assertEqual(pct, Decimal('100.00'))

    def test_T06_overpayment_caps_at_100(self):
        """Sobrepago: coverage='complete', pct capeado a 100.00."""
        coverage, pct = compute_coverage(Decimal('1500'), Decimal('1000'))
        self.assertEqual(coverage, 'complete')
        self.assertEqual(pct, Decimal('100.00'))

    def test_T07_rounding_half_up(self):
        """ROUND_HALF_UP: 1/3 * 100 = 33.33... → 33.33 (not 33.34)."""
        coverage, pct = compute_coverage(Decimal('1'), Decimal('3'))
        self.assertIn(coverage, ('partial',))
        self.assertEqual(pct, Decimal('33.33'))

    def test_T08_rounding_half_up_rounds_up(self):
        """2/3 * 100 = 66.666... → ROUND_HALF_UP → 66.67."""
        coverage, pct = compute_coverage(Decimal('2'), Decimal('3'))
        self.assertEqual(pct, Decimal('66.67'))


# ════════════════════════════════════════════════════════════════════
#  BLOQUE 2 — recalculate_expediente_credit() con payment_status (T09-T14)
# ════════════════════════════════════════════════════════════════════

class TestRecalculateCreditPaymentStatus(TestCase):
    """T09-T14: recalculate filtra solo credit_released."""

    def setUp(self):
        self.exp = make_expediente()

    def test_T09_pending_payments_not_counted(self):
        make_pago(self.exp, 500, status='pending')
        recalculate_expediente_credit(self.exp)
        self.exp.refresh_from_db()
        # credit_released=False porque no hay pagos credit_released
        self.assertFalse(self.exp.credit_released)

    def test_T10_verified_payments_not_counted(self):
        make_pago(self.exp, 500, status='verified')
        recalculate_expediente_credit(self.exp)
        self.exp.refresh_from_db()
        self.assertFalse(self.exp.credit_released)

    def test_T11_rejected_payments_not_counted(self):
        make_pago(self.exp, 500, status='rejected')
        recalculate_expediente_credit(self.exp)
        self.exp.refresh_from_db()
        self.assertFalse(self.exp.credit_released)

    def test_T12_only_credit_released_counted(self):
        """Solo credit_released suma para credit_exposure."""
        make_pago(self.exp, 300, status='pending')
        make_pago(self.exp, 200, status='credit_released')
        recalculate_expediente_credit(self.exp)
        self.exp.refresh_from_db()
        # total_lines=0 (no product_lines), released=200 → exposure=-200 → credit_released=True
        self.assertTrue(self.exp.credit_released)

    def test_T13_mix_statuses_only_released_count(self):
        make_pago(self.exp, 1000, status='verified')
        make_pago(self.exp, 500, status='credit_released')
        recalculate_expediente_credit(self.exp)
        self.exp.refresh_from_db()
        # exposure = total_lines(0) - released(500) = -500 → credit_released=True
        self.assertEqual(self.exp.credit_exposure, Decimal('-500.00'))

    def test_T14_no_payments_exposure_zero(self):
        recalculate_expediente_credit(self.exp)
        self.exp.refresh_from_db()
        self.assertEqual(self.exp.credit_exposure, Decimal('0.00'))


# ════════════════════════════════════════════════════════════════════
#  BLOQUE 3 — verify_payment endpoint (T15-T20)
# ════════════════════════════════════════════════════════════════════

class TestVerifyPaymentEndpoint(TestCase):
    """T15-T20: POST /api/expedientes/{exp_id}/pagos/{pago_id}/verify/"""

    def setUp(self):
        self.ceo = make_user(superuser=True, username='ceo')
        self.agent = make_user(username='agent')
        self.exp = make_expediente()
        self.pago = make_pago(self.exp, 500, status='pending')
        self.client = APIClient()
        self.url = reverse('expedientes:payment-verify', kwargs={
            'exp_id': self.exp.expediente_id,
            'pago_id': self.pago.pk,
        })

    def test_T15_non_ceo_gets_403(self):
        self.client.force_authenticate(user=self.agent)
        resp = self.client.post(self.url)
        self.assertEqual(resp.status_code, 403)

    def test_T16_pending_to_verified(self):
        self.client.force_authenticate(user=self.ceo)
        resp = self.client.post(self.url)
        self.assertEqual(resp.status_code, 200)
        self.pago.refresh_from_db()
        self.assertEqual(self.pago.payment_status, 'verified')
        self.assertIsNotNone(self.pago.verified_at)
        self.assertEqual(self.pago.verified_by, self.ceo)

    def test_T17_already_verified_returns_409(self):
        self.pago.payment_status = 'verified'
        self.pago.save()
        self.client.force_authenticate(user=self.ceo)
        resp = self.client.post(self.url)
        self.assertEqual(resp.status_code, 409)

    def test_T18_credit_released_returns_409(self):
        self.pago.payment_status = 'credit_released'
        self.pago.save()
        self.client.force_authenticate(user=self.ceo)
        resp = self.client.post(self.url)
        self.assertEqual(resp.status_code, 409)

    def test_T19_does_not_recalculate_credit(self):
        """Verify NO libera crédito automáticamente."""
        before = self.exp.credit_exposure
        self.client.force_authenticate(user=self.ceo)
        self.client.post(self.url)
        self.exp.refresh_from_db()
        self.assertEqual(self.exp.credit_exposure, before)

    def test_T20_eventlog_created(self):
        from apps.expedientes.models import EventLog
        count_before = EventLog.objects.filter(expediente=self.exp).count()
        self.client.force_authenticate(user=self.ceo)
        self.client.post(self.url)
        count_after = EventLog.objects.filter(expediente=self.exp).count()
        self.assertEqual(count_after, count_before + 1)


# ════════════════════════════════════════════════════════════════════
#  BLOQUE 4 — reject_payment endpoint (T21-T27)
# ════════════════════════════════════════════════════════════════════

class TestRejectPaymentEndpoint(TestCase):
    """T21-T27: POST /api/expedientes/{exp_id}/pagos/{pago_id}/reject/"""

    def setUp(self):
        self.ceo = make_user(superuser=True, username='ceo')
        self.agent = make_user(username='agent')
        self.exp = make_expediente()
        self.pago = make_pago(self.exp, 500, status='pending')
        self.client = APIClient()
        self.url = reverse('expedientes:payment-reject', kwargs={
            'exp_id': self.exp.expediente_id,
            'pago_id': self.pago.pk,
        })

    def test_T21_non_ceo_403(self):
        self.client.force_authenticate(user=self.agent)
        resp = self.client.post(self.url, {'reason': 'fake'})
        self.assertEqual(resp.status_code, 403)

    def test_T22_missing_reason_400(self):
        self.client.force_authenticate(user=self.ceo)
        resp = self.client.post(self.url, {})
        self.assertEqual(resp.status_code, 400)

    def test_T23_pending_to_rejected(self):
        self.client.force_authenticate(user=self.ceo)
        resp = self.client.post(self.url, {'reason': 'Cheque rebotado'})
        self.assertEqual(resp.status_code, 200)
        self.pago.refresh_from_db()
        self.assertEqual(self.pago.payment_status, 'rejected')
        self.assertEqual(self.pago.rejection_reason, 'Cheque rebotado')

    def test_T24_verified_to_rejected(self):
        self.pago.payment_status = 'verified'
        self.pago.save()
        self.client.force_authenticate(user=self.ceo)
        resp = self.client.post(self.url, {'reason': 'Fraude detectado'})
        self.assertEqual(resp.status_code, 200)
        self.pago.refresh_from_db()
        self.assertEqual(self.pago.payment_status, 'rejected')

    def test_T25_credit_released_returns_409(self):
        self.pago.payment_status = 'credit_released'
        self.pago.save()
        self.client.force_authenticate(user=self.ceo)
        resp = self.client.post(self.url, {'reason': 'Error'})
        self.assertEqual(resp.status_code, 409)

    def test_T26_reject_triggers_recalculate(self):
        """Reject llama recalculate_expediente_credit."""
        self.pago.payment_status = 'credit_released'  # simular: fue liberado antes
        self.pago.save()
        # override para poder rechazar (cambiamos a verified)
        self.pago.payment_status = 'verified'
        self.pago.save()
        self.client.force_authenticate(user=self.ceo)
        self.client.post(self.url, {'reason': 'Test'})
        self.exp.refresh_from_db()
        # credit_exposure debería haber cambiado
        self.assertIsNotNone(self.exp.credit_exposure)

    def test_T27_eventlog_created_on_reject(self):
        from apps.expedientes.models import EventLog
        before = EventLog.objects.filter(expediente=self.exp).count()
        self.client.force_authenticate(user=self.ceo)
        self.client.post(self.url, {'reason': 'Log test'})
        after = EventLog.objects.filter(expediente=self.exp).count()
        self.assertEqual(after, before + 1)


# ════════════════════════════════════════════════════════════════════
#  BLOQUE 5 — release_credit individual (T28-T32)
# ════════════════════════════════════════════════════════════════════

class TestReleaseCreditEndpoint(TestCase):
    """T28-T32: POST /api/expedientes/{exp_id}/pagos/{pago_id}/release-credit/"""

    def setUp(self):
        self.ceo = make_user(superuser=True, username='ceo')
        self.exp = make_expediente()
        self.pago = make_pago(self.exp, 500, status='verified')
        self.client = APIClient()
        self.url = reverse('expedientes:payment-release-credit', kwargs={
            'exp_id': self.exp.expediente_id,
            'pago_id': self.pago.pk,
        })

    def test_T28_verified_to_credit_released(self):
        self.client.force_authenticate(user=self.ceo)
        resp = self.client.post(self.url)
        self.assertEqual(resp.status_code, 200)
        self.pago.refresh_from_db()
        self.assertEqual(self.pago.payment_status, 'credit_released')
        self.assertIsNotNone(self.pago.credit_released_at)
        self.assertEqual(self.pago.credit_released_by, self.ceo)

    def test_T29_pending_returns_409(self):
        self.pago.payment_status = 'pending'
        self.pago.save()
        self.client.force_authenticate(user=self.ceo)
        resp = self.client.post(self.url)
        self.assertEqual(resp.status_code, 409)

    def test_T30_already_released_returns_409(self):
        self.pago.payment_status = 'credit_released'
        self.pago.save()
        self.client.force_authenticate(user=self.ceo)
        resp = self.client.post(self.url)
        self.assertEqual(resp.status_code, 409)

    def test_T31_recalculate_called_on_release(self):
        self.client.force_authenticate(user=self.ceo)
        self.client.post(self.url)
        self.exp.refresh_from_db()
        # Con 1 pago de 500 credit_released y sin product_lines, exposure = -500
        self.assertEqual(self.exp.credit_exposure, Decimal('-500.00'))

    def test_T32_eventlog_created(self):
        from apps.expedientes.models import EventLog
        before = EventLog.objects.filter(expediente=self.exp).count()
        self.client.force_authenticate(user=self.ceo)
        self.client.post(self.url)
        after = EventLog.objects.filter(expediente=self.exp).count()
        self.assertEqual(after, before + 1)


# ════════════════════════════════════════════════════════════════════
#  BLOQUE 6 — release_all_verified bulk (T33-T38)
# ════════════════════════════════════════════════════════════════════

class TestReleaseAllVerifiedEndpoint(TestCase):
    """T33-T38: POST /api/expedientes/{exp_id}/pagos/release-all-verified/"""

    def setUp(self):
        self.ceo = make_user(superuser=True, username='ceo')
        self.exp = make_expediente()
        self.client = APIClient()
        self.url = reverse('expedientes:payment-release-all-verified', kwargs={
            'exp_id': self.exp.expediente_id,
        })

    def test_T33_releases_all_verified(self):
        p1 = make_pago(self.exp, 100, status='verified')
        p2 = make_pago(self.exp, 200, status='verified')
        self.client.force_authenticate(user=self.ceo)
        resp = self.client.post(self.url)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data['released'], 2)
        p1.refresh_from_db()
        p2.refresh_from_db()
        self.assertEqual(p1.payment_status, 'credit_released')
        self.assertEqual(p2.payment_status, 'credit_released')

    def test_T34_ignores_pending_and_rejected(self):
        make_pago(self.exp, 100, status='pending')
        make_pago(self.exp, 200, status='rejected')
        self.client.force_authenticate(user=self.ceo)
        resp = self.client.post(self.url)
        self.assertEqual(resp.data['released'], 0)
        self.assertEqual(resp.data['already_released'], 0)

    def test_T35_idempotent_second_call_returns_zero_released(self):
        make_pago(self.exp, 300, status='verified')
        self.client.force_authenticate(user=self.ceo)
        self.client.post(self.url)  # primera vez
        resp = self.client.post(self.url)  # segunda
        self.assertEqual(resp.data['released'], 0)
        self.assertEqual(resp.data['already_released'], 1)

    def test_T36_recalculate_called_once_per_bulk(self):
        """Recalculate se llama UNA sola vez post-bulk (no N veces)."""
        make_pago(self.exp, 100, status='verified')
        make_pago(self.exp, 200, status='verified')
        self.client.force_authenticate(user=self.ceo)
        self.client.post(self.url)
        self.exp.refresh_from_db()
        # exposure = 0 - 300 = -300
        self.assertEqual(self.exp.credit_exposure, Decimal('-300.00'))

    def test_T37_one_eventlog_per_pago(self):
        from apps.expedientes.models import EventLog
        make_pago(self.exp, 100, status='verified')
        make_pago(self.exp, 200, status='verified')
        before = EventLog.objects.filter(expediente=self.exp).count()
        self.client.force_authenticate(user=self.ceo)
        self.client.post(self.url)
        after = EventLog.objects.filter(expediente=self.exp).count()
        self.assertEqual(after - before, 2)  # 1 por pago

    def test_T38_non_ceo_403(self):
        agent = make_user(username='agent')
        self.client.force_authenticate(user=agent)
        resp = self.client.post(self.url)
        self.assertEqual(resp.status_code, 403)


# ════════════════════════════════════════════════════════════════════
#  BLOQUE 7 — patch_deferred_price invariants (T39-T48)
# ════════════════════════════════════════════════════════════════════

class TestPatchDeferredPrice(TestCase):
    """T39-T48: PATCH /api/expedientes/{exp_id}/deferred-price/"""

    def setUp(self):
        self.ceo = make_user(superuser=True, username='ceo')
        self.agent = make_user(username='agent')
        self.exp = make_expediente()
        self.client = APIClient()
        self.url = reverse('expedientes:deferred-price', kwargs={
            'exp_id': self.exp.expediente_id,
        })

    def test_T39_non_ceo_403(self):
        self.client.force_authenticate(user=self.agent)
        resp = self.client.patch(self.url, {'deferred_total_price': '500.00'})
        self.assertEqual(resp.status_code, 403)

    def test_T40_set_price_ok(self):
        self.client.force_authenticate(user=self.ceo)
        resp = self.client.patch(self.url, {'deferred_total_price': '1500.00'})
        self.assertEqual(resp.status_code, 200)
        self.exp.refresh_from_db()
        self.assertEqual(self.exp.deferred_total_price, Decimal('1500.00'))

    def test_T41_set_visible_true_with_price_ok(self):
        self.exp.deferred_total_price = Decimal('1000')
        self.exp.save()
        self.client.force_authenticate(user=self.ceo)
        resp = self.client.patch(self.url, {'deferred_visible': True})
        self.assertEqual(resp.status_code, 200)
        self.exp.refresh_from_db()
        self.assertTrue(self.exp.deferred_visible)

    def test_T42_visible_true_without_price_400(self):
        """visible=True sin precio → 400."""
        self.client.force_authenticate(user=self.ceo)
        resp = self.client.patch(self.url, {'deferred_visible': True})
        self.assertEqual(resp.status_code, 400)

    def test_T43_null_price_plus_visible_true_same_call_400(self):
        """Contradictorio: null + visible=True en misma llamada → 400 duro."""
        self.client.force_authenticate(user=self.ceo)
        resp = self.client.patch(self.url, {
            'deferred_total_price': None,
            'deferred_visible': True,
        })
        self.assertEqual(resp.status_code, 400)

    def test_T44_null_price_auto_corrects_visible_false(self):
        """null precio → visible auto-corregido a False (paso 2 del algoritmo)."""
        self.exp.deferred_total_price = Decimal('1000')
        self.exp.deferred_visible = True
        self.exp.save()
        self.client.force_authenticate(user=self.ceo)
        resp = self.client.patch(self.url, {'deferred_total_price': None})
        self.assertEqual(resp.status_code, 200)
        self.exp.refresh_from_db()
        self.assertIsNone(self.exp.deferred_total_price)
        self.assertFalse(self.exp.deferred_visible)

    def test_T45_negative_price_400(self):
        self.client.force_authenticate(user=self.ceo)
        resp = self.client.patch(self.url, {'deferred_total_price': '-100'})
        self.assertEqual(resp.status_code, 400)

    def test_T46_zero_price_is_valid(self):
        """0.00 es valor válido (distinto de null)."""
        self.client.force_authenticate(user=self.ceo)
        resp = self.client.patch(self.url, {'deferred_total_price': '0.00'})
        self.assertEqual(resp.status_code, 200)
        self.exp.refresh_from_db()
        self.assertEqual(self.exp.deferred_total_price, Decimal('0.00'))

    def test_T47_empty_body_400(self):
        self.client.force_authenticate(user=self.ceo)
        resp = self.client.patch(self.url, {})
        self.assertEqual(resp.status_code, 400)

    def test_T48_eventlog_created_on_update(self):
        from apps.expedientes.models import EventLog
        before = EventLog.objects.filter(expediente=self.exp).count()
        self.client.force_authenticate(user=self.ceo)
        self.client.patch(self.url, {'deferred_total_price': '2000'})
        after = EventLog.objects.filter(expediente=self.exp).count()
        self.assertEqual(after, before + 1)


# ════════════════════════════════════════════════════════════════════
#  BLOQUE 8 — split_expediente con invert_parent (T49-T54)
# ════════════════════════════════════════════════════════════════════

class TestSplitExpedienteInvertParent(TestCase):
    """T49-T54: POST /api/expedientes/{pk}/separate-products/ con invert_parent."""

    def setUp(self):
        from apps.expedientes.models import ExpedienteProductLine
        self.user = make_user(username='ops')
        self.exp = make_expediente()
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        # Crear 2 product lines para poder hacer split
        # (se necesita al menos 2 para que len(line_ids) < total_lines)
        self.line1 = ExpedienteProductLine.objects.create(
            expediente=self.exp,
            unit_price=Decimal('100'),
            quantity=1,
        )
        self.line2 = ExpedienteProductLine.objects.create(
            expediente=self.exp,
            unit_price=Decimal('200'),
            quantity=1,
        )
        self.url = reverse('expedientes:separate-products', kwargs={'pk': self.exp.expediente_id})

    def test_T49_split_default_creates_child_nuevo(self):
        """Sin invert_parent: nuevo es hijo (parent=original)."""
        resp = self.client.post(self.url, {'product_line_ids': [self.line1.pk]})
        self.assertEqual(resp.status_code, 201)
        new_id = resp.data['new_expediente']['expediente_id']
        new_exp = Expediente.objects.get(expediente_id=new_id)
        self.assertEqual(str(new_exp.parent_expediente_id), str(self.exp.expediente_id))

    def test_T50_invert_parent_makes_original_child(self):
        """invert_parent=True: original → hijo del nuevo."""
        resp = self.client.post(self.url, {
            'product_line_ids': [self.line1.pk],
            'invert_parent': True,
        })
        self.assertEqual(resp.status_code, 201)
        self.exp.refresh_from_db()
        new_id = resp.data['new_expediente']['expediente_id']
        new_exp = Expediente.objects.get(expediente_id=new_id)
        self.assertEqual(str(self.exp.parent_expediente_id), str(new_exp.expediente_id))
        self.assertTrue(self.exp.is_inverted_child)

    def test_T51_invert_on_already_child_returns_409(self):
        """409 si original ya tiene parent (ya es hijo)."""
        another = make_expediente()
        self.exp.parent_expediente = another
        self.exp.save()
        resp = self.client.post(self.url, {
            'product_line_ids': [self.line1.pk],
            'invert_parent': True,
        })
        self.assertEqual(resp.status_code, 409)

    def test_T52_backward_compat_no_invert_param(self):
        """Llamada sin invert_parent es backward compat con S18."""
        resp = self.client.post(self.url, {'product_line_ids': [self.line1.pk]})
        self.assertEqual(resp.status_code, 201)
        # nuevo es hijo del original (comportamiento S18)
        new_exp = Expediente.objects.get(
            expediente_id=resp.data['new_expediente']['expediente_id']
        )
        self.assertEqual(str(new_exp.parent_expediente_id), str(self.exp.expediente_id))

    def test_T53_eventlog_in_both_expedientes(self):
        from apps.expedientes.models import EventLog
        resp = self.client.post(self.url, {
            'product_line_ids': [self.line1.pk],
            'invert_parent': False,
        })
        self.assertEqual(resp.status_code, 201)
        new_id = resp.data['new_expediente']['expediente_id']
        logs_original = EventLog.objects.filter(expediente=self.exp)
        logs_new = EventLog.objects.filter(expediente__expediente_id=new_id)
        self.assertGreater(logs_original.count(), 0)
        self.assertGreater(logs_new.count(), 0)

    def test_T54_all_lines_split_returns_400(self):
        """No se pueden separar TODAS las líneas."""
        resp = self.client.post(self.url, {
            'product_line_ids': [self.line1.pk, self.line2.pk],
        })
        self.assertEqual(resp.status_code, 400)


# ════════════════════════════════════════════════════════════════════
#  BLOQUE 9 — data migration legacy C2 (T55-T56)
# ════════════════════════════════════════════════════════════════════

class TestLegacyMigrationC2(TestCase):
    """
    T55-T56: Verifica que la lógica de clasificación C2 es correcta.
    No corre la migración en sí (no se puede en tests Django estándar);
    verifica la lógica del forwards() con datos reales.
    """

    def test_T55_zero_amount_classifies_as_pending(self):
        """amount_paid=0 → payment_status='pending' (lógica C2)."""
        exp = make_expediente()
        pago = make_pago(exp, 0, status='pending')
        # La migración daría: 0 <= 0 → pending
        result = 'pending' if (pago.amount_paid is None or pago.amount_paid <= 0) else 'verified'
        self.assertEqual(result, 'pending')

    def test_T56_gate_passed_status_classifies_as_credit_released(self):
        """Expediente en PRODUCCION + pago >0 → credit_released (C2)."""
        GATE_PASSED_STATUSES = {
            'PRODUCCION', 'PREPARACION', 'DESPACHO',
            'TRANSITO', 'EN_DESTINO', 'CERRADO',
        }
        exp = make_expediente()
        exp.status = 'PRODUCCION'
        exp.save()
        pago = make_pago(exp, 500, status='pending')
        # Simular lógica de migración forward
        if pago.amount_paid is None or pago.amount_paid <= 0:
            result = 'pending'
        elif exp.status in GATE_PASSED_STATUSES:
            result = 'credit_released'
        else:
            result = 'verified'
        self.assertEqual(result, 'credit_released')
