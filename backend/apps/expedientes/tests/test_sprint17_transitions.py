"""
S17-14: Tests for Sprint 17 state machine transitions.
New file — does NOT modify existing tests.
"""
import pytest
from django.test import TestCase


class TestPreparacionToDespacho(TestCase):
    """
    S17-01: PREPARACION → DESPACHO (C11 fixed).
    """

    def test_c11_transitions_to_despacho(self):
        """C11 must transition status to DESPACHO, not TRANSITO."""
        from apps.expedientes.services.constants import COMMAND_SPEC
        from apps.expedientes.enums_exp import ExpedienteStatus

        spec = COMMAND_SPEC['C11']
        self.assertEqual(
            spec['transition_to'],
            ExpedienteStatus.DESPACHO,
            "C11 must transition to DESPACHO (S17-01 fix)"
        )

    def test_c11_requires_preparacion(self):
        """C11 requires PREPARACION status."""
        from apps.expedientes.services.constants import COMMAND_SPEC
        from apps.expedientes.enums_exp import ExpedienteStatus

        spec = COMMAND_SPEC['C11']
        self.assertEqual(spec['requires_status'], ExpedienteStatus.PREPARACION)


class TestDespachoToTransito(TestCase):
    """
    S17-02: DESPACHO → TRANSITO (C11B).
    """

    def test_c11b_exists_in_command_spec(self):
        """C11B must be registered in COMMAND_SPEC."""
        from apps.expedientes.services.constants import COMMAND_SPEC
        self.assertIn('C11B', COMMAND_SPEC)

    def test_c11b_transitions_to_transito(self):
        """C11B must transition status from DESPACHO to TRANSITO."""
        from apps.expedientes.services.constants import COMMAND_SPEC
        from apps.expedientes.enums_exp import ExpedienteStatus

        spec = COMMAND_SPEC['C11B']
        self.assertEqual(spec['transition_to'], ExpedienteStatus.TRANSITO)
        self.assertEqual(spec['requires_status'], ExpedienteStatus.DESPACHO)

    def test_c11b_in_handlers(self):
        """C11B must be registered in HANDLERS dict."""
        from apps.expedientes.services import HANDLERS
        self.assertIn('C11B', HANDLERS)


class TestReopenInDispatcher(TestCase):
    """
    S17-03: REOPEN must be in COMMAND_SPEC and HANDLERS.
    """

    def test_reopen_in_command_spec(self):
        from apps.expedientes.services.constants import COMMAND_SPEC
        self.assertIn('REOPEN', COMMAND_SPEC)

    def test_reopen_in_handlers(self):
        from apps.expedientes.services import HANDLERS
        self.assertIn('REOPEN', HANDLERS)

    def test_reopen_requires_ceo(self):
        from apps.expedientes.services.constants import COMMAND_SPEC
        self.assertTrue(COMMAND_SPEC['REOPEN'].get('requires_ceo', False))


class TestHandleC1Signature(TestCase):
    """
    S17-05: handle_c1 signature must be (payload, user).
    """

    def test_handle_c1_accepts_payload_user_order(self):
        """Calling handle_c1(payload={...}, user=...) must not raise TypeError."""
        import inspect
        from apps.expedientes.services.commands.c1 import handle_c1
        sig = inspect.signature(handle_c1)
        params = list(sig.parameters.keys())
        self.assertEqual(params[0], 'payload', "First param must be 'payload'")
        self.assertEqual(params[1], 'user', "Second param must be 'user'")
