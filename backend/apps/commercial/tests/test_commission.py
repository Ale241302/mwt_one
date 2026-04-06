from decimal import Decimal
from datetime import date
from django.test import TestCase
from django.db import IntegrityError
from apps.commercial.models import CommissionRule
from apps.commercial.services.commissions import resolve_commission_rule, resolve_commission
from apps.brands.models import Brand
from apps.clients.models import Client, Subsidiary


class TestCommissionT8(TestCase):
    """T8: resolve_commission_rule() — cascada de scope"""

    def setUp(self):
        self.brand = Brand.objects.create(name="BrandComm")
        self.client = Client.objects.create(name="ClientComm", brand=self.brand)
        self.subsidiary = Subsidiary.objects.create(name="SubComm", client=self.client)
        self.product_key = "SKU-001"

    def _make_rule(self, **kwargs):
        base = dict(
            brand=self.brand,
            commission_type="percentage",
            commission_value=Decimal("3.00"),
            is_active=True,
        )
        base.update(kwargs)
        return CommissionRule.objects.create(**base)

    def test_subsidiary_product_beats_all(self):
        self._make_rule(brand=self.brand)  # brand default
        self._make_rule(client=self.client)  # client default
        rule = self._make_rule(subsidiary=self.subsidiary, product_key=self.product_key)
        result = resolve_commission_rule(
            brand=self.brand, client=self.client,
            subsidiary=self.subsidiary, product_key=self.product_key
        )
        self.assertEqual(result, rule)

    def test_falls_back_to_brand_default(self):
        rule = self._make_rule(brand=self.brand)
        result = resolve_commission_rule(
            brand=self.brand, client=self.client,
            subsidiary=self.subsidiary, product_key=self.product_key
        )
        self.assertEqual(result, rule)

    def test_returns_none_if_no_rule(self):
        result = resolve_commission_rule(
            brand=self.brand, client=self.client,
            subsidiary=self.subsidiary, product_key=self.product_key
        )
        self.assertIsNone(result)


class TestCommissionT9(TestCase):
    """T9: resolve_commission()"""

    def setUp(self):
        self.brand = Brand.objects.create(name="BrandComm2")

    def _make_rule(self, **kwargs):
        base = dict(
            brand=self.brand,
            commission_type="percentage",
            commission_value=Decimal("5.00"),
            commission_base="sale_price",
            is_active=True,
        )
        base.update(kwargs)
        return CommissionRule.objects.create(**base)

    def test_sale_price_base(self):
        rule = self._make_rule(commission_base="sale_price")
        result = resolve_commission(rule=rule, sale_price=Decimal("1000.00"))
        self.assertEqual(result, Decimal("50.00"))

    def test_gross_margin_base(self):
        rule = self._make_rule(commission_base="gross_margin")
        result = resolve_commission(
            rule=rule,
            sale_price=Decimal("1000.00"),
            cost_price=Decimal("700.00"),
        )
        self.assertEqual(result, Decimal("15.00"))  # 5% of 300

    def test_fixed_amount_rule(self):
        rule = self._make_rule(commission_type="fixed_amount", commission_value=Decimal("25.00"))
        result = resolve_commission(rule=rule, sale_price=Decimal("1000.00"))
        self.assertEqual(result, Decimal("25.00"))

    def test_commission_base_none_on_percentage_raises(self):
        rule = self._make_rule(commission_base=None)
        with self.assertRaises(ValueError) as ctx:
            resolve_commission(rule=rule, sale_price=Decimal("1000.00"))
        self.assertIn("DEC-S23-03", str(ctx.exception))

    def test_gross_margin_without_cost_price_raises(self):
        rule = self._make_rule(commission_base="gross_margin")
        with self.assertRaises(ValueError):
            resolve_commission(rule=rule, sale_price=Decimal("1000.00"))


class TestCommissionT10(TestCase):
    """T10: UniqueConstraints en CommissionRule"""

    def setUp(self):
        self.brand = Brand.objects.create(name="BrandComm3")

    def test_duplicate_active_brand_default_raises(self):
        CommissionRule.objects.create(
            brand=self.brand,
            commission_type="percentage",
            commission_value=Decimal("3.00"),
            is_active=True,
        )
        with self.assertRaises(IntegrityError):
            CommissionRule.objects.create(
                brand=self.brand,
                commission_type="percentage",
                commission_value=Decimal("4.00"),
                is_active=True,
            )

    def test_inactive_duplicate_does_not_raise(self):
        CommissionRule.objects.create(
            brand=self.brand,
            commission_type="percentage",
            commission_value=Decimal("3.00"),
            is_active=False,
        )
        # second inactive — should not raise
        rule2 = CommissionRule.objects.create(
            brand=self.brand,
            commission_type="percentage",
            commission_value=Decimal("4.00"),
            is_active=False,
        )
        self.assertIsNotNone(rule2.pk)
