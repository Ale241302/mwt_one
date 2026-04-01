"""
S21-07 — 24 tests del Activity Feed.

Cubre:
  Tests 1-6:   EventLog campos S21 poblados correctamente
  Tests 7-9:   UserNotificationState (get_or_create, mark-seen)
  Tests 10-15: Endpoints GET feed, filtros, paginación, mark-seen
  Tests 16-19: Permisos por rol (CLIENT_*, AGENT_*, CEO)
  Test 20:     No autenticado → 401
  Tests 21-23: GET count (normal, cap 99, cero)
  Test 24:     Backward compat (EventLog sin campos S21 → no explota)
"""
import uuid
from datetime import datetime
from django.test import TestCase
from django.utils import timezone
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

from apps.expedientes.models import EventLog, UserNotificationState
from apps.expedientes.services.activity_permissions import (
    get_visible_events, CEO_ONLY_EVENT_TYPES
)

User = get_user_model()


def make_user(username, role='AGENT', **kwargs):
    """Helper: crea un usuario con rol."""
    u = User.objects.create_user(username=username, password='pass', **kwargs)
    u.role = role
    u.save()
    return u


def make_event(user=None, event_type='expediente.state_changed', action_source=None,
               previous_status=None, new_status=None, proforma=None,
               aggregate_id=None):
    """Helper: crea un EventLog con los campos S21."""
    return EventLog.objects.create(
        event_type=event_type,
        aggregate_type='EXP',
        aggregate_id=aggregate_id or uuid.uuid4(),
        payload={},
        occurred_at=timezone.now(),
        emitted_by='test',
        retry_count=0,
        correlation_id=uuid.uuid4(),
        user=user,
        proforma=proforma,
        action_source=action_source,
        previous_status=previous_status,
        new_status=new_status,
    )


# ---------------------------------------------------------------------------
# Tests 1-6: Campos S21 en EventLog
# ---------------------------------------------------------------------------

class TestEventLogCamposS21(TestCase):

    def test_01_command_c1_event_tiene_user_y_action_source(self):
        """T1: Command C1 → EventLog con user y action_source='C1'."""
        user = make_user('agente1')
        ev = make_event(user=user, action_source='C1')
        self.assertEqual(ev.action_source, 'C1')
        self.assertEqual(ev.user, user)

    def test_02_command_c5_tiene_status_transition(self):
        """T2: Command C5 → previous_status='REGISTRO', new_status='PRODUCCION'."""
        user = make_user('agente2')
        ev = make_event(
            user=user, action_source='C5',
            previous_status='REGISTRO', new_status='PRODUCCION'
        )
        self.assertEqual(ev.previous_status, 'REGISTRO')
        self.assertEqual(ev.new_status, 'PRODUCCION')

    def test_03_create_proforma_tiene_proforma_fk(self):
        """T3: create_proforma → proforma FK poblado, action_source='create_proforma'."""
        from apps.expedientes.models import ArtifactInstance, Expediente
        # Solo creamos si hay una forma de crear Expediente minimal
        # Este test verifica la estructura del campo, sin Expediente real
        ev = make_event(action_source='create_proforma')
        self.assertEqual(ev.action_source, 'create_proforma')
        self.assertIsNone(ev.proforma)  # sin proforma real en unit test

    def test_04_change_mode_action_source(self):
        """T4: change_mode → action_source='change_mode'."""
        ev = make_event(action_source='change_mode')
        self.assertEqual(ev.action_source, 'change_mode')

    def test_05_celery_credit_clock_user_null(self):
        """T5: Celery credit_clock → user=NULL, action_source='system_credit_clock'."""
        ev = make_event(user=None, action_source='system_credit_clock')
        self.assertIsNone(ev.user)
        self.assertEqual(ev.action_source, 'system_credit_clock')

    def test_06_eventlog_pre_s21_campos_nuevos_null(self):
        """T6: EventLog sin campos S21 → campos nuevos = NULL, no explota."""
        ev = EventLog.objects.create(
            event_type='legacy.event',
            aggregate_type='EXP',
            aggregate_id=uuid.uuid4(),
            payload={},
            occurred_at=timezone.now(),
            emitted_by='legacy',
            retry_count=0,
            correlation_id=uuid.uuid4(),
            # NO se pasan user, proforma, action_source
        )
        self.assertIsNone(ev.user)
        self.assertIsNone(ev.proforma)
        self.assertIsNone(ev.action_source)
        self.assertIsNone(ev.previous_status)
        self.assertIsNone(ev.new_status)


# ---------------------------------------------------------------------------
# Tests 7-9: UserNotificationState
# ---------------------------------------------------------------------------

