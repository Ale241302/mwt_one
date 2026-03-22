from rest_framework.test import APITestCase
from django.urls import reverse
from rest_framework import status
from apps.users.models import MWTUser, UserRole
from apps.expedientes.models import Expediente, EventLog

class Phase1CEOOverrideTests(APITestCase):
    def setUp(self):
        self.ceo = MWTUser.objects.create_user(
            email="ceo@example.com",
            password="password",
            role=UserRole.CEO,
            is_superuser=True
        )
        self.normal_user = MWTUser.objects.create_user(
            email="user@example.com",
            password="password",
            role=UserRole.OPERATIONS
        )
        self.expediente = Expediente.objects.create(
            status="draft",
            client="Test Client"
        )
        self.url = reverse('expedientes:ceo-override', args=[self.expediente.id])

    def test_24_override_success(self):
        """Test #24: CEO can override state."""
        self.client.force_authenticate(user=self.ceo)
        data = {"target_state": "confirmed", "reason": "Exec decision"}
        res = self.client.post(self.url, data)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.expediente.refresh_from_db()
        self.assertEqual(self.expediente.status, "confirmed")

    def test_25_override_creates_log(self):
        """Test #25: Override creates EventLog."""
        self.client.force_authenticate(user=self.ceo)
        data = {"target_state": "confirmed", "reason": "Exec decision"}
        self.client.post(self.url, data)
        logs = EventLog.objects.filter(expediente=self.expediente)
        self.assertGreaterEqual(logs.count(), 1)
        # Checking if description contains 'CEO Override' or if standard log was created
        found = any("CEO Override" in log.description or "Estado" in log.description for log in logs)
        self.assertTrue(found)

    def test_26_override_rejected_non_ceo(self):
        """Test #26: Non-superuser rejected."""
        self.client.force_authenticate(user=self.normal_user)
        data = {"target_state": "confirmed", "reason": "Exec decision"}
        res = self.client.post(self.url, data)
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_27_override_missing_target(self):
        """Test #27: Missing target state."""
        self.client.force_authenticate(user=self.ceo)
        res = self.client.post(self.url, {"reason": "Test"})
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_28_override_missing_reason(self):
        """Test #28: Missing reason."""
        self.client.force_authenticate(user=self.ceo)
        res = self.client.post(self.url, {"target_state": "confirmed"})
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_29_override_unknown_expediente(self):
        """Test #29: Unknown expediente."""
        self.client.force_authenticate(user=self.ceo)
        import uuid
        url = reverse('expedientes:ceo-override', args=[uuid.uuid4()])
        res = self.client.post(url, {"target_state": "confirmed", "reason": "Test"})
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_30_override_changes_block(self):
        """Test #30: Override removes block if is_blocked passed."""
        self.expediente.is_blocked = True
        self.expediente.save()
        self.client.force_authenticate(user=self.ceo)
        res = self.client.post(self.url, {
            "target_state": "draft",
            "reason": "Unblock",
            "is_blocked": False
        })
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.expediente.refresh_from_db()
        self.assertFalse(self.expediente.is_blocked)
