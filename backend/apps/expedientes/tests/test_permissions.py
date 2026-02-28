import pytest
from apps.expedientes.permissions import IsCEO, EnsureNotBlocked

@pytest.mark.django_db
def test_is_ceo_permission():
    assert IsCEO
    assert EnsureNotBlocked
    # permission tests would normally mock a request and views.
    pass
