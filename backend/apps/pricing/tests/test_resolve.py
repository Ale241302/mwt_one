import pytest
from decimal import Decimal
from django.utils import timezone
from apps.pricing.models import (
    PriceListVersion, PriceListGradeItem, ClientProductAssignment,
    EarlyPaymentPolicy, EarlyPaymentTier, PriceListItem, PriceList
)
from apps.pricing.services import resolve_client_price
from apps.productos.models import BrandSKU, ProductMaster
from apps.clientes.models import ClientSubsidiary, Client
from apps.brands.models import Brand

@pytest.mark.django_db
class TestPricingResolutionV2:
    @pytest.fixture
    def setup_data(self):
        # Basic setup: Brand, Product, SKU, Client
        self.brand = Brand.objects.create(name="Marluvas", min_margin_alert_pct=Decimal("15.00"))
        self.product = ProductMaster.objects.create(sku="10VS48-A", name="Botina Marluvas", brand=self.brand, base_price=Decimal("10.00"))
        self.sku = BrandSKU.objects.create(product=self.product, sku_code="10VS48-A-37", reference_code="10VS48-A-37", brand=self.brand)
        self.client = Client.objects.create(name="Cliente ABC")
        self.subsidiary = ClientSubsidiary.objects.create(client=self.client, name="Subsidiaria 1")

        # PriceList Version V1 (Active)
        self.v1 = PriceListVersion.objects.create(brand=self.brand, version_label="V1", is_active=True)
        self.item1 = PriceListGradeItem.objects.create(
            pricelist_version=self.v1, 
            brand_sku=self.sku,
            reference_code="10VS48-A",
            unit_price_usd=Decimal("8.00"),
            size_multipliers={"37": 5, "38": 5}
        )

    def test_waterfall_step2a_pricelist_grade(self, setup_data):
        """Test standard resolution from active PriceListGradeItem."""
        res = resolve_client_price(self.product, self.client, self.brand, brand_sku_id=self.sku.id, client_subsidiary_id=self.subsidiary.id)
        assert res['price'] == Decimal("8.00")
        assert res['source'] == 'pricelist_grade'
        assert res['grade_moq'] == 10
        assert res['pricelist_version'] == self.v1.id

    def test_waterfall_step1_bcpa_override(self, setup_data):
        """Test Step 1: BCPA override takes precedence over pricelist."""
        from apps.agreements.models import BrandClientPriceAgreement
        BrandClientPriceAgreement.objects.create(
            client_subsidiary=self.subsidiary,
            brand_sku=self.sku,
            agreed_price=Decimal("7.50"),
            is_active=True
        )
        res = resolve_client_price(self.product, self.client, self.brand, brand_sku_id=self.sku.id, client_subsidiary_id=self.subsidiary.id)
        assert res['price'] == Decimal("7.50")
        assert res['source'] == 'agreement'

    def test_waterfall_step0_cpa_cache(self, setup_data):
        """Test Step 0: CPA cached price takes highest precedence."""
        cpa = ClientProductAssignment.objects.create(
            client_subsidiary=self.subsidiary,
            brand_sku=self.sku,
            cached_client_price=Decimal("7.00"),
            cached_base_price=Decimal("7.00"),
            is_active=True
        )
        res = resolve_client_price(self.product, self.client, self.brand, brand_sku_id=self.sku.id, client_subsidiary_id=self.subsidiary.id)
        assert res['price'] == Decimal("7.00")
        assert res['source'] == 'assignment'

    def test_waterfall_step0_skip_cache(self, setup_data):
        """Test skip_cache=True ignores CPA (critical for Celery)."""
        ClientProductAssignment.objects.create(
            client_subsidiary=self.subsidiary,
            brand_sku=self.sku,
            cached_client_price=Decimal("7.00"),
            is_active=True
        )
        res = resolve_client_price(self.product, self.client, self.brand, brand_sku_id=self.sku.id, client_subsidiary_id=self.subsidiary.id, skip_cache=True)
        assert res['price'] == Decimal("8.00") # Returns to Step 2A
        assert res['source'] == 'pricelist_grade'

    def test_early_payment_discount(self, setup_data):
        """Test early payment policy application."""
        policy = EarlyPaymentPolicy.objects.create(client_subsidiary=self.subsidiary, brand=self.brand, is_active=True)
        EarlyPaymentTier.objects.create(policy=policy, payment_days=30, discount_pct=Decimal("2.00"))
        
        # Resolve with 30 days
        res = resolve_client_price(self.product, self.client, self.brand, brand_sku_id=self.sku.id, client_subsidiary_id=self.subsidiary.id, payment_days=30)
        # 8.00 - 2% = 7.84
        assert res['price'] == Decimal("7.8400")
        assert res['discount_applied'] == Decimal("2.00")
        assert res['base_price'] == Decimal("8.00")

    def test_moq_desacoplado(self, setup_data):
        """Test R4 rule: MCQ comes from Grade even if price is override."""
        from apps.agreements.models import BrandClientPriceAgreement
        BrandClientPriceAgreement.objects.create(
            client_subsidiary=self.subsidiary,
            brand_sku=self.sku,
            agreed_price=Decimal("6.00"),
            is_active=True
        )
        res = resolve_client_price(self.product, self.client, self.brand, brand_sku_id=self.sku.id, client_subsidiary_id=self.subsidiary.id)
        assert res['price'] == Decimal("6.00") # From Agreement
        assert res['source'] == 'agreement'
        assert res['grade_moq'] == 10 # From Grade (desacoplado)
        assert res['size_multipliers'] == {"37": 5, "38": 5}

    def test_legacy_fallback(self, setup_data):
        """Test Step 2B: Fallback to PriceListItem if no GradeItem exists."""
        # Deactivate Grade version
        self.v1.is_active = False
        self.v1.save()
        
        # Create Legacy S14 data
        pl = PriceList.objects.create(brand=self.brand, valid_from=timezone.now().date())
        PriceListItem.objects.create(price_list=pl, sku=self.product.sku, price=Decimal("9.50"))
        
        res = resolve_client_price(self.product, self.client, self.brand, brand_sku_id=self.sku.id, client_subsidiary_id=self.subsidiary.id)
        assert res['price'] == Decimal("9.50")
        assert res['source'] == 'pricelist_legacy'

    def test_min_price_multi_version(self, setup_data):
        """Test MIN(price) rule when multiple versions are active."""
        v2 = PriceListVersion.objects.create(brand=self.brand, version_label="V2", is_active=True)
        PriceListGradeItem.objects.create(
            pricelist_version=v2, 
            brand_sku=self.sku,
            reference_code="10VS48-A",
            unit_price_usd=Decimal("7.90"), # Cheaper than v1 (8.00)
            size_multipliers={"37": 10}
        )
        
        res = resolve_client_price(self.product, self.client, self.brand, brand_sku_id=self.sku.id, client_subsidiary_id=self.subsidiary.id)
        assert res['price'] == Decimal("7.90")
        assert res['pricelist_version'] == v2.id

    def test_validate_moq_success(self, setup_data):
        """Test validate_moq service with valid quantities."""
        from apps.pricing.services import validate_moq
        # Total 10 (valid for grade_moq 10), and >= multipliers
        q = {"37": 5, "38": 5}
        val = validate_moq(self.sku.id, self.subsidiary.id, q)
        assert val['valid'] is True
        assert len(val['errors']) == 0
        assert len(val['warnings']) == 0

    def test_validate_moq_error_total(self, setup_data):
        """Test validate_moq returns error if total < grade_moq."""
        from apps.pricing.services import validate_moq
        q = {"37": 5, "38": 2} # Total 7 < 10
        val = validate_moq(self.sku.id, self.subsidiary.id, q)
        assert val['valid'] is False
        assert len(val['errors']) == 1
        assert "menor al MOQ" in val['errors'][0]['message']

    def test_validate_moq_warning_size(self, setup_data):
        """Test validate_moq returns warning if size_qty < multiplier."""
        from apps.pricing.services import validate_moq
        # Total 12 >= 10 (Error OK), but talla 38 has 2 < 5 (Warning)
        q = {"37": 10, "38": 2}
        val = validate_moq(self.sku.id, self.subsidiary.id, q)
        assert val['valid'] is True # Warning doesn't invalidate
        assert len(val['warnings']) == 1
        assert val['warnings'][0]['size'] == "38"

    def test_portal_security_filter(self, setup_data):
        """Verify that portal serializer (simulated) doesn't leak internal data."""
        # This is more of a service test for the dict structure expected by portal
        res = resolve_client_price(self.product, self.client, self.brand, brand_sku_id=self.sku.id, client_subsidiary_id=self.subsidiary.id)
        # Internal response has everything
        assert 'source' in res
        assert 'base_price' in res
        # Serializer test should follow in a separate DRF test file