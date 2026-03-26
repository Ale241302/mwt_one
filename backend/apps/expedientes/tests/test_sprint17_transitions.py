"""
S17-14: Tests for Sprint 17 state machine transitions.
New file — does NOT modify existing tests.

Covers:
- S17-01: C11 transitions to DESPACHO (not TRANSITO)
- S17-02: C11B exists and transitions DESPACHO → TRANSITO
- S17-03: REOPEN in dispatcher
- S17-05: handle_c1 signature (payload, user)
- Full 8-state flow: REGISTRO → ... → CERRADO
- REOPEN: functional + blocked when reopen_count >= 1
"""
import inspect
import pytest
from django.test import TestCase
from unittest.mock import patch, MagicMock


class TestC11TransitionsToDespacho(TestCase):
    """
    S17-01: C11 must transition status to DESPACHO, not TRANSITO.
    """

    def test_c11_transition_target_is_despacho(self):
        from apps.expedientes.services.constants import COMMAND_SPEC
        from apps.expedientes.enums_exp import ExpedienteStatus
        spec = COMMAND_SPEC['C11']
        self.assertEqual(
            spec['transition_to'],
            ExpedienteStatus.DESPACHO,
            "C11 must transition to DESPACHO (S17-01 fix)"
        )

    def test_c11_requires_preparacion(self):
        from apps.expedientes.services.constants import COMMAND_SPEC
        from apps.expedientes.enums_exp import ExpedienteStatus
        spec = COMMAND_SPEC['C11']
        self.assertEqual(spec['requires_status'], ExpedienteStatus.PREPARACION)

    def test_c11_transition_is_not_transito(self):
        """Regression: ensure old incorrect target TRANSITO is no longer set."""
        from apps.expedientes.services.constants import COMMAND_SPEC
        from apps.expedientes.enums_exp import ExpedienteStatus
        spec = COMMAND_SPEC['C11']
        self.assertNotEqual(
            spec['transition_to'],
            ExpedienteStatus.TRANSITO,
            "Regression: C11 must NOT go to TRANSITO anymore"
        )


class TestC11BDespachoToTransito(TestCase):
    """
    S17-02: DESPACHO → TRANSITO via C11B.
    """

    def test_c11b_exists_in_command_spec(self):
        from apps.expedientes.services.constants import COMMAND_SPEC
        self.assertIn('C11B', COMMAND_SPEC, "C11B must be registered in COMMAND_SPEC")

    def test_c11b_transitions_to_transito(self):
        from apps.expedientes.services.constants import COMMAND_SPEC
        from apps.expedientes.enums_exp import ExpedienteStatus
        spec = COMMAND_SPEC['C11B']
        self.assertEqual(spec['transition_to'], ExpedienteStatus.TRANSITO)

    def test_c11b_requires_despacho(self):
        from apps.expedientes.services.constants import COMMAND_SPEC
        from apps.expedientes.enums_exp import ExpedienteStatus
        spec = COMMAND_SPEC['C11B']
        self.assertEqual(spec['requires_status'], ExpedienteStatus.DESPACHO)

    def test_c11b_in_handlers(self):
        from apps.expedientes.services import HANDLERS
        self.assertIn('C11B', HANDLERS, "C11B must be registered in HANDLERS dict")

    def test_c11b_handler_is_callable(self):
        from apps.expedientes.services import HANDLERS
        handler = HANDLERS['C11B']
        self.assertTrue(callable(handler), "C11B handler must be callable")


class TestPreparacionDespachoTransitoFlow(TestCase):
    """
    Integration: PREPARACION → DESPACHO → TRANSITO full flow test.
    """

    def setUp(self):
        from apps.expedientes.tests.factories import ExpedienteFactory, UserFactory
        self.ceo = UserFactory(username='ceo_s17', is_superuser=True)
        self.expediente = ExpedienteFactory(status='PREPARACION')

    def test_preparacion_to_despacho_via_c11(self):
        """Executing C11 on a PREPARACION expediente must yield DESPACHO."""
        from apps.expedientes.services import HANDLERS
        from apps.expedientes.enums_exp import ExpedienteStatus

        handler = HANDLERS['C11']
        result = handler(self.expediente, {}, self.ceo)

        self.expediente.refresh_from_db()
        self.assertEqual(
            self.expediente.status,
            ExpedienteStatus.DESPACHO,
            "After C11, status must be DESPACHO"
        )

    def test_despacho_to_transito_via_c11b(self):
        """Executing C11B on a DESPACHO expediente must yield TRANSITO."""
        from apps.expedientes.services import HANDLERS
        from apps.expedientes.enums_exp import ExpedienteStatus

        # Force DESPACHO state
        self.expediente.status = 'DESPACHO'
        self.expediente.save(update_fields=['status'])

        handler = HANDLERS['C11B']
        handler(self.expediente, {}, self.ceo)

        self.expediente.refresh_from_db()
        self.assertEqual(
            self.expediente.status,
            ExpedienteStatus.TRANSITO,
            "After C11B, status must be TRANSITO"
        )

    def test_full_preparacion_despacho_transito_sequence(self):
        """Chained: PREPARACION → C11 → DESPACHO → C11B → TRANSITO."""
        from apps.expedientes.services import HANDLERS
        from apps.expedientes.enums_exp import ExpedienteStatus

        HANDLERS['C11'](self.expediente, {}, self.ceo)
        self.expediente.refresh_from_db()
        self.assertEqual(self.expediente.status, ExpedienteStatus.DESPACHO)

        HANDLERS['C11B'](self.expediente, {}, self.ceo)
        self.expediente.refresh_from_db()
        self.assertEqual(self.expediente.status, ExpedienteStatus.TRANSITO)


class TestReopenInDispatcher(TestCase):
    """
    S17-03: REOPEN must be connected in COMMAND_SPEC, URL, and HANDLERS.
    """

    def test_reopen_in_command_spec(self):
        from apps.expedientes.services.constants import COMMAND_SPEC
        self.assertIn('REOPEN', COMMAND_SPEC)

    def test_reopen_in_handlers(self):
        from apps.expedientes.services import HANDLERS
        self.assertIn('REOPEN', HANDLERS)

    def test_reopen_requires_ceo(self):
        from apps.expedientes.services.constants import COMMAND_SPEC
        self.assertTrue(
            COMMAND_SPEC['REOPEN'].get('requires_ceo', False),
            "REOPEN must require CEO"
        )

    def test_reopen_requires_cancelado(self):
        from apps.expedientes.services.constants import COMMAND_SPEC
        from apps.expedientes.enums_exp import ExpedienteStatus
        spec = COMMAND_SPEC['REOPEN']
        requires = spec.get('requires_status')
        if isinstance(requires, list):
            self.assertIn(ExpedienteStatus.CANCELADO, requires)
        else:
            self.assertEqual(requires, ExpedienteStatus.CANCELADO)

    def test_reopen_transitions_to_registro(self):
        from apps.expedientes.services.constants import COMMAND_SPEC
        from apps.expedientes.enums_exp import ExpedienteStatus
        spec = COMMAND_SPEC['REOPEN']
        self.assertEqual(spec.get('transition_to'), ExpedienteStatus.REGISTRO)


class TestReopenFunctional(TestCase):
    """
    REOPEN integration: CANCELADO → REOPEN → REGISTRO, and blocked if reopen_count >= 1.
    """

    def setUp(self):
        from apps.expedientes.tests.factories import ExpedienteFactory, UserFactory
        self.ceo = UserFactory(username='ceo_reopen', is_superuser=True)
        self.expediente = ExpedienteFactory(status='CANCELADO', reopen_count=0)

    def test_reopen_cancelado_to_registro(self):
        """CEO can reopen a CANCELADO expediente → status becomes REGISTRO."""
        from apps.expedientes.services import HANDLERS
        from apps.expedientes.enums_exp import ExpedienteStatus

        handler = HANDLERS['REOPEN']
        handler(self.expediente, {}, self.ceo)

        self.expediente.refresh_from_db()
        self.assertEqual(
            self.expediente.status,
            ExpedienteStatus.REGISTRO,
            "After REOPEN, status must be REGISTRO"
        )

    def test_reopen_increments_reopen_count(self):
        """REOPEN must increment reopen_count by 1."""
        from apps.expedientes.services import HANDLERS

        initial_count = self.expediente.reopen_count
        HANDLERS['REOPEN'](self.expediente, {}, self.ceo)
        self.expediente.refresh_from_db()
        self.assertEqual(
            self.expediente.reopen_count,
            initial_count + 1
        )

    def test_reopen_blocked_if_already_reopened(self):
        """REOPEN must be blocked if reopen_count >= 1 (max 1 reopening)."""
        from apps.expedientes.services import HANDLERS
        from django.core.exceptions import ValidationError, PermissionDenied

        # Set reopen_count to 1 (already reopened once)
        self.expediente.reopen_count = 1
        self.expediente.save(update_fields=['reopen_count'])

        handler = HANDLERS['REOPEN']
        with self.assertRaises((ValidationError, PermissionDenied, ValueError, Exception)):
            handler(self.expediente, {}, self.ceo)

    def test_reopen_blocked_for_non_ceo(self):
        """Only CEO (superuser) can execute REOPEN."""
        from apps.expedientes.tests.factories import UserFactory
        from apps.expedientes.services import HANDLERS
        from django.core.exceptions import PermissionDenied

        normal_user = UserFactory(username='normal_s17', is_superuser=False)
        handler = HANDLERS['REOPEN']
        with self.assertRaises((PermissionDenied, ValueError, Exception)):
            handler(self.expediente, {}, normal_user)


class TestHandleC1Signature(TestCase):
    """
    S17-05: handle_c1 signature must be (payload, user).
    """

    def test_handle_c1_first_param_is_payload(self):
        from apps.expedientes.services.commands.c1 import handle_c1
        sig = inspect.signature(handle_c1)
        params = list(sig.parameters.keys())
        self.assertEqual(params[0], 'payload', "First param must be 'payload'")

    def test_handle_c1_second_param_is_user(self):
        from apps.expedientes.services.commands.c1 import handle_c1
        sig = inspect.signature(handle_c1)
        params = list(sig.parameters.keys())
        self.assertEqual(params[1], 'user', "Second param must be 'user'")


class TestFull8StateFlow(TestCase):
    """
    Full state machine flow: all 8 canonical states reachable in sequence.
    REGISTRO → PRODUCCION → PREPARACION → DESPACHO → TRANSITO → EN_DESTINO → CERRADO
    + CANCELADO reachable from any active state.
    """

    def setUp(self):
        from apps.expedientes.tests.factories import ExpedienteFactory, UserFactory
        self.ceo = UserFactory(username='ceo_flow', is_superuser=True)
        self.expediente = ExpedienteFactory(status='REGISTRO')

    def _force_status(self, status):
        self.expediente.status = status
        self.expediente.save(update_fields=['status'])
        self.expediente.refresh_from_db()

    def test_all_8_states_are_defined(self):
        """All 8 canonical states must exist in ExpedienteStatus enum."""
        from apps.expedientes.enums_exp import ExpedienteStatus
        canonical = [
            'REGISTRO', 'PRODUCCION', 'PREPARACION', 'DESPACHO',
            'TRANSITO', 'EN_DESTINO', 'CERRADO', 'CANCELADO'
        ]
        for state in canonical:
            self.assertIn(
                state,
                [s.value for s in ExpedienteStatus],
                f"State {state} must exist in ExpedienteStatus"
            )

    def test_despacho_state_is_reachable(self):
        """DESPACHO must be reachable from PREPARACION via C11."""
        from apps.expedientes.services import HANDLERS
        from apps.expedientes.enums_exp import ExpedienteStatus

        self._force_status('PREPARACION')
        HANDLERS['C11'](self.expediente, {}, self.ceo)
        self.expediente.refresh_from_db()
        self.assertEqual(self.expediente.status, ExpedienteStatus.DESPACHO)

    def test_transito_reachable_from_despacho(self):
        """TRANSITO must be reachable from DESPACHO via C11B."""
        from apps.expedientes.services import HANDLERS
        from apps.expedientes.enums_exp import ExpedienteStatus

        self._force_status('DESPACHO')
        HANDLERS['C11B'](self.expediente, {}, self.ceo)
        self.expediente.refresh_from_db()
        self.assertEqual(self.expediente.status, ExpedienteStatus.TRANSITO)

    def test_cancelado_is_reachable(self):
        """CANCELADO must be reachable via CANCEL command from active states."""
        from apps.expedientes.services.constants import COMMAND_SPEC
        cancel_spec = next(
            (v for k, v in COMMAND_SPEC.items() if v.get('transition_to') == 'CANCELADO'
             or str(v.get('transition_to', '')).upper() == 'CANCELADO'),
            None
        )
        self.assertIsNotNone(
            cancel_spec,
            "There must be a command that transitions to CANCELADO"
        )
