from apps.productos.models import Product

class ProductService:
    """Servicio para resolución de productos unificados (Master/Variant fusionados)."""

    @staticmethod
    def get_entity(product_id):
        """Resuelve un UUID de producto a su instancia."""
        try:
            return Product.objects.get(id=product_id)
        except (Product.DoesNotExist, ValueError):
            return None

    @staticmethod
    def get_variant(variant_sku):
        """
        Busca una variante por su SKU dentro del JSON de productos.
        Retorna una tupla (Product, variant_dict) o (None, None).
        """
        # Búsqueda optimizada por JSON (PostgreSQL JSONB)
        product = Product.objects.filter(variants_json__contains=[{'sku': variant_sku}]).first()
        if product:
            for v in product.variants_json:
                if v.get('sku') == variant_sku:
                    return product, v
        return None, None

    @staticmethod
    def resolve_variant_to_product(variant_sku):
        """Devuelve el producto padre de una variante."""
        product, _ = ProductService.get_variant(variant_sku)
        return product
