# Sprint 22 - S22-08: Views para Bulk Assignment y resolve de precio
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated


class BulkAssignmentView(APIView):
    """
    S22-08: POST /api/pricing/client-assignments/bulk/
    Crea N ClientProductAssignment de golpe dado un product_key.
    Idempotente: si un CPA ya existe para un SKU, lo saltea sin error.

    Body: { product_key: str, client_subsidiary_ids: [int, ...] }
    Response: { created: N, skipped: N, errors: [...] }
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        from apps.pricing.serializers import BulkAssignmentSerializer
        from apps.pricing.models import ClientProductAssignment
        from apps.brands.models import BrandSKU
        from django.utils import timezone

        serializer = BulkAssignmentSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        product_key = serializer.validated_data['product_key']
        subsidiary_ids = serializer.validated_data['client_subsidiary_ids']

        # Resolver BrandSKUs por product_key
        try:
            brand_skus = BrandSKU.objects.filter(product_key=product_key)
        except Exception:
            brand_skus = BrandSKU.objects.none()

        if not brand_skus.exists():
            return Response(
                {'detail': f'No se encontraron BrandSKUs para product_key={product_key}'},
                status=status.HTTP_404_NOT_FOUND,
            )

        created = 0
        skipped = 0
        errors = []

        for brand_sku in brand_skus:
            for subsidiary_id in subsidiary_ids:
                try:
                    _, was_created = ClientProductAssignment.objects.get_or_create(
                        brand_sku=brand_sku,
                        client_subsidiary_id=subsidiary_id,
                        defaults={
                            'is_active': True,
                            'cached_at': None,
                        },
                    )
                    if was_created:
                        created += 1
                    else:
                        skipped += 1
                except Exception as e:
                    errors.append({
                        'brand_sku_id': brand_sku.pk,
                        'client_subsidiary_id': subsidiary_id,
                        'error': str(e),
                    })

        return Response({
            'created': created,
            'skipped': skipped,
            'errors': errors,
        }, status=status.HTTP_200_OK)


class ResolvePriceView(APIView):
    """
    GET /api/pricing/resolve/
    Params: brand_sku_id, client_subsidiary_id, payment_days (opcional)
    Retorna precio resuelto. Portal recibe solo price+moq, backoffice recibe todo.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from apps.pricing.services import resolve_client_price
        from apps.pricing.serializers import PricingPortalSerializer, PricingInternalSerializer
        from apps.brands.models import BrandSKU

        brand_sku_id = request.query_params.get('brand_sku_id')
        client_subsidiary_id = request.query_params.get('client_subsidiary_id')
        payment_days = request.query_params.get('payment_days')

        if not brand_sku_id or not client_subsidiary_id:
            return Response(
                {'detail': 'brand_sku_id y client_subsidiary_id son requeridos'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            brand_sku = BrandSKU.objects.select_related('brand').get(pk=brand_sku_id)
        except BrandSKU.DoesNotExist:
            return Response({'detail': 'BrandSKU no encontrado'}, status=status.HTTP_404_NOT_FOUND)

        result = resolve_client_price(
            product=brand_sku,
            client=None,
            brand=brand_sku.brand,
            brand_sku_id=int(brand_sku_id),
            client_subsidiary_id=int(client_subsidiary_id),
            payment_days=int(payment_days) if payment_days else None,
        )

        if not result:
            return Response({'detail': 'No se pudo resolver precio'}, status=status.HTTP_404_NOT_FOUND)

        # Seleccionar serializer según rol del usuario
        is_portal_user = getattr(request.user, 'is_portal_client', False)
        if is_portal_user:
            serializer = PricingPortalSerializer(result)
        else:
            serializer = PricingInternalSerializer(result)

        return Response(serializer.data)


class ActivatePriceListView(APIView):
    """
    POST /api/pricing/pricelists/<version_id>/activate/
    Body opcional: { force: bool }
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, version_id):
        from apps.pricing.services import activate_pricelist

        force = request.data.get('force', False)
        try:
            result = activate_pricelist(
                version_id=version_id,
                force=force,
                activated_by=request.user.pk,
            )
            return Response(result, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class ValidateMOQView(APIView):
    """
    POST /api/pricing/validate-moq/
    Body: { brand_sku_id, client_subsidiary_id, quantities_by_size: {talla: qty} }
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        from apps.pricing.services import validate_moq

        brand_sku_id = request.data.get('brand_sku_id')
        client_subsidiary_id = request.data.get('client_subsidiary_id')
        quantities_by_size = request.data.get('quantities_by_size', {})

        if not brand_sku_id:
            return Response(
                {'detail': 'brand_sku_id es requerido'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        result = validate_moq(
            brand_sku_id=brand_sku_id,
            client_subsidiary_id=client_subsidiary_id,
            quantities_by_size=quantities_by_size,
        )
        status_code = status.HTTP_200_OK if result['valid'] else status.HTTP_422_UNPROCESSABLE_ENTITY
        return Response(result, status=status_code)
