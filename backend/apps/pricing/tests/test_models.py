import pytest
from decimal import Decimal
from django.db import IntegrityError
from apps.pricing.models import (
    PriceListVersion, PriceListGradeItem, ClientProductAssignment,
    EarlyPaymentPolicy, EarlyPaymentTier
)
from apps.productos.models import BrandSKU, ProductMaster
from apps.clientes.models import ClientSubsidiary, Client
from apps.brands.models import Brand

@pytest.mark.django_db
class TestPricingModels:
    @pytest.fixture
    def setup_data(self):
        self.brand = Brand.objects.create(name="Marluvas")
        self.product = ProductMaster.objects.create(sku="MOD-1", name="Product 1", brand=self.brand)
        self.sku1 = BrandSKU.objects.create(product=self.product, sku_code="SKU-1", brand=self.brand)
        self.sku2 = BrandSKU.objects.create(product=self.product, sku_code="SKU-2", brand=self.brand)
        self.client = Client.objects.create(name="Client A")
        self.subsidiary = ClientSubsidiary.objects.create(client=self.client, name="Subs 1")

    def test_cpa_unique_constraint(self, setup_data):
        """Test unique(client_subsidiary, brand_sku) in CPA."""
        ClientProductAssignment.objects.create(
            client_subsidiary=self.subsidiary,
            brand_sku=self.sku1,
            is_active=True
        )
        with pytest.raises(IntegrityError):
            ClientProductAssignment.objects.create(
                client_subsidiary=self.subsidiary,
                brand_sku=self.sku1,
                is_active=True
            )

    def test_grade_item_moq_total_property(self, setup_data):
        """Test PriceListGradeItem.moq_total calculation."""
        v = PriceListVersion.objects.create(brand=self.brand, version_label="V1")
        item = PriceListGradeItem(
            pricelist_version=v,
            reference_code="REF-1",
            unit_price_usd=Decimal("10.00"),
            size_multipliers={"37": 5, "38": 10, "39": 5}
        )
        assert item.moq_total == 20
        assert item.available_sizes == ["37", "38", "39"]

    def test_early_payment_policy_unique(self, setup_data):
        """Test unique(client_subsidiary, brand) in EarlyPaymentPolicy."""
        EarlyPaymentPolicy.objects.create(client_subsidiary=self.subsidiary, brand=self.brand)
        with pytest.raises(IntegrityError):
            EarlyPaymentPolicy.objects.create(client_subsidiary=self.subsidiary, brand=self.brand)

    def test_early_payment_tier_unique(self, setup_data):
        """Test unique(policy, payment_days) in EarlyPaymentTier."""
        policy = EarlyPaymentPolicy.objects.create(client_subsidiary=self.subsidiary, brand=self.brand)
        EarlyPaymentTier.objects.create(policy=policy, payment_days=30, discount_pct=Decimal("1.50"))
        with pytest.raises(IntegrityError):
            EarlyPaymentTier.objects.create(policy=policy, payment_days=30, discount_pct=Decimal("2.00"))