"""
T11 — BrandArtifactPolicyVersion + resolve_artifact_policy() + update_artifact_policy()
"""
from django.test import TestCase
from unittest.mock import patch

from apps.commercial.models import BrandArtifactPolicyVersion
from apps.commercial.services.artifact_policy import (
    resolve_artifact_policy,
    update_artifact_policy,
)
from apps.audit.models import ConfigChangeLog


def make_brand(slug='brand-ap'):
    from apps.brands.models import Brand
    return Brand.objects.get_or_create(slug=slug, defaults={'name': f'Brand {slug}'})[0]


def make_user():
    from apps.users.models import MWTUser, UserRole
    user, _ = MWTUser.objects.get_or_create(
        username='ceo-ap', defaults={'role': UserRole.CEO, 'email': 'ceo-ap@test.com'}
    )
    return user


SAMPLE_POLICY = {
    'documents': ['invoice', 'packing_list'],
    'requires_signature': True,
}

SAMPLE_POLICY_V2 = {
    'documents': ['invoice', 'packing_list', 'certificate'],
    'requires_signature': True,
}


class T11ArtifactPolicyResolveTest(TestCase):
    """T11-a/b — resolve_artifact_policy(): DB primero, fallback Python."""

    def setUp(self):
        self.brand = make_brand()

    def test_T11a_returns_active_db_policy(self):
        BrandArtifactPolicyVersion.objects.create(
            brand=self.brand,
            version=1,
            artifact_policy=SAMPLE_POLICY,
            is_active=True,
        )
        result = resolve_artifact_policy(self.brand.slug)
        self.assertEqual(result, SAMPLE_POLICY)

    def test_T11b_fallback_when_no_db_version(self):
        fallback = {'default_key': 'default_value'}
        with patch(
            'apps.commercial.services.artifact_policy._get_fallback_policy',
            return_value=fallback
        ):
            result = resolve_artifact_policy(self.brand.slug)
        self.assertEqual(result, fallback)

    def test_T11b_fallback_returns_empty_dict_on_import_error(self):
        result = resolve_artifact_policy('nonexistent-brand-slug-xyz')
        # Sin versión en DB y sin ARTIFACT_POLICY importable → {} o valor del fallback
        self.assertIsInstance(result, dict)


class T11ArtifactPolicyUpdateTest(TestCase):
    """T11-c/e — update_artifact_policy(): versionado append-only."""

    def setUp(self):
        self.brand = make_brand(slug='brand-ap-update')
        self.user = make_user()

    def test_T11c_creates_v1_no_previous(self):
        new_version = update_artifact_policy(
            brand_slug=self.brand.slug,
            new_policy=SAMPLE_POLICY,
            notes='Initial version',
            changed_by=self.user,
        )
        self.assertEqual(new_version.version, 1)
        self.assertTrue(new_version.is_active)
        self.assertEqual(new_version.artifact_policy, SAMPLE_POLICY)

        log = ConfigChangeLog.objects.filter(
            model_name='BrandArtifactPolicyVersion',
            record_id=str(new_version.id),
        ).first()
        self.assertIsNotNone(log)
        self.assertEqual(log.action, 'create')

    def test_T11c_creates_v2_deactivates_v1(self):
        v1 = update_artifact_policy(
            brand_slug=self.brand.slug,
            new_policy=SAMPLE_POLICY,
            changed_by=self.user,
        )
        v2 = update_artifact_policy(
            brand_slug=self.brand.slug,
            new_policy=SAMPLE_POLICY_V2,
            notes='V2',
            changed_by=self.user,
        )
        v1.refresh_from_db()
        self.assertFalse(v1.is_active)
        self.assertTrue(v2.is_active)
        self.assertEqual(v2.version, 2)
        self.assertEqual(v1.superseded_by, v2)

    def test_T11e_only_one_active_per_brand_after_update(self):
        update_artifact_policy(brand_slug=self.brand.slug, new_policy=SAMPLE_POLICY, changed_by=self.user)
        update_artifact_policy(brand_slug=self.brand.slug, new_policy=SAMPLE_POLICY_V2, changed_by=self.user)
        active_count = BrandArtifactPolicyVersion.objects.filter(
            brand=self.brand, is_active=True
        ).count()
        self.assertEqual(active_count, 1)

    def test_T11c_config_change_log_created(self):
        initial_count = ConfigChangeLog.objects.count()
        update_artifact_policy(
            brand_slug=self.brand.slug,
            new_policy=SAMPLE_POLICY,
            changed_by=self.user,
        )
        self.assertEqual(ConfigChangeLog.objects.count(), initial_count + 1)

    def test_T11_resolve_returns_updated_policy_after_update(self):
        update_artifact_policy(brand_slug=self.brand.slug, new_policy=SAMPLE_POLICY, changed_by=self.user)
        update_artifact_policy(brand_slug=self.brand.slug, new_policy=SAMPLE_POLICY_V2, changed_by=self.user)
        result = resolve_artifact_policy(self.brand.slug)
        self.assertEqual(result, SAMPLE_POLICY_V2)


class T11dIntegrityErrorTest(TestCase):
    """T11-d — MultipleObjectsReturned emite ConfigChangeLog(integrity_error)."""

    def setUp(self):
        self.brand = make_brand(slug='brand-ap-integrity')

    def test_T11d_multiple_active_emits_integrity_log(self):
        # Forzar dos versiones activas (bypass constraints usando bulk_create directo)
        BrandArtifactPolicyVersion.objects.bulk_create([
            BrandArtifactPolicyVersion(
                brand=self.brand, version=1, artifact_policy={'k': 'v1'}, is_active=True
            ),
            BrandArtifactPolicyVersion(
                brand=self.brand, version=2, artifact_policy={'k': 'v2'}, is_active=True
            ),
        ])
        initial_count = ConfigChangeLog.objects.filter(action='integrity_error').count()
        result = resolve_artifact_policy(self.brand.slug)
        # Debe retornar algo (más reciente) y haber emitido log
        self.assertIsInstance(result, dict)
        self.assertEqual(
            ConfigChangeLog.objects.filter(action='integrity_error').count(),
            initial_count + 1,
        )
