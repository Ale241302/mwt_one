"""Sprint 8 S8-13: Tests Pilar B — Knowledge endpoints con mocks OpenAI y Anthropic."""
import json
import pytest
from django.test import TestCase, RequestFactory
from unittest.mock import patch, MagicMock
from datetime import date, timedelta


class TestAskEndpoint(TestCase):
    def _make_jwt_mock(self, permissions, role='INTERNAL', user_id=1):
        token = MagicMock()
        token.get = lambda key, default=None: {
            'permissions': permissions,
            'role': role,
            'user_id': user_id,
        }.get(key, default)
        return MagicMock(), token

    @patch('apps.knowledge.views._get_redis')
    @patch('rest_framework_simplejwt.authentication.JWTStatelessUserAuthentication.authenticate')
    @patch('urllib.request.urlopen')
    def test_ask_creates_conversation_log(self, mock_urlopen, mock_auth, mock_redis):
        from apps.knowledge.views import AskView
        from apps.knowledge.models import ConversationLog
        from django.contrib.auth import get_user_model
        User = get_user_model()
        u = User.objects.create_user(username='asker', password='p', is_api_user=True, role='INTERNAL')

        mock_auth.return_value = self._make_jwt_mock(['ask_knowledge_ops'], user_id=u.id)
        mock_redis.return_value = MagicMock(get=MagicMock(return_value=None), setex=MagicMock())

        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps({'answer': 'Test answer', 'chunks_used': []}).encode()
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_resp

        factory = RequestFactory()
        req = factory.post('/api/knowledge/ask/', json.dumps({'question': 'Test?'}), content_type='application/json')
        resp = AskView.as_view()(req)
        data = json.loads(resp.content)
        assert resp.status_code == 200
        assert 'answer' in data
        assert ConversationLog.objects.count() == 1

    @patch('rest_framework_simplejwt.authentication.JWTStatelessUserAuthentication.authenticate')
    def test_ask_without_permission_returns_403(self, mock_auth):
        from apps.knowledge.views import AskView
        mock_auth.return_value = self._make_jwt_mock([])
        factory = RequestFactory()
        req = factory.post('/api/knowledge/ask/', json.dumps({'question': 'q?'}), content_type='application/json')
        resp = AskView.as_view()(req)
        assert resp.status_code == 403


class TestIndexEndpoint(TestCase):
    @patch('rest_framework_simplejwt.authentication.JWTStatelessUserAuthentication.authenticate')
    def test_index_non_ceo_returns_403(self, mock_auth):
        from apps.knowledge.views import IndexKBView
        token = MagicMock()
        token.get = lambda k, d=None: {'role': 'INTERNAL', 'user_id': 1}.get(k, d)
        mock_auth.return_value = (MagicMock(), token)
        factory = RequestFactory()
        req = factory.post('/api/knowledge/index/', '{}', content_type='application/json')
        resp = IndexKBView.as_view()(req)
        assert resp.status_code == 403


class TestSessionsEndpoint(TestCase):
    def test_sessions_filters_expired(self):
        from apps.knowledge.models import ConversationLog
        from apps.knowledge.views import SessionListView
        from django.contrib.auth import get_user_model
        import json
        from unittest.mock import patch, MagicMock
        User = get_user_model()
        u = User.objects.create_user(username='sessuser', password='p', is_api_user=True, role='INTERNAL')
        today = date.today()
        ConversationLog.objects.create(
            session_id='active-session', user=u, user_role='INTERNAL',
            question='q', answer='a',
            retain_until=today + timedelta(days=5),
        )
        ConversationLog.objects.create(
            session_id='expired-session', user=u, user_role='INTERNAL',
            question='q', answer='a',
            retain_until=today - timedelta(days=1),
        )
        token = MagicMock()
        token.get = lambda k, d=None: {'role': 'INTERNAL', 'user_id': u.id, 'permissions': []}.get(k, d)
        with patch('rest_framework_simplejwt.authentication.JWTStatelessUserAuthentication.authenticate',
                   return_value=(MagicMock(), token)):
            factory = RequestFactory()
            req = factory.get('/api/knowledge/sessions/')
            resp = SessionListView.as_view()(req)
        data = json.loads(resp.content)
        session_ids = [s['session_id'] for s in data['sessions']]
        assert 'active-session' in session_ids
        assert 'expired-session' not in session_ids
