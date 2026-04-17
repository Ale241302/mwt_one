from rest_framework import viewsets, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import action
from apps.core.registry import ModuleRegistry
from apps.users.models import UserRole
from .serializers import ExpedientePortalSerializer, ArtifactPortalSerializer

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
            
        expediente_model = ModuleRegistry.get_model('expedientes', 'Expediente')
        if not expediente_model:
            return [] # O manejar error
            
        if user.role == UserRole.CEO or user.role == UserRole.INTERNAL:
            return expediente_model.objects.all()
            
        if brand_slug:
            return expediente_model.objects.filter(brand_id=brand_slug)
            
        return expediente_model.objects.none()

    @action(detail=True, methods=['get'])
    def artifacts(self, request, pk=None):
        expediente = self.get_object()
        artifact_model = ModuleRegistry.get_model('expedientes', 'ArtifactInstance')
        if not artifact_model:
            return Response({"error": "Artifacts module unavailable"}, status=503)
            
        artifacts = artifact_model.objects.filter(expediente_id=expediente.expediente_id)
        serializer = ArtifactPortalSerializer(artifacts, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def pagos(self, request, pk=None):
        """
        S25-13 FIX: GET /api/portal/expedientes/{id}/pagos/
        Retorna pagos con campos restringidos para el portal del cliente.
        """
        expediente = self.get_object()
        payment_model = ModuleRegistry.get_model('finance', 'Payment')
        if not payment_model:
            return Response({"error": "Finance module unavailable"}, status=503)

        pagos = payment_model.objects.filter(expediente_id=expediente.expediente_id).order_by('-payment_date')
        
        data = [{
            "id": str(p.id),
            "amount_paid": p.amount_paid,
            "payment_date": p.payment_date,
            "status": p.status,
            "metodo_pago": p.metodo_pago
        } for p in pagos]
        
        return Response(data)

class CatalogView(APIView):
    """S14-14: GET /api/portal/catalog/"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        from apps.productos.models import Product
        from apps.pricing.services import resolve_client_price
        from django.utils import timezone
        
        user = request.user
        brand_slug = None
        if user.role == UserRole.CLIENT_MARLUVAS:
            brand_slug = 'marluvas'
        elif user.role == UserRole.CLIENT_TECMATER:
            brand_slug = 'tecmater'
            
        if not brand_slug:
            return Response({"error": "No brand associated with client"}, status=403)
            
        products = Product.objects.filter(brand_id=brand_slug)
        context = {
            'brand': brand_slug,
            'date': timezone.now().date(),
            'currency': 'USD',
        }
        
        catalog = []
        for product in products:
            price_data = resolve_client_price(
                brand_id=brand_slug,
                party_type='subsidiary', 
                party_id=user.id,
                sku=product.sku_base,
                mode='FOB',
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
