import pytest
import datetime
from django.utils import timezone
import uuid

from apps.expedientes.models import Expediente, LegalEntity, EventLog
from apps.expedientes.tasks import evaluar_relojes_credito

@pytest.fixture
def make_entities():
    le = LegalEntity.objects.create(entity_id="MWT-1", legal_name="MWT", country="CR", role="OPERATOR", relationship_to_mwt="INTERNAL", frontend="APP", visibility_level="PUBLIC", pricing_visibility="ALL")
    client = LegalEntity.objects.create(entity_id="CLI-1", legal_name="Client", country="CR", role="CLIENT", relationship_to_mwt="EXTERNAL", frontend="NONE", visibility_level="PRIVATE", pricing_visibility="NONE")
    return le, client

@pytest.mark.django_db
def test_evaluate_credit_clocks_no_active_expedientes():
    evaluar_relojes_credito()
    assert EventLog.objects.filter(event_type="WARNING_60_DIAS").count() == 0

@pytest.mark.django_db
def test_evaluate_credit_clocks_60_days_warning(make_entities):
    le, client = make_entities
    started_at = timezone.now() - datetime.timedelta(days=61)
    exp = Expediente.objects.create(
        expediente_id=uuid.uuid4(),
        legal_entity=le,
        client=client,
        credit_clock_started_at=started_at,
        is_blocked=False,
        status="PRODUCCION"
    )
    evaluar_relojes_credito()
    events = EventLog.objects.filter(event_type="WARNING_60_DIAS", aggregate_id=str(exp.expediente_id))
    assert events.count() == 1

@pytest.mark.django_db
def test_evaluate_credit_clocks_75_days_warning(make_entities):
    le, client = make_entities
    started_at = timezone.now() - datetime.timedelta(days=76)
    exp = Expediente.objects.create(
        expediente_id=uuid.uuid4(),
        legal_entity=le,
        client=client,
        credit_clock_started_at=started_at,
        is_blocked=False,
        status="PRODUCCION"
    )
    evaluar_relojes_credito()
    events = EventLog.objects.filter(event_type="WARNING_75_DIAS", aggregate_id=str(exp.expediente_id))
    assert events.count() == 1

@pytest.mark.django_db
def test_evaluate_credit_clocks_90_days_block(make_entities):
    le, client = make_entities
    started_at = timezone.now() - datetime.timedelta(days=91)
    exp = Expediente.objects.create(
        expediente_id=uuid.uuid4(),
        legal_entity=le,
        client=client,
        credit_clock_started_at=started_at,
        is_blocked=False,
        status="PRODUCCION"
    )
    evaluar_relojes_credito()
    warnings = EventLog.objects.filter(event_type="WARNING_60_DIAS", aggregate_id=str(exp.expediente_id))
    assert warnings.count() == 0
    blocks = EventLog.objects.filter(event_type="BLOCKED_POR_MORA", aggregate_id=str(exp.expediente_id))
    assert blocks.count() == 1
    exp.refresh_from_db()
    assert exp.is_blocked is True

@pytest.mark.django_db
def test_evaluate_credit_clocks_idempotent(make_entities):
    le, client = make_entities
    started_at = timezone.now() - datetime.timedelta(days=91)
    exp = Expediente.objects.create(
        expediente_id=uuid.uuid4(),
        legal_entity=le,
        client=client,
        credit_clock_started_at=started_at,
        is_blocked=True,
        blocked_reason="credit_clock_expired",
        status="PRODUCCION"
    )
    evaluar_relojes_credito()
    blocks = EventLog.objects.filter(event_type="BLOCKED_POR_MORA", aggregate_id=str(exp.expediente_id))
    assert blocks.count() == 0

@pytest.mark.django_db
def test_evaluate_credit_clocks_ignores_terminal_states(make_entities):
    le, client = make_entities
    started_at = timezone.now() - datetime.timedelta(days=91)
    # CERRADO is a terminal state
    exp = Expediente.objects.create(
        expediente_id=uuid.uuid4(),
        legal_entity=le,
        client=client,
        credit_clock_started_at=started_at,
        is_blocked=False,
        status="CERRADO"
    )
    evaluar_relojes_credito()
    assert exp.is_blocked is False
    assert EventLog.objects.filter(aggregate_id=str(exp.expediente_id)).count() == 0

@pytest.mark.django_db
def test_evaluate_credit_clocks_ignores_missing_start_time(make_entities):
    le, client = make_entities
    exp = Expediente.objects.create(
        expediente_id=uuid.uuid4(),
        legal_entity=le,
        client=client,
        credit_clock_started_at=None,
        is_blocked=False,
        status="PRODUCCION"
    )
    evaluar_relojes_credito()
    assert exp.is_blocked is False
    assert EventLog.objects.filter(aggregate_id=str(exp.expediente_id)).count() == 0

@pytest.mark.django_db
def test_evaluate_credit_clocks_59_days_no_action(make_entities):
    le, client = make_entities
    started_at = timezone.now() - datetime.timedelta(days=59)
    exp = Expediente.objects.create(
        expediente_id=uuid.uuid4(),
        legal_entity=le,
        client=client,
        credit_clock_started_at=started_at,
        is_blocked=False,
        status="PRODUCCION"
    )
    evaluar_relojes_credito()
    assert EventLog.objects.filter(aggregate_id=str(exp.expediente_id)).count() == 0
