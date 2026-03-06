from django.test import TestCase
from apps.brands.models import Brand, BrandArtifactRule, BrandSKU
from apps.brands.services import BrandService
from apps.expedientes.enums import ArchProfile, DestinationChoices, BrandType

class BrandsAppTests(TestCase):
    def setUp(self):
        self.brand = Brand.objects.create(
            name="Rana Walk",
            slug="rana_walk",
            brand_type=BrandType.RANA_WALK
        )
        self.rule = BrandArtifactRule.objects.create(
            brand=self.brand,
            artifact_type="ART-19",
            is_required=True,
            flow_stage="LOGISTICS"
        )
        self.sku = BrandSKU.objects.create(
            brand=self.brand,
            product_name="Goliath",
            sku_code="RW-GOL-BLK",
            size="42",
            arch_profile=ArchProfile.MEDIUM
        )

    def test_brand_str(self):
        self.assertEqual(str(self.brand), "Rana Walk (rana_walk)")
    
    def test_brand_service_get_flow(self):
        flow = BrandService.get_artifact_flow(self.brand.id)
        self.assertEqual(len(flow), 1)
        self.assertEqual(flow[0].artifact_type, "ART-19")
