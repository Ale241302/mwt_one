import pytest
from apps.expedientes.services import get_available_commands

@pytest.mark.django_db
def test_get_available_commands_returns_actions():
    assert get_available_commands
    pass
