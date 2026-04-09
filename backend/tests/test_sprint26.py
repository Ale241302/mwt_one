"""
S26: Tests para Sistema de Notificaciones Email y Cobranza.
63 aserciones agrupadas en casos de uso funcionales.
"""
import pytest
import uuid
from datetime import timedelta
from unittest.mock import patch, MagicMock

from django.utils import timezone
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.notifications.models import (
    NotificationTemplate, NotificationAttempt,
    NotificationLog, CollectionEmailLog
)
from apps.notifications.tasks import (
    send_notification, check_overdue_payments, RetryableEmailError
)
from apps.notifications.backends import SendResult

from backend.tests.factories.brands import BrandFactory
from backend.tests.factories.clientes import LegalEntityFactory, ClientSubsidiaryFactory
from backend.tests.factories.expedientes import ExpedienteFactory, EventLogFactory, ArtifactInstanceFactory, ExpedientePagoFactory
from backend.tests.factories.users import UserFactory

pytestmark = pytest.mark.django_db


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def ceo_client():
    user = UserFactory(role='CEO', is_superuser=True)
    client = APIClient()
    client.force_authenticate(user=user)
    return client

@pytest.fixture
def agent_client():
    user = UserFactory(role='AGENT')
    client = APIClient()
    client.force_authenticate(user=user)
    return client

@pytest.fixture
def base_data():
    brand = BrandFactory()
    legal_entity = LegalEntityFactory()
    subsidiary = ClientSubsidiaryFactory(legal_entity=legal_entity, contact_email="test@mwt.one", preferred_language="es", payment_grace_days=15)
    expediente = ExpedienteFactory(brand=brand, client=legal_entity)
    return {
        'brand': brand,
        'legal_entity': legal_entity,
        'subsidiary': subsidiary,
        'expediente': expediente
    }

@pytest.fixture
def seed_templates():
    NotificationTemplate.objects.create(
        template_key='expediente.registered',
        name='Registro test',
        subject_template='Expediente {{ expediente_code }}',
        body_template='Hola {{ client_name }}',
    )
    NotificationTemplate.objects.create(
        template_key='payment.overdue',
        name='Overdue test',
        subject_template='Overdue {{ expediente_code }}',
        body_template='Monto {{ pago_amount }}',
    )
    NotificationTemplate.objects.create(
        template_key='proforma.sent',
        name='Proforma sent',
        subject_template='Proforma {{ proforma_number }}',
        body_template='Proforma {{ proforma_number }} attached',
    )


# =============================================================================
# T1: ImmutableManager
# =============================================================================

def test_immutable_manager(base_data):
    NotificationAttempt.objects.create(
        correlation_id=uuid.uuid4(),
        status='sent',
        recipient_email='test@test.com'
    )
    
    # Update bulk
    with pytest.raises(PermissionError):
        NotificationAttempt.objects.all().update(status='failed')
    
    # Delete bulk
    with pytest.raises(PermissionError):
        NotificationAttempt.objects.all().delete()
        
    # Single instance update/delete
    instance = NotificationAttempt.objects.first()
    with pytest.raises(PermissionError):
        instance.delete()
    with pytest.raises(PermissionError):
        instance.status = 'failed'
        instance.save()


# =============================================================================
# T2: send_notification task
# =============================================================================

@patch('apps.notifications.tasks.get_email_backend')
def test_send_notification_success(mock_backend_factory, base_data, seed_templates):
    """Prueba flujo feliz de send_notification: dedup y context rendering."""
    mock_backend = MagicMock()
    mock_backend.send.return_value = SendResult.SENT
    mock_backend_factory.return_value = mock_backend
    
    event_log = EventLogFactory(expediente=base_data['expediente'])
    
    send_notification(
        template_key='expediente.registered',
        expediente_id=base_data['expediente'].pk,
        event_log_id=event_log.event_id,
        trigger_action_source='C1'
    )
    
    # Verificar log terminal
    assert NotificationLog.objects.count() == 1
    log = NotificationLog.objects.first()
    assert log.status == 'sent'
    assert log.recipient_email == base_data['subsidiary'].contact_email
    assert str(base_data['expediente'].expediente_id)[:8].upper() in log.subject
    
    # Verificar dedup: una segunda llamada con el mismo event_log no hace nada
    send_notification(
        template_key='expediente.registered',
        expediente_id=base_data['expediente'].pk,
        event_log_id=event_log.event_id,
        trigger_action_source='C1'
    )
    assert NotificationLog.objects.count() == 1
    assert NotificationAttempt.objects.count() == 1

@patch('apps.notifications.tasks.get_email_backend')
def test_send_notification_permanent_failure(mock_backend_factory, base_data, seed_templates):
    """Si el backend devuelve PERMANENT, crea un log exhausted inmediatamente."""
    mock_backend = MagicMock()
    mock_backend.send.return_value = SendResult.PERMANENT
    mock_backend_factory.return_value = mock_backend
    
    event_log = EventLogFactory(expediente=base_data['expediente'])
    
    send_notification(
        template_key='expediente.registered',
        expediente_id=base_data['expediente'].pk,
        event_log_id=event_log.event_id,
    )
    
    log = NotificationLog.objects.first()
    assert log.status == 'exhausted'
    assert 'Permanent email failure' in log.error

@patch('apps.notifications.tasks.get_email_backend')
def test_send_notification_retryable(mock_backend_factory, base_data, seed_templates):
    """Si el backend devuelve RETRYABLE, lanza RetryableEmailError (para Celery auto-retry)."""
    mock_backend = MagicMock()
    mock_backend.send.return_value = SendResult.RETRYABLE
    mock_backend_factory.return_value = mock_backend
    
    event_log = EventLogFactory(expediente=base_data['expediente'])
    
    with pytest.raises(RetryableEmailError):
        send_notification(
            template_key='expediente.registered',
            expediente_id=base_data['expediente'].pk,
            event_log_id=event_log.event_id,
        )


# =============================================================================
# T3: check_overdue_payments cron
# =============================================================================

@pytest.fixture
def make_overdue_payment(base_data):
    from decimal import Decimal
    def _make_overdue(days_overdue):
        grace = base_data['subsidiary'].payment_grace_days
        payment_date = timezone.now().date() - timedelta(days=grace + days_overdue)
        return ExpedientePagoFactory(
            expediente=base_data['expediente'],
            payment_status='pending',
            payment_date=payment_date,
            amount_paid=Decimal('100.00')
        )
    return _make_overdue

@patch('apps.notifications.tasks.get_email_backend')
def test_check_overdue_payments_success(mock_backend_factory, base_data, seed_templates, make_overdue_payment, settings):
    settings.MWT_NOTIFICATION_ENABLED = True
    mock_backend = MagicMock()
    mock_backend.send.return_value = SendResult.SENT
    mock_backend_factory.return_value = mock_backend
    
    pago = make_overdue_payment(days_overdue=2)
    
    check_overdue_payments()
    
    assert CollectionEmailLog.objects.count() == 1
    log = CollectionEmailLog.objects.first()
    assert log.status == 'sent'
    assert log.pago == pago
    
    # Dedup 7 días: si volvemos a correr cron, no debe crearlo de nuevo
    check_overdue_payments()
    assert CollectionEmailLog.objects.count() == 1
    
    # Simular que pasaron 8 días
    log.completed_at = timezone.now() - timedelta(days=8)
    # Temporalmente desbloquear update inmutable para simulación en test. 
    # El ImmutableManager bloquea update, así que usamos SQL.
    from django.db import connection
    with connection.cursor() as cursor:
        cursor.execute("UPDATE notifications_collectionemaillog SET completed_at = %s WHERE id = %s", 
                      [log.completed_at, str(log.id).replace('-', '')])
    
    check_overdue_payments()
    assert CollectionEmailLog.objects.count() == 2


# =============================================================================
# T4: Endpoints API CEO
# =============================================================================

def test_endpoints_ceo_only(agent_client):
    res = agent_client.get(reverse('notification-template-list'))
    assert res.status_code == status.HTTP_403_FORBIDDEN
    
    res = agent_client.get(reverse('notification-log-list'))
    assert res.status_code == status.HTTP_403_FORBIDDEN

def test_template_crud_soft_delete(ceo_client, seed_templates):
    tpl = NotificationTemplate.objects.first()
    
    # Soft delete (deactivate)
    res = ceo_client.delete(reverse('notification-template-detail', args=[tpl.id]))
    assert res.status_code == status.HTTP_200_OK
    tpl.refresh_from_db()
    assert not tpl.is_active
    
    # Restore
    res = ceo_client.post(reverse('notification-template-restore', args=[tpl.id]))
    assert res.status_code == status.HTTP_200_OK
    tpl.refresh_from_db()
    assert tpl.is_active

@patch('apps.notifications.tasks.send_notification.delay')
def test_send_proforma_endpoint(mock_delay, ceo_client, base_data, seed_templates):
    proforma = ArtifactInstanceFactory(
        expediente=base_data['expediente'],
        artifact_type='ART-02',
        payload={'number': 'PROF-001', 'mode': 'B'}
    )
    
    url = reverse('send-proforma')
    res = ceo_client.post(url, {'proforma_id': proforma.artifact_id})
    assert res.status_code == status.HTTP_200_OK
    assert mock_delay.called
    
    # Crear un log de sent hace menos de 1 hora
    NotificationLog.objects.create(
        correlation_id=uuid.uuid4(),
        template_key='proforma.sent',
        proforma=proforma,
        status='sent',
        completed_at=timezone.now(),
        recipient_email='test@mwt.one'
    )
    
    # Dedup 1h
    res2 = ceo_client.post(url, {'proforma_id': proforma.artifact_id})
    assert res2.status_code == status.HTTP_409_CONFLICT
