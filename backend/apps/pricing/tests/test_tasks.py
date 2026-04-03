import pytest
from decimal import Decimal
from apps.pricing.models import (
    PriceListVersion, PriceListGradeItem, ClientProductAssignment
)
from apps.pricing.tasks import recalculate_assignments_for_brand
from apps.productos.models import BrandSKU, ProductMaster
from apps.clientes.models import ClientSubsidiary, Client
from apps.brands.models import Brand

@pytest.mark.django_db
class TestPricingTasks:
    @pytest.fixture
    def setup_data(self):
        self.brand = Brand.objects.create(name="Marluvas")
        self.product = ProductMaster.objects.create(sku="PROD-1", name="Product 1", brand=self.brand)
        self.sku = BrandSKU.objects.create(product=self.product, sku_code="SKU-1", brand=self.brand)
        self.client = Client.objects.create(name="Client A")
        self.subsidiary = ClientSubsidiary.objects.create(client=self.client, name="Subs 1")
        
        # Initial Assignment with old price (cached)
        self.cpa = ClientProductAssignment.objects.create(
            client_subsidiary=self.subsidiary,
            brand_sku=self.sku,
            cached_client_price=Decimal("10.00"),
            is_active=True
        )

    def test_recalculate_task_updates_cpa(self, setup_data):
        """Test recalculate_assignments_for_brand task updates CPA prices."""
        # Create new active pricelist with cheaper price
        v = PriceListVersion.objects.create(brand=self.brand, is_active=True, version_label="V_NEW")
        PriceListGradeItem.objects.create(
            pricelist_version=v,
            brand_sku=self.sku,
            reference_code="REF-1",
            unit_price_usd=Decimal("8.50")
        )
        
        # Run task synchronously for testing
        recalculate_assignments_for_brand(self.brand.id)
        
        self.cpa.refresh_from_db()
        assert self.cpa.cached_client_price == Decimal("8.50")
        assert self.cpa.cached_pricelist_version == v

    def test_recalculate_task_skip_cache_integrity(self, setup_data):
        """Verify task actually clears cache (skip_cache=True) by checking price change."""
        # Initial Price 10.00 cached.
        # Now add a pricelist version with 12.00
        v = PriceListVersion.objects.create(brand=self.brand, is_active=True, version_label="V_HI")
        PriceListGradeItem.objects.create(
            pricelist_version=v,
            brand_sku=self.sku,
            reference_code="REF-1",
            unit_price_usd=Decimal("12.00")
        )
        
        # Task should update 10.00 -> 12.00
        recalculate_assignments_for_brand(self.brand.id)
        
        self.cpa.refresh_from_db()
        assert self.cpa.cached_client_price == Decimal("12.00")