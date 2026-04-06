from django.test import TestCase
from unittest.mock import patch
from apps.commercial.models import BrandArtifactPolicyVersion
from apps.commercial.services.artifact_policy import (
    resolve_artifact_policy,
    update_artifact_policy,
)
from apps.changelog.models import ConfigChangeLog
from apps.eventlog.models import EventLog
from apps.brands.models import Brand


FALLBACK_POLICY = {"default": True}


class TestArtifactPolicyT11(TestCase):
    """T11: resolve_artifact_policy() and update_artifact_policy()"""

    def setUp(self):
        self.brand = Brand.objects.create(name="BrandPolicy")

    def test_t11a_returns_active_db_policy(self):
        BrandArtifactPolicyVersion.objects.create(
            brand=self.brand,
            version=1,
            artifact_policy={"rule": "strict"},
            is_active=True,
        )
        result = resolve_artifact_policy(brand=self.brand)
        self.assertEqual(result["rule"], "strict")

    def test_t11b_no_db_version_returns_fallback(self):
        with patch(
            "apps.commercial.services.artifact_policy.ARTIFACT_POLICY",
            FALLBACK_POLICY,
        ):
            result = resolve_artifact_policy(brand=self.brand)
        self.assertEqual(result, FALLBACK_POLICY)

    def test_t11c_update_creates_new_version_and_deactivates_old(self):
        v1 = BrandArtifactPolicyVersion.objects.create(
            brand=self.brand,
            version=1,
            artifact_policy={"rule": "old"},
            is_active=True,
        )
        update_artifact_policy(
            brand=self.brand,
            new_policy={"rule": "new"},
            changed_by_description="Test",
        )
        v1.refresh_from_db()
        self.assertFalse(v1.is_active)
        self.assertIsNotNone(v1.superseded_by)
        v2 = BrandArtifactPolicyVersion.objects.get(brand=self.brand, version=2)
        self.assertTrue(v2.is_active)
        log = ConfigChangeLog.objects.filter(action="update_artifact_policy").first()
        self.assertIsNotNone(log)

    def test_t11d_multiple_active_emits_integrity_error_log(self):
        # Force two active records (bypassing constraint for test)
        BrandArtifactPolicyVersion.objects.bulk_create([
            BrandArtifactPolicyVersion(brand=self.brand, version=1, artifact_policy={"r": "1"}, is_active=True),
            BrandArtifactPolicyVersion(brand=self.brand, version=2, artifact_policy={"r": "2"}, is_active=True),
        ])
        resolve_artifact_policy(brand=self.brand)
        log = EventLog.objects.filter(event_type="artifact_policy.integrity_error").first()
        self.assertIsNotNone(log)

    def test_t11e_unique_constraint_only_one_active_per_brand(self):
        from django.db import IntegrityError
        BrandArtifactPolicyVersion.objects.create(
            brand=self.brand, version=1, artifact_policy={"r": "1"}, is_active=True
        )
        with self.assertRaises(IntegrityError):
            BrandArtifactPolicyVersion.objects.create(
                brand=self.brand, version=2, artifact_policy={"r": "2"}, is_active=True
            )
