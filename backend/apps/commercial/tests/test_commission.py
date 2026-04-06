"""
T8  — resolve_commission_rule(): cascada de scopes
T9  — resolve_commission(): cálculo, ValueError, gross_margin
T10 — CommissionRule UniqueConstraints
"""
from decimal import Decimal
from datetime import date
from django.db import IntegrityError
from django.test import TestCase

from apps.commercial.models import CommissionRule, CommissionRuleType, CommissionBase
from apps.commercial.services.commissions import resolve_commission_rule, resolve_commission


def make_brand(slug='brand-comm'):
    from apps.brands.models import Brand
    return Brand.objects.get_or_create(slug=slug, defaults={'name': f'Brand {slug}'})[0]


def make_client():
    from apps.clientes.models import Cliente
    return Cliente.objects.get_or_create(
        nombre='Cliente Comm', defaults={'email': 'comm@test.com'}
    )[0]


def make_subsidiary(client):
    from apps.clientes.models import ClientSubsidiary
    return ClientSubsidiary.objects.get_or_create(
        client=client, name='Sub Comm', defaults={}
    )[0]


def make_rule(brand=None, client=None, subsidiary=None, product_key=None,
              rule_type=CommissionRuleType.PERCENTAGE, rule_value=Decimal('3.0000'),
              commission_base=CommissionBase.SALE_PRICE, is_active=True):
    return CommissionRule.objects.create(
        brand=brand,
        client=client,
        subsidiary=subsidiary,
        product_key=product_key,
        rule_type=rule_type,
        rule_value=rule_value,
        commission_base=commission_base,
        is_active=is_active,
    )


class T8ResolveCommissionRuleTest(TestCase):
    """T8 — Cascada: subsidiary+product > subsidiary default > client+product > client default > brand+product > brand default > None."""

    def setUp(self):
        self.brand = make_brand()
        self.client = make_client()
        self.subsidiary = make_subsidiary(self.client)

    def test_returns_none_when_no_rules(self):
        result = resolve_commission_rule(brand_slug=self.brand.slug)
        self.assertIsNone(result)

    def test_brand_default(self):
        make_rule(brand=self.brand, rule_value=Decimal('1.0000'))
        result = resolve_commission_rule(brand_slug=self.brand.slug)
        self.assertEqual(result.scope_level, 'brand')
        self.assertEqual(result.rule_value, Decimal('1.0000'))

    def test_brand_product_over_brand_default(self):
        make_rule(brand=self.brand, rule_value=Decimal('1.0000'))  # default
        make_rule(brand=self.brand, product_key='SKU-A', rule_value=Decimal('2.0000'))  # product
        result = resolve_commission_rule(brand_slug=self.brand.slug, product_key='SKU-A')
        self.assertEqual(result.rule_value, Decimal('2.0000'))
        self.assertEqual(result.product_key, 'SKU-A')

    def test_client_default_over_brand(self):
        make_rule(brand=self.brand, rule_value=Decimal('1.0000'))
        make_rule(client=self.client, rule_value=Decimal('4.0000'))
        result = resolve_commission_rule(
            brand_slug=self.brand.slug, client_id=self.client.pk
        )
        self.assertEqual(result.scope_level, 'client')
        self.assertEqual(result.rule_value, Decimal('4.0000'))

    def test_subsidiary_default_over_client(self):
        make_rule(client=self.client, rule_value=Decimal('4.0000'))
        make_rule(subsidiary=self.subsidiary, rule_value=Decimal('6.0000'))
        result = resolve_commission_rule(
            brand_slug=self.brand.slug,
            client_id=self.client.pk,
            subsidiary_id=self.subsidiary.pk,
        )
        self.assertEqual(result.scope_level, 'subsidiary')
        self.assertEqual(result.rule_value, Decimal('6.0000'))

    def test_subsidiary_product_over_subsidiary_default(self):
        make_rule(subsidiary=self.subsidiary, rule_value=Decimal('6.0000'))  # default
        make_rule(subsidiary=self.subsidiary, product_key='SKU-B', rule_value=Decimal('8.0000'))  # product
        result = resolve_commission_rule(
            brand_slug=self.brand.slug,
            subsidiary_id=self.subsidiary.pk,
            product_key='SKU-B',
        )
        self.assertEqual(result.rule_value, Decimal('8.0000'))
        self.assertEqual(result.scope_level, 'subsidiary')

    def test_inactive_rule_not_resolved(self):
        make_rule(brand=self.brand, rule_value=Decimal('1.0000'), is_active=False)
        result = resolve_commission_rule(brand_slug=self.brand.slug)
        self.assertIsNone(result)


