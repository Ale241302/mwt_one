from .models import Brand, BrandArtifactRule

class BrandService:
    @staticmethod
    def get_artifact_flow(brand_slug, destination):
        # returns required artifact types for a brand and destination
        rules = BrandArtifactRule.objects.filter(
            brand_id=brand_slug,
            is_required=True,
            destination__in=[destination, 'ALL']
        )
        return list(rules.values_list('artifact_type', flat=True))
