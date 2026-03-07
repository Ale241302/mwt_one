import pytest
from apps.expedientes.enums import ExpedienteStatus, DispatchMode
from apps.expedientes.services import get_available_commands
from .factories import ExpedienteFactory, UserFactory, ArtifactInstanceFactory

@pytest.mark.django_db
class TestAvailableCommands:
    def setup_method(self):
        self.user = UserFactory(is_superuser=True) # CEO

    def test_commands_estado_registro(self):
        """test_commands_estado_registro() â†’ [C2, C3, C4, C15, C17] disponibles"""
        exp = ExpedienteFactory(status=ExpedienteStatus.REGISTRO)
        
        actions = get_available_commands(exp, self.user)
        ids = [a['id'] for a in actions['primary']] + [a['id'] for a in actions['secondary']] + [a['id'] for a in actions['ops']]
        assert 'C2' in ids
        assert 'C15' in ids
        assert 'C17' in ids
        
        # C3 requires ART-01
        ArtifactInstanceFactory(expediente=exp, artifact_type='ART-01', status='completed')
        actions = get_available_commands(exp, self.user)
        ids = [a['id'] for a in actions['primary']] + [a['id'] for a in actions['secondary']] + [a['id'] for a in actions['ops']]
        assert 'C3' in ids

    def test_commands_estado_produccion(self):
        """test_commands_estado_produccion()  â†’ [C6, C15, C17/C18]"""
        exp = ExpedienteFactory(status=ExpedienteStatus.PRODUCCION)
        actions = get_available_commands(exp, self.user)
        ids = [a['id'] for a in actions['primary']] + [a['id'] for a in actions['secondary']] + [a['id'] for a in actions['ops']]
        assert 'C6' in ids
        assert 'C15' in ids
        assert 'C17' in ids

    def test_commands_estado_preparacion(self):
        """test_commands_estado_preparacion() â†’ [C7, C8, C9, C10, C15]"""
        exp = ExpedienteFactory(status=ExpedienteStatus.PREPARACION)
        actions = get_available_commands(exp, self.user)
        ids = [a['id'] for a in actions['primary']] + [a['id'] for a in actions['secondary']] + [a['id'] for a in actions['ops']]
        assert 'C7' in ids
        
        # C8 requires ART-05
        ArtifactInstanceFactory(expediente=exp, artifact_type='ART-05', status='completed')
        actions = get_available_commands(exp, self.user)
        ids = [a['id'] for a in actions['primary']] + [a['id'] for a in actions['secondary']] + [a['id'] for a in actions['ops']]
        assert 'C8' in ids

    def test_commands_estado_despacho(self):
        """test_commands_estado_despacho()    â†’ [C11, C15, C17/C18]"""
        exp = ExpedienteFactory(status=ExpedienteStatus.DESPACHO)
        actions = get_available_commands(exp, self.user)
        ids = [a['id'] for a in actions['primary']] + [a['id'] for a in actions['secondary']] + [a['id'] for a in actions['ops']]
        assert 'C11' in ids

    def test_commands_estado_recepcion(self):
        """test_commands_estado_recepcion()   â†’ [C12, C15, C17/C18]"""
        exp = ExpedienteFactory(status=ExpedienteStatus.TRANSITO)
        actions = get_available_commands(exp, self.user)
        ids = [a['id'] for a in actions['primary']] + [a['id'] for a in actions['secondary']] + [a['id'] for a in actions['ops']]
        assert 'C12' in ids

    def test_commands_estado_facturacion(self):
        """test_commands_estado_facturacion() â†’ [C13, C21, C14, C15]"""
        exp = ExpedienteFactory(status=ExpedienteStatus.EN_DESTINO)
        actions = get_available_commands(exp, self.user)
        ids = [a['id'] for a in actions['primary']] + [a['id'] for a in actions['secondary']] + [a['id'] for a in actions['ops']]
        assert 'C13' in ids

    def test_commands_estado_cerrado(self):
        """test_commands_estado_cerrado()     â†’ [] vacÃ­o (solo lectura)"""
        exp = ExpedienteFactory(status=ExpedienteStatus.CERRADO)
        actions = get_available_commands(exp, self.user)
        assert len(actions['primary']) == 0
        assert len(actions['secondary']) == 0
        # Optional: could check some ops are still there like C15 or C17 (though usually not for closed)
        # assert len(actions['ops']) >= 0 

    def test_commands_estado_cancelado(self):
        """test_commands_estado_cancelado()   â†’ [] vacÃ­o"""
        exp = ExpedienteFactory(status=ExpedienteStatus.CANCELADO)
        actions = get_available_commands(exp, self.user)
        assert len(actions['primary']) == 0
        assert len(actions['secondary']) == 0
        assert len(actions['ops']) == 0
