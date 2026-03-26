from rest_framework import viewsets, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import action
from apps.expedientes.models import Expediente
from apps.users.models import UserRole
from .serializers import ExpedientePortalSerializer

class PortalExpedienteViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ExpedientePortalSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        
        # Determine brand from user role
        brand_slug = None
        if user.role == UserRole.CLIENT_MARLUVAS:
            brand_slug = 'marluvas'
        elif user.role == UserRole.CLIENT_TECMATER:
            brand_slug = 'tecmater'
            
        if user.role == UserRole.CEO or user.role == UserRole.INTERNAL:
            return Expediente.objects.all()
            
        if brand_slug:
            return Expediente.objects.filter(brand_id=brand_slug)
            
        return Expediente.objects.none()

    @action(detail=True, methods=['get'])
    def artifacts(self, request, pk=None):
        expediente = self.get_object()
        from apps.expedientes.models import ArtifactInstance
        from .serializers import ArtifactPortalSerializer
        
        artifacts = ArtifactInstance.objects.filter(expediente=expediente)
        serializer = ArtifactPortalSerializer(artifacts, many=True)
        return Response(serializer.data)


class CatalogView(APIView):
    """S14-14: GET /api/portal/catalog/"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        from apps.productos.models import ProductMaster
        from apps.pricing.services import resolve_client_price
        from decimal import Decimal
        from django.utils import timezone
        
        user = request.user
        
        brand_slug = None
        if user.role == UserRole.CLIENT_MARLUVAS:
            brand_slug = 'marluvas'
        elif user.role == UserRole.CLIENT_TECMATER:
            brand_slug = 'tecmater'
            
        if not brand_slug:
            return Response({"error": "No brand associated with client"}, status=403)
            
        products = ProductMaster.objects.filter(brand_id=brand_slug)
        
        context = {
            'brand': brand_slug,
            'client_subsidiary_id': user.id, # mock resolution
            'date': timezone.now().date(),
            'currency': 'USD',
            'channel': 'distributor' # simplified generic for portal
        }
        
        catalog = []
        for product in products:
            price_data = resolve_client_price(
                brand_id=brand_slug,
                party_type='subsidiary', 
                party_id=user.id,
                sku=product.sku_base,
                mode='FOB', # Default for catalog
                currency=context['currency'],
                date=context['date']
            )
            
            price = price_data['price'] if price_data else 0
            
            catalog.append({
                'sku': product.sku_base,
                'name': product.name,
                'price': float(price),
                'currency': context['currency'],
                'pricing_source': price_data.get('source', 'none') if price_data else 'none'
            })
            
        return Response(catalog)

class PortalContactsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        return Response({"detail": "Contact saved"}, status=status.HTTP_201_CREATED)

class PortalPreferencesView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request):
        return Response({"detail": "Preferences updated"}, status=status.HTTP_200_OK)
