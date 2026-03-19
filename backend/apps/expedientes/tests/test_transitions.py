from django.test import TestCase
from apps.expedientes.models import Expediente
from apps.expedientes.enums import ExpedienteStatus, DispatchMode
from apps.expedientes.services import can_transition_to, execute_command
from apps.expedientes.exceptions import TransitionNotAllowedError, ArtifactMissingError
from apps.expedientes.tests.factories import create_expediente, create_user

class TransitionTests(TestCase):
    def setUp(self):
        self.user = create_user()
        self.ceo = create_user(username='ceo', is_superuser=True)
        self.exp = create_expediente(
            mode='IMPORT',
            freight_mode='FCL',
            dispatch_mode=DispatchMode.MWT
        )

    def test_happy_path_transitions_import_fcl_mwt(self):
        # Initial state is REGISTRO
        self.assertEqual(self.exp.status, ExpedienteStatus.REGISTRO)
        
        # Test C2 (OC)
        self.exp, ev = execute_command(self.exp, 'C2', {'file_url': 'a.pdf', 'file_name': 'a.pdf'}, self.user)
        # Test C3 (Proforma)
        self.exp, ev = execute_command(self.exp, 'C3', {'file_url': 'b.pdf', 'file_name': 'b.pdf', 'payload': {'total': 1000, 'total_client_view': 1000}}, self.user)
        # Test C4 (Mode rules) -> requires CEO
        self.exp, ev = execute_command(self.exp, 'C4', {'file_url': 'c.pdf', 'file_name': 'c.pdf'}, self.ceo)
        # Test C5 (SAP) -> Auto-transitions to PRODUCCION
        self.exp, ev = execute_command(self.exp, 'C5', {'file_url': 'd.pdf', 'file_name': 'd.pdf'}, self.user)
        
        self.assertEqual(self.exp.status, ExpedienteStatus.PRODUCCION)
        
        # Test C6 (Confirm Production)
        self.exp, ev = execute_command(self.exp, 'C6', {}, self.user)
        
        # Test C7 (Shipment)
        self.exp, ev = execute_command(self.exp, 'C7', {'file_url': 'e.pdf', 'file_name': 'e.pdf'}, self.user)
        
        # Test C8 (Freight)
        self.exp, ev = execute_command(self.exp, 'C8', {'file_url': 'f.pdf', 'file_name': 'f.pdf'}, self.user)
        
        # Test C9 (Customs - requires mwt)
        self.exp, ev = execute_command(self.exp, 'C9', {'file_url': 'g.pdf', 'file_name': 'g.pdf'}, self.user)
        
        # Test C10 (Approve dispatch) -> Auto transitions to DESPACHO
        self.exp, ev = execute_command(self.exp, 'C10', {'file_url': 'h.pdf', 'file_name': 'h.pdf'}, self.user)
        self.assertEqual(self.exp.status, ExpedienteStatus.DESPACHO)
        
        # Test C11 (Departure)
        self.exp, ev = execute_command(self.exp, 'C11', {}, self.user)
        
        # Test C12 (Arrival)
        self.exp, ev = execute_command(self.exp, 'C12', {}, self.user)
        
        # Test C13 (Invoice)
        self.exp, ev = execute_command(self.exp, 'C13', {
            'file_url': 'i.pdf', 
            'file_name': 'i.pdf',
            'payload': {'total': 1000, 'total_client_view': 1000}
        }, self.user)
        
        # Test C21 (Payment) -> Complete total
        self.exp, ev = execute_command(self.exp, 'C21', {
            'amount': 1000, 
            'currency': 'USD',
            'method': 'WIRE',
            'reference': 'REF'
        }, self.ceo)
        
        # Test C14 (Close)
        self.exp.payment_status = 'paid'; self.exp.save(); self.exp, ev = execute_command(self.exp, 'C14', {}, self.user)
        self.assertEqual(self.exp.status, ExpedienteStatus.CERRADO)

    def test_invalid_transitions(self):
        # Cannot confirm production (C6) while in REGISTRO
        self.assertFalse(can_transition_to(self.exp, ExpedienteStatus.PRODUCCION))

class ParametricMatrixTests(TestCase):
    def setUp(self):
        self.user = create_user(username='staff')
        self.ceo = create_user(username='ceo', is_superuser=True)
        self.exp = create_expediente(mode='IMPORT', brand='MARLUVAS', dispatch_mode=DispatchMode.MWT)

    def test_command_guards_matrix(self):
        """
        Matrix test for commands against states where they should FAIL.
        Focus: S11-08A exhaustive verification.
        """
        # Command -> (Invalid status for that command, Exception to expect)
        # Note: Transfer and Portal/Products often trigger C15, C21, C22 etc.
        matrix = [
            ('C2', ExpedienteStatus.PRODUCCION, TransitionNotAllowedError),
            ('C6', ExpedienteStatus.REGISTRO, TransitionNotAllowedError),
            ('C7', ExpedienteStatus.PRODUCCION, TransitionNotAllowedError),
            ('C11', ExpedienteStatus.REGISTRO, TransitionNotAllowedError),
            ('C12', ExpedienteStatus.REGISTRO, TransitionNotAllowedError),
            ('C13', ExpedienteStatus.REGISTRO, TransitionNotAllowedError),
            ('C14', ExpedienteStatus.EN_DESTINO, ArtifactMissingError), # Missing ART-09
        ]

        for cmd, status, exc in matrix:
            self.exp.status = status
            self.exp.save()
            with self.subTest(cmd=cmd, status=status):
                with self.assertRaises(exc):
                    execute_command(self.exp, cmd, {}, self.user)

    def test_ceo_only_commands(self):
        """Verify C16, C18, C22, C23, C24 require superuser."""
        ceo_cmds = ['C16', 'C18', 'C22', 'C23', 'C24']
        self.exp.status = ExpedienteStatus.REGISTRO
        self.exp.save()
        
        # C16 specifically is allowed from REGISTRO
        from rest_framework.exceptions import PermissionDenied
        for cmd in ceo_cmds:
            with self.subTest(cmd=cmd):
                with self.assertRaises(PermissionDenied):
                    execute_command(self.exp, cmd, {}, self.user)

    def test_portal_and_products_logical_integrity(self):
        """
        Verify transition logic for products (C22 Commission Invoice) 
        and portal (C30 Logistics Decision).
        """
        # C22 (Commission Invoice) - CEO ONLY
        self.exp.mode = 'COMISION'
        self.exp.save()
        
        # Should fail for normal user
        from rest_framework.exceptions import PermissionDenied
        with self.assertRaises(PermissionDenied):
            execute_command(self.exp, 'C22', {}, self.user)
            
        # Should work for CEO even in REGISTRO (C22 allows not in CERRADO/CANCELADO)
        # Note: creates_art ART-10
        self.exp, evs = execute_command(self.exp, 'C22', {}, self.ceo)
        self.assertTrue(self.exp.artifacts.filter(artifact_type='ART-10').exists())

        # C30 (Materialize Logistics) - Focus Phase 0 Rule 1
        # Requires ART-04 + status in (PRODUCCION, PREPARACION)
        self.exp.status = ExpedienteStatus.REGISTRO
        self.exp.save()
        with self.assertRaises(TransitionNotAllowedError): # Not in valid state for C30
            execute_command(self.exp, 'C30', {}, self.ceo)
            
        # Move to PRODUCCION
        self.exp.status = ExpedienteStatus.PRODUCCION
        self.exp.save()
        # Still fails because missing ART-04
        with self.assertRaises(ArtifactMissingError):
            execute_command(self.exp, 'C30', {}, self.ceo)
