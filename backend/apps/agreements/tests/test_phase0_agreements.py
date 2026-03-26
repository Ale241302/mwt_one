from django.test import TestCase
from django.utils import timezone
from django.db import IntegrityError
from datetime import timedelta
from apps.brands.models import Brand
from apps.agreements.models import (
    BrandClientAgreement,
    BrandClientPriceAgreement,
    AssortmentPolicy,
    CreditPolicy,
    BrandWorkflowPolicy,
    PaymentTermPricingVersion
)

# Use dummy constraint checks depending on DB engine; sqlite might not support ExclusionConstraints,
# but we write the test assuming Postgres or skip them if unhandled.
# To ensure tests pass correctly in standard Django test environment without psycopg2 specific imports
# we will construct a valid naive or timezone aware date if possible.
from psycopg2.extras import DateTimeTZRange

class Phase0AgreementsTests(TestCase):
    def setUp(self):
        self.brand = Brand.objects.create(name="Test Brand", slug="test-brand", code="TB")
        self.now = timezone.now()
        self.range1 = DateTimeTZRange(self.now, self.now + timedelta(days=30))
        self.range2 = DateTimeTZRange(self.now + timedelta(days=15), self.now + timedelta(days=45))

    def test_1_create_brand_client_agreement(self):
        """Test #1: Create basic BrandClientAgreement."""
        agg = BrandClientAgreement.objects.create(
            brand=self.brand,
            party_type='subsidiary',
            party_id=1,
            version="1.0",
            status="active"
        )
        self.assertEqual(agg.party_id, 1)

    def test_2_overlap_brand_client_agreement(self):
        """Test #2: Overlapping active BrandClientAgreements should raise IntegrityError."""
        BrandClientAgreement.objects.create(
            brand=self.brand,
            party_type='subsidiary',
            party_id=1,
            version="1.0",
            valid_daterange=self.range1,
            status="active"
        )
        with self.assertRaises(IntegrityError):
            BrandClientAgreement.objects.create(
                brand=self.brand,
                party_type='subsidiary',
                party_id=1,
                version="2.0",
                valid_daterange=self.range2,
                status="active"
            )

    def test_3_create_price_agreement(self):
        """Test #3: Create BrandClientPriceAgreement."""
        pa = BrandClientPriceAgreement.objects.create(
            brand=self.brand,
            party_type='subsidiary',
            party_id=1,
            sku='SKU123',
            mode='FOB',
            currency='USD',
            override_price=10.50,
            status='active'
        )
        self.assertEqual(pa.override_price, 10.50)

    def test_4_overlap_price_agreement(self):
        """Test #4: Overlapping active ClientPriceAgreements raise IntegrityError."""
        BrandClientPriceAgreement.objects.create(
            brand=self.brand,
            party_type='subsidiary',
            party_id=1,
            sku='SKU123',
            mode='FOB',
            currency='USD',
            override_price=10.50,
            valid_daterange=self.range1,
            status='active'
        )
        with self.assertRaises(IntegrityError):
            BrandClientPriceAgreement.objects.create(
                brand=self.brand,
                party_type='subsidiary',
                party_id=1,
                sku='SKU123',
                mode='FOB',
                currency='USD',
                override_price=12.00,
                valid_daterange=self.range2,
                status='active'
            )

    def test_5_create_assortment_policy(self):
        """Test #5: Default AssortmentPolicy has empty rules."""
        ap = AssortmentPolicy.objects.create(
            brand=self.brand,
            party_type='subsidiary',
            party_id=1,
            channel='b2b',
            status='active'
        )
        self.assertEqual(ap.include_rules, [])

    def test_6_create_credit_policy(self):
        """Test #6: Create CreditPolicy."""
        cp = CreditPolicy.objects.create(
            scope_type='global',
            subject_type='client',
            subject_id=1,
            brand=self.brand,
            currency='USD',
            max_amount=10000.00,
            status='active'
        )
        self.assertEqual(cp.max_amount, 10000.00)

    def test_7_create_payment_term_version(self):
        """Test #7: Payment term pricing version."""
        pt = PaymentTermPricingVersion.objects.create(
            brand=self.brand,
            scope_type='brand_default',
            version='v1',
            status='active'
        )
        self.assertEqual(pt.version, 'v1')

    def test_8_create_workflow_policy(self):
        """Test #8: Workflow policy creation."""
        wp = BrandWorkflowPolicy.objects.create(
            brand=self.brand,
            status='active'
        )
        self.assertIsNotNone(wp.id)
