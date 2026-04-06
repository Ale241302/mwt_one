# Sprint 22 - S22-08: Views para Bulk Assignment y resolve de precio
# Sprint 22 - S22-11/12: Upload y Confirm de PriceListVersion
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated
from django.db.models import Count, Q
from rest_framework.decorators import action



# -------------------------------------------------------------------
# S22-08: Bulk Assignment
# -------------------------------------------------------------------

class BulkAssignmentView(APIView):
    """
    POST /api/pricing/client-assignments/bulk/
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

        serializer = BulkAssignmentSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        product_key = serializer.validated_data['product_key']
        subsidiary_ids = serializer.validated_data['client_subsidiary_ids']

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
                        defaults={'is_active': True, 'cached_at': None},
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

        return Response({'created': created, 'skipped': skipped, 'errors': errors})


# -------------------------------------------------------------------
# S22-05: Resolve precio
# -------------------------------------------------------------------

class ResolvePriceView(APIView):
    """
    GET /api/pricing/resolve/
    Params: brand_sku_id, client_subsidiary_id, payment_days (opcional)
    Portal recibe solo price+moq, backoffice recibe todo.
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

        is_portal_user = getattr(request.user, 'is_portal_client', False)
        serializer = PricingPortalSerializer(result) if is_portal_user else PricingInternalSerializer(result)
        return Response(serializer.data)


# -------------------------------------------------------------------
# S22-06: Activar pricelist
# -------------------------------------------------------------------

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
            return Response(result)
        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)


# -------------------------------------------------------------------
# S22-07: Validar MOQ
# -------------------------------------------------------------------

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
        http_status = status.HTTP_200_OK if result['valid'] else status.HTTP_422_UNPROCESSABLE_ENTITY
        return Response(result, status=http_status)


# -------------------------------------------------------------------
# S22-11: Upload pricelist CSV/Excel
# -------------------------------------------------------------------

