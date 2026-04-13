from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from apps.users.models import UserRole
from apps.productos.models import ProductMaster
from apps.pricing.services import resolve_client_price
from django.utils import timezone

class VendorCatalogView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        
        # Vendor or CEO can see catalog. CEO sees all, Vendor only sees base prices.
        if user.role not in [UserRole.INTERNAL, UserRole.CEO]:
            return Response({"error": "Unauthorized"}, status=403)
            
        brand_slug = request.query_params.get('brand')
        if not brand_slug:
            return Response({"error": "Brand ID required"}, status=400)
            
        products = ProductMaster.objects.filter(brand_id=brand_slug)
        
        catalog = []
        for product in products:
            # We mock resolution. In reality, pass the appropriate mode and rules.
            price_data = resolve_client_price(
                brand_id=brand_slug,
                party_type='subsidiary', 
                party_id=user.id,
                sku=product.sku_base,
                mode='FOB', 
                currency='USD',
                date=timezone.now().date()
            )
            
            # S31 constraint: Show 'precio_lista' but never raw CEO margins or specific client costs
            pricing_to_show = price_data['price'] if price_data else 0
            
            catalog.append({
                'sku': product.sku_base,
                'name': product.name,
                'price_lista': float(pricing_to_show), # CEO-only prices not exposed
                'currency': 'USD',
                'stock_available': 'N/A' # Hook up to Inventory API later if connected
            })
            
        return Response(catalog)