class T9ResolveCommissionTest(TestCase):
    """T9 — resolve_commission(): cálculos y ValueError."""

    def setUp(self):
        self.brand = make_brand(slug='brand-t9')
        self.client = make_client()

    def test_sale_price_base_percentage(self):
        make_rule(brand=self.brand, commission_base=CommissionBase.SALE_PRICE,
                  rule_value=Decimal('5.0000'))
        result = resolve_commission(
            brand_slug=self.brand.slug,
            sale_price=Decimal('1000.00'),
        )
        self.assertIsNotNone(result)
        self.assertEqual(result.commission_amount, Decimal('50.0000'))
        self.assertEqual(result.base_amount, Decimal('1000.00'))
        self.assertEqual(result.commission_base, 'sale_price')

    def test_gross_margin_base(self):
        make_rule(brand=self.brand, commission_base=CommissionBase.GROSS_MARGIN,
                  rule_value=Decimal('10.0000'))
        result = resolve_commission(
            brand_slug=self.brand.slug,
            sale_price=Decimal('1000.00'),
            cost_price=Decimal('700.00'),
        )
        # base = 1000 - 700 = 300; commission = 300 * 10% = 30.0000
        self.assertEqual(result.base_amount, Decimal('300.00'))
        self.assertEqual(result.commission_amount, Decimal('30.0000'))

    def test_gross_margin_base_no_cost_price_raises(self):
        make_rule(brand=self.brand, commission_base=CommissionBase.GROSS_MARGIN,
                  rule_value=Decimal('10.0000'))
        with self.assertRaises(ValueError) as ctx:
            resolve_commission(
                brand_slug=self.brand.slug,
                sale_price=Decimal('1000.00'),
                # cost_price no proporcionado
            )
        self.assertIn('cost_price', str(ctx.exception))

    def test_commission_base_none_percentage_raises(self):
        make_rule(brand=self.brand, commission_base=None, rule_value=Decimal('5.0000'))
        with self.assertRaises(ValueError) as ctx:
            resolve_commission(
                brand_slug=self.brand.slug,
                sale_price=Decimal('1000.00'),
            )
        self.assertIn('DEC-S23-03', str(ctx.exception))

    def test_fixed_amount_rule(self):
        make_rule(brand=self.brand,
                  rule_type=CommissionRuleType.FIXED_AMOUNT,
                  rule_value=Decimal('50.0000'),
                  commission_base=None)
        result = resolve_commission(
            brand_slug=self.brand.slug,
            sale_price=Decimal('1000.00'),
        )
        self.assertEqual(result.commission_amount, Decimal('50.0000'))

    def test_returns_none_when_no_rule(self):
        result = resolve_commission(
            brand_slug=self.brand.slug,
            sale_price=Decimal('1000.00'),
        )
        self.assertIsNone(result)

    def test_gross_margin_negative_clipped_to_zero(self):
        make_rule(brand=self.brand, commission_base=CommissionBase.GROSS_MARGIN,
                  rule_value=Decimal('10.0000'))
        result = resolve_commission(
            brand_slug=self.brand.slug,
            sale_price=Decimal('500.00'),
            cost_price=Decimal('700.00'),  # costo > precio → margen negativo → 0
        )
        self.assertEqual(result.base_amount, Decimal('0'))
        self.assertEqual(result.commission_amount, Decimal('0.0000'))


class T10CommissionRuleConstraintsTest(TestCase):
    """T10 — UniqueConstraints de CommissionRule."""

    def setUp(self):
        self.brand = make_brand(slug='brand-t10')
        self.client = make_client()
        self.subsidiary = make_subsidiary(self.client)

    def test_T10_duplicate_active_brand_default_raises(self):
        make_rule(brand=self.brand, is_active=True)
        with self.assertRaises(IntegrityError):
            make_rule(brand=self.brand, is_active=True)

    def test_T10_inactive_brand_default_duplicate_allowed(self):
        make_rule(brand=self.brand, is_active=False)
        r2 = make_rule(brand=self.brand, is_active=False)
        self.assertIsNotNone(r2.pk)

    def test_T10_duplicate_active_brand_product_raises(self):
        make_rule(brand=self.brand, product_key='SKU-X', is_active=True)
        with self.assertRaises(IntegrityError):
            make_rule(brand=self.brand, product_key='SKU-X', is_active=True)

    def test_T10_duplicate_active_client_default_raises(self):
        make_rule(client=self.client, is_active=True)
        with self.assertRaises(IntegrityError):
            make_rule(client=self.client, is_active=True)

    def test_T10_duplicate_active_subsidiary_default_raises(self):
        make_rule(subsidiary=self.subsidiary, is_active=True)
        with self.assertRaises(IntegrityError):
            make_rule(subsidiary=self.subsidiary, is_active=True)

    def test_T10_one_level_only_two_scopes_raises(self):
        with self.assertRaises(IntegrityError):
            CommissionRule.objects.create(
                brand=self.brand,
                client=self.client,
                rule_type=CommissionRuleType.PERCENTAGE,
                rule_value=Decimal('3.0000'),
                commission_base=CommissionBase.SALE_PRICE,
            )

    def test_T10_one_level_only_no_scope_raises(self):
        with self.assertRaises(IntegrityError):
            CommissionRule.objects.create(
                rule_type=CommissionRuleType.PERCENTAGE,
                rule_value=Decimal('3.0000'),
                commission_base=CommissionBase.SALE_PRICE,
            )
