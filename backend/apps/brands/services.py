from apps.core.services import ModuleService
from .models import Brand

class BrandService(ModuleService):
    @classmethod
    def get_entity(cls, entity_id):
        """
        Obtiene una marca por ID o por Slug.
        En este sistema, Brand usa Slug como PK.
        """
        try:
            return Brand.objects.get(slug=entity_id, is_active=True)
        except Brand.DoesNotExist:
            try:
                # Intento por ID si viene en formato UUID
                return Brand.objects.get(id=entity_id, is_active=True)
            except (Brand.DoesNotExist, ValueError):
                return None

    @classmethod
    def get_brand_name(cls, brand_id):
        brand = cls.get_entity(brand_id)
        return brand.name if brand else "Marca Desconocida"