class PriceListUploadView(APIView):
    """
    POST /api/pricing/pricelists/upload/
    Multipart: file (CSV o Excel), brand_id (int)

    Parsea el archivo con estructura Marluvas, retorna preview + reporte.
    NO crea PriceListVersion todavía.

    Response:
    {
        session_id: str,
        valid_lines: int,
        warnings: [...],
        errors: [...],
        preview: [...primeras 5 líneas]
    }
    """
    permission_classes = [IsAuthenticated]
    parser_classes = None  # usa los defaults DRF (multipart + json)

    def post(self, request):
        from apps.pricing.parsers import parse_marluvas_pricelist
        from rest_framework.parsers import MultiPartParser

        file = request.FILES.get('file')
        brand_id = request.data.get('brand_id')

        if not file:
            return Response(
                {'detail': 'Campo "file" requerido.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not brand_id:
            return Response(
                {'detail': 'Campo "brand_id" requerido.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            brand_id = int(brand_id)
        except (ValueError, TypeError):
            return Response(
                {'detail': 'brand_id debe ser un entero.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            result = parse_marluvas_pricelist(file, brand_id=brand_id)

            # Si solo hay errores críticos (sin session_id) → 400
            if not result['session_id']:
                return Response(result, status=status.HTTP_400_BAD_REQUEST)

            # Si hay líneas válidas (aunque haya warnings/errores de fila) → 200
            return Response(result, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'detail': f'Error procesando el archivo: {str(e)}',
                'valid_lines': 0,
                'errors': [{'row': None, 'message': str(e)}],
                'session_id': None
            }, status=status.HTTP_400_BAD_REQUEST)


# -------------------------------------------------------------------
# S22-12: Confirmar upload → crear PriceListVersion + GradeItems
# -------------------------------------------------------------------

class PriceListConfirmView(APIView):
    """
    POST /api/pricing/pricelists/confirm/
    Body: {
        session_id: str,
        brand_id: int,
        version_label: str,
        notes: str (opcional)
    }

    Crea PriceListVersion (is_active=False) + N PriceListGradeItems.
    La versión se activa manualmente por el CEO desde Brand Console.

    Response:
    {
        version_id: int,
        version_label: str,
        items_created: int,
        is_active: false,
        warnings: [...]
    }
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        from apps.pricing.parsers import get_upload_session, clear_upload_session
        from apps.pricing.models import PriceListVersion, PriceListGradeItem
        from apps.brands.models import Brand, BrandSKU
        from decimal import Decimal

        session_id = request.data.get('session_id')
        brand_id = request.data.get('brand_id')
        version_label = request.data.get('version_label', '').strip()
        notes = request.data.get('notes', '').strip()

        # Validaciones básicas
        if not session_id:
            return Response(
                {'detail': 'session_id es requerido. Llama primero a /upload/.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not brand_id:
            return Response(
                {'detail': 'brand_id es requerido.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not version_label:
            return Response(
                {'detail': 'version_label es requerido (ej: "2025-Q2").'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Recuperar sesión de upload
        session = get_upload_session(session_id)
        if not session:
            return Response(
                {
                    'detail': (
                        f'Sesión de upload "{session_id}" no encontrada o expirada. '
                        'Sube el archivo nuevamente.'
                    )
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        valid_rows = session.get('valid_rows', [])
        if not valid_rows:
            return Response(
                {'detail': 'La sesión no tiene líneas válidas para confirmar.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Verificar que el brand existe
        try:
            brand = Brand.objects.get(pk=brand_id)
        except Brand.DoesNotExist:
            return Response(
                {'detail': f'Brand {brand_id} no encontrado.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Crear PriceListVersion (is_active=False — el CEO activa manualmente)
        version = PriceListVersion.objects.create(
            brand=brand,
            version_label=version_label,
            notes=notes,
            uploaded_by=request.user,
            is_active=False,
        )

        # Crear PriceListGradeItems
        items_created = 0
        confirm_warnings = []

        # Precarga BrandSKUs del brand para intentar match por reference_code
        sku_map = {
            sku.reference_code: sku
            for sku in BrandSKU.objects.filter(brand=brand)
            if hasattr(sku, 'reference_code') and sku.reference_code
        }

        for row in valid_rows:
            reference_code = row['reference_code']

            # Intentar match con BrandSKU existente (nullable — no bloquea si no encuentra)
            matched_sku = sku_map.get(reference_code)
            if not matched_sku:
                confirm_warnings.append({
                    'reference_code': reference_code,
                    'message': (
                        f'No se encontró BrandSKU con reference_code="{reference_code}" '
                        f'para brand {brand_id}. brand_sku quedará NULL.'
                    ),
                })

            try:
                PriceListGradeItem.objects.create(
                    pricelist_version=version,
                    reference_code=reference_code,
                    brand_sku=matched_sku,
                    unit_price_usd=Decimal(str(row['unit_price_usd'])),
                    grade_label=row.get('grade_label', ''),
                    tip_type=row.get('tip_type', ''),
                    insole_type=row.get('insole_type', ''),
                    ncm=row.get('ncm', ''),
                    ca_number=row.get('ca_number', ''),
                    factory_code=row.get('factory_code', ''),
                    factory_center=row.get('factory_center', ''),
                    size_multipliers=row.get('size_multipliers', {}),
                )
                items_created += 1
            except Exception as e:
                confirm_warnings.append({
                    'reference_code': reference_code,
                    'message': f'Error creando item: {str(e)}',
                })

        # Limpiar sesión de memoria
        clear_upload_session(session_id)

        return Response({
            'version_id': version.pk,
            'version_label': version.version_label,
            'items_created': items_created,
            'is_active': version.is_active,
            'warnings': confirm_warnings,
        }, status=status.HTTP_201_CREATED)


# -------------------------------------------------------------------
# S22-01: Listar versiones (Brand Console)
# -------------------------------------------------------------------

class PriceListVersionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    GET /api/pricing/pricelists/
    Listar y recuperar versiones de pricelist por marca.
    """
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        from apps.pricing.serializers import PriceListVersionSerializer
        return PriceListVersionSerializer

    def get_queryset(self):
        from apps.pricing.models import PriceListVersion
        qs = PriceListVersion.objects.all().select_related('uploaded_by').annotate(
            items_count=Count('grade_items')
        ).order_by('-created_at')
        brand_id = self.request.query_params.get('brand_id')
        if brand_id:
            qs = qs.filter(brand_id=brand_id)
        return qs

    @action(detail=True, methods=['get'])
    def items(self, request, pk=None):
        from apps.pricing.models import PriceListGradeItem
        from apps.pricing.serializers import PriceListGradeItemSerializer
        items = PriceListGradeItem.objects.filter(pricelist_version_id=pk)
        items = PriceListGradeItem.objects.filter(pricelist_version_id=pk)
        serializer = PriceListGradeItemSerializer(items, many=True)
        return Response(serializer.data)



# -------------------------------------------------------------------
# S22-16: Payment Terms (EarlyPaymentPolicy)
# -------------------------------------------------------------------

class EarlyPaymentPolicyViewSet(viewsets.ModelViewSet):
    """
    CRUD /api/pricing/early-payment-policies/
    """
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        from apps.pricing.serializers import EarlyPaymentPolicySerializer
        return EarlyPaymentPolicySerializer

    def get_queryset(self):
        from apps.pricing.models import EarlyPaymentPolicy
        qs = EarlyPaymentPolicy.objects.all().prefetch_related('tiers')
        brand_id = self.request.query_params.get('brand_id')
        if brand_id:
            qs = qs.filter(brand_id=brand_id)
        return qs



# -------------------------------------------------------------------
# S22-17: Assignments (CPA)
# -------------------------------------------------------------------

class ClientAssignmentViewSet(viewsets.ReadOnlyModelViewSet):
    """
    GET /api/pricing/client-assignments/
    """
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        from apps.pricing.serializers import ClientProductAssignmentSerializer
        return ClientProductAssignmentSerializer

    def get_queryset(self):
        from apps.pricing.models import ClientProductAssignment
        qs = ClientProductAssignment.objects.all().select_related(
            'client_subsidiary', 'brand_sku', 'brand_sku__product'
        )
        brand_id = self.request.query_params.get('brand_id')
        if brand_id:
            qs = qs.filter(brand_sku__brand_id=brand_id)
        return qs



# -------------------------------------------------------------------
# S22-15: Catalog Enrichment (Brand Console)
# -------------------------------------------------------------------

class CatalogBrandSKUView(APIView):
    """
    GET /api/pricing/catalog/brand-skus/?brand_id=X
    Retorna lista de BrandSKUs con el precio resuelto inyectado.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from apps.brands.models import BrandSKU
        from apps.pricing.services import resolve_client_price
        
        brand_id = request.query_params.get('brand_id')
        if not brand_id:
            return Response({'detail': 'brand_id es requerido'}, status=400)

        skus = BrandSKU.objects.filter(brand_id=brand_id, is_active=True).select_related('product')
        
        results = []
        for sku in skus:
            # Resolvemos el precio (sin cliente ni subsidiaria, para ver el base de la marca)
            res = resolve_client_price(
                product=sku.product,
                client=None,
                brand=sku.brand,
                brand_sku_id=sku.id,
                client_subsidiary_id=None
            )
            
            results.append({
                'id': sku.id,
                'sku_code': sku.sku_code,
                'reference_code': sku.reference_code,
                'description': sku.product.name,
                'is_active': sku.is_active,
                'price_resolved': res
            })

        return Response(results)