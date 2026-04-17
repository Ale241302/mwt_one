from apps.productos.models import Product, ProductVariant

class ProductService:
    """Servicio para gestión de productos y resolución de entidades."""

    @staticmethod
    def get_entity(product_id):
        """Resuelve un UUID de producto a su instancia."""
        try:
            return Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return None

    @staticmethod
    def get_variant(variant_sku):
        """Busca una variante por su SKU."""
        try:
            return ProductVariant.objects.get(variant_sku=variant_sku)
        except ProductVariant.DoesNotExist:
            return None

    @staticmethod
    def resolve_variant_to_product(variant_sku):
        """Devuelve el producto padre de una variante."""
        variant = ProductService.get_variant(variant_sku)
        return variant.product if variant else None