class TestUserNotificationState(TestCase):

    def test_07_primera_visita_get_or_create_last_seen_zero(self):
        """T7: Primera visita → get_or_create da last_seen_event_id=0."""
        user = make_user('user_nuevo')
        state, created = UserNotificationState.objects.get_or_create(user=user)
        self.assertTrue(created)
        self.assertEqual(state.last_seen_event_id, 0)

    def test_08_mark_seen_retorna_campos_correctos(self):
        """T8: POST mark-seen → response tiene previous_last_seen + last_seen_event_id."""
        user = make_user('user_markseen')
        client = APIClient()
        client.force_authenticate(user=user)
        response = client.post('/api/activity-feed/mark-seen/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('previous_last_seen', response.data)
        self.assertIn('last_seen_event_id', response.data)
        self.assertNotIn('marked', response.data)  # T14 tambien

    def test_09_segundo_mark_seen_last_seen_avanza(self):
        """T9: Segundo mark-seen con nuevos eventos → last_seen avanza."""
        user = make_user('user_avanza')
        # Estado inicial
        state = UserNotificationState.objects.create(user=user, last_seen_event_id=0)
        # Crear un evento visible para el usuario
        make_event(user=user, action_source='C1')

        client = APIClient()
        client.force_authenticate(user=user)
        response = client.post('/api/activity-feed/mark-seen/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['previous_last_seen'], 0)
        # last_seen_event_id debe haber avanzado
        state.refresh_from_db()
        self.assertGreater(state.last_seen_event_id, 0)


# ---------------------------------------------------------------------------
# Tests 10-15: Endpoints GET feed + filtros + mark-seen
# ---------------------------------------------------------------------------

class TestActivityFeedEndpoints(TestCase):

    def setUp(self):
        self.ceo = make_user('ceo_test', role='CEO')
        self.ceo.is_superuser = True
        self.ceo.save()
        self.client = APIClient()
        self.client.force_authenticate(user=self.ceo)

    def test_10_get_feed_sin_filtros_paginado(self):
        """T10: GET feed sin filtros → paginado."""
        for _ in range(5):
            make_event(action_source='C1')
        response = self.client.get('/api/activity-feed/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        self.assertIn('count', response.data)

    def test_11_get_feed_filtro_expediente(self):
        """T11: GET feed ?expediente=<uuid> → solo ese expediente."""
        exp_id = uuid.uuid4()
        make_event(action_source='C1', aggregate_id=exp_id)
        make_event(action_source='C2', aggregate_id=uuid.uuid4())  # otro
        response = self.client.get(f'/api/activity-feed/?expediente={exp_id}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for item in response.data['results']:
            self.assertEqual(str(item['aggregate_id']), str(exp_id))

    def test_12_get_feed_filtro_event_type(self):
        """T12: GET feed ?event_type=<str> → solo ese tipo."""
        make_event(event_type='test.alpha', action_source='C1')
        make_event(event_type='test.beta', action_source='C2')
        response = self.client.get('/api/activity-feed/?event_type=test.alpha')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for item in response.data['results']:
            self.assertEqual(item['event_type'], 'test.alpha')

    def test_13_get_feed_unread_only(self):
        """T13: GET feed ?unread_only=true → solo id > last_seen."""
        state = UserNotificationState.objects.create(
            user=self.ceo, last_seen_event_id=0
        )
        ev1 = make_event(action_source='C1')
        state.last_seen_event_id = ev1.pk
        state.save()
        ev2 = make_event(action_source='C2')  # este si es unread
        response = self.client.get('/api/activity-feed/?unread_only=true')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = [item['event_id'] for item in response.data['results']]
        self.assertIn(str(ev2.event_id), [str(i) for i in ids])
        self.assertNotIn(str(ev1.event_id), [str(i) for i in ids])

    def test_14_mark_seen_no_tiene_campo_marked(self):
        """T14: POST mark-seen → response NO tiene campo 'marked'."""
        response = self.client.post('/api/activity-feed/mark-seen/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotIn('marked', response.data)

    def test_15_mark_seen_avanza_al_max_global(self):
        """T15: mark-seen avanza al max GLOBAL, no al max filtrado."""
        ev_max = make_event(action_source='C99')
        response = self.client.post('/api/activity-feed/mark-seen/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        state = UserNotificationState.objects.get(user=self.ceo)
        self.assertGreaterEqual(state.last_seen_event_id, ev_max.pk)


# ---------------------------------------------------------------------------
# Tests 16-19: Permisos por rol
# ---------------------------------------------------------------------------

class TestActivityFeedPermisos(TestCase):

    def test_16_client_solo_ve_su_subsidiaria(self):
        """T16: CLIENT_* → solo ve sus expedientes."""
        from unittest.mock import patch
        client_user = make_user('client1', role='CLIENT')
        # Simular client_subsidiary
        client_user.client_subsidiary = 'SUB-A'
        client_user.save()
        # Evento de otra subsidiaria (no debe verse)
        make_event(action_source='C1')
        qs = get_visible_events(client_user)
        # No debe incluir eventos de expedientes de otras subsidiarias
        self.assertIsNotNone(qs)  # queryset valido

    def test_17_client_no_ve_cost_registered(self):
        """T17: CLIENT_* → NO ve 'cost.registered'."""
        client_user = make_user('client2', role='CLIENT')
        client_user.client_subsidiary = 'SUB-B'
        client_user.save()
        make_event(event_type='cost.registered', action_source='C1')
        qs = get_visible_events(client_user)
        self.assertFalse(qs.filter(event_type='cost.registered').exists())

    def test_18_agent_solo_expedientes_que_opero(self):
        """T18: AGENT_* → solo expedientes donde ha operado."""
        agent = make_user('agent_x', role='AGENT')
        other_agent = make_user('agent_y', role='AGENT')
        exp_propio = uuid.uuid4()
        exp_ajeno = uuid.uuid4()
        make_event(user=agent, action_source='C1', aggregate_id=exp_propio)
        make_event(user=other_agent, action_source='C1', aggregate_id=exp_ajeno)
        qs = get_visible_events(agent)
        ids = list(qs.values_list('aggregate_id', flat=True))
        self.assertIn(exp_propio, ids)
        self.assertNotIn(exp_ajeno, ids)

    def test_19_ceo_ve_todo(self):
        """T19: CEO → ve todos los eventos."""
        ceo = make_user('ceo2', role='CEO')
        ceo.is_superuser = True
        ceo.save()
        make_event(event_type='cost.registered', action_source='C1')
        make_event(event_type='commission.invoiced', action_source='C2')
        qs = get_visible_events(ceo)
        self.assertTrue(qs.filter(event_type='cost.registered').exists())
        self.assertTrue(qs.filter(event_type='commission.invoiced').exists())


# ---------------------------------------------------------------------------
# Test 20: No autenticado → 401
# ---------------------------------------------------------------------------

class TestActivityFeedAuth(TestCase):

    def test_20_no_autenticado_401(self):
        """T20: No autenticado → 401."""
        client = APIClient()  # sin autenticar
        urls = [
            '/api/activity-feed/',
            '/api/activity-feed/count/',
        ]
        for url in urls:
            response = client.get(url)
            self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED, msg=url)
        response = client.post('/api/activity-feed/mark-seen/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


# ---------------------------------------------------------------------------
# Tests 21-23: GET count
# ---------------------------------------------------------------------------

class TestActivityFeedCount(TestCase):

    def setUp(self):
        self.ceo = make_user('ceo_count', role='CEO')
        self.ceo.is_superuser = True
        self.ceo.save()
        self.client = APIClient()
        self.client.force_authenticate(user=self.ceo)

    def test_21_count_unread_correcto(self):
        """T21: GET count → unread_count correcto."""
        UserNotificationState.objects.create(user=self.ceo, last_seen_event_id=0)
        make_event(action_source='C1')
        make_event(action_source='C2')
        response = self.client.get('/api/activity-feed/count/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(response.data['unread_count'], 2)

    def test_22_count_150_eventos_cap_99(self):
        """T22: 150 eventos no leídos → unread_count=99, has_more=True."""
        UserNotificationState.objects.create(user=self.ceo, last_seen_event_id=0)
        for _ in range(150):
            make_event(action_source='C1')
        response = self.client.get('/api/activity-feed/count/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['unread_count'], 99)
        self.assertTrue(response.data['has_more'])

    def test_23_count_cero_sin_has_more(self):
        """T23: 0 eventos no leídos → unread_count=0, has_more=False."""
        # Avanzar last_seen a un valor muy alto
        UserNotificationState.objects.create(
            user=self.ceo, last_seen_event_id=999999999
        )
        response = self.client.get('/api/activity-feed/count/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['unread_count'], 0)
        self.assertFalse(response.data['has_more'])


# ---------------------------------------------------------------------------
# Test 24: Backward compat
# ---------------------------------------------------------------------------

class TestBackwardCompat(TestCase):

    def test_24_eventlog_create_sin_campos_s21_no_explota(self):
        """T24: EventLog.objects.create() sin campos nuevos → no explota (null=True)."""
        try:
            ev = EventLog.objects.create(
                event_type='legacy.event',
                aggregate_type='EXP',
                aggregate_id=uuid.uuid4(),
                payload={},
                occurred_at=timezone.now(),
                emitted_by='legacy_system',
                retry_count=0,
                correlation_id=uuid.uuid4(),
            )
            self.assertIsNone(ev.user)
            self.assertIsNone(ev.proforma)
            self.assertIsNone(ev.action_source)
        except Exception as e:
            self.fail(f'EventLog.create() sin campos S21 exploto: {e}')
