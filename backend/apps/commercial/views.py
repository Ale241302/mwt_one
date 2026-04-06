"""
S23-10/11/12 — Views DRF para la capa comercial.

Endpoints:
  S23-10  GET/POST   /api/commercial/rebate-programs/
          GET/PUT/PATCH/DELETE /api/commercial/rebate-programs/{id}/
          GET        /api/commercial/rebate-ledgers/
          POST       /api/commercial/rebate-ledgers/{id}/approve/
          GET        /api/commercial/portal/rebate-progress/

  S23-11  GET/POST   /api/commercial/commission-rules/
          GET/PUT/PATCH/DELETE /api/commercial/commission-rules/{id}/

  S23-12  GET        /api/commercial/artifact-policies/
          POST       /api/commercial/artifact-policies/
          GET/PATCH  /api/commercial/artifact-policies/{id}/
"""
from django.db.models import Count
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.commercial.models import (
    BrandArtifactPolicyVersion,
    CommissionRule,
    RebateAssignment,
    RebateLedger,
    RebateProgram,
)
from apps.commercial.permissions import (
    IsCEO,
    IsCEOOrInternalAgent,
    IsClientUser,
)
from apps.commercial.serializers import (
    BrandArtifactPolicyVersionSerializer,
    CommissionRuleSerializer,
    RebateLedgerInternalSerializer,
    RebateProgramInternalSerializer,
    RebateProgressPortalSerializer,
)


# ---------------------------------------------------------------------------
# S23-10 — RebateProgram (CEO + AGENT)
# ---------------------------------------------------------------------------

class RebateProgramViewSet(viewsets.ModelViewSet):
    """
    S23-10: CRUD completo de programas de rebate.
    Acceso: CEO o agentes internos.
    Los agentes ven solo programas de las marcas que tienen asignadas.
    """
    serializer_class = RebateProgramInternalSerializer
    permission_classes = [IsCEOOrInternalAgent]

    def get_queryset(self):
        user = self.request.user
        role = getattr(user, 'role', '') or ''

        qs = RebateProgram.objects.select_related('brand').prefetch_related('product_inclusions')

        # CEO ve todos los programas
        if role == 'CEO':
            return qs.order_by('-valid_from')

        # Agentes: scope por brand asignada al agente
        # Se asume que el usuario tiene un atributo brand_id o relacion brand
        agent_brand = getattr(user, 'brand_id', None) or getattr(user, 'brand', None)
        if agent_brand:
            brand_id = agent_brand.pk if hasattr(agent_brand, 'pk') else agent_brand
            return qs.filter(brand_id=brand_id).order_by('-valid_from')

        return qs.none()


# ---------------------------------------------------------------------------
# S23-10 — RebateLedger (CEO + AGENT) + Approve (CEO only)
# ---------------------------------------------------------------------------

class RebateLedgerViewSet(viewsets.ReadOnlyModelViewSet):
    """
    S23-10: Vista de ledgers de rebate (solo lectura para agentes/CEO).
    Agrega entries_count via annotate.
    La accion 'approve' es exclusiva del CEO.
    """
    serializer_class = RebateLedgerInternalSerializer
    permission_classes = [IsCEOOrInternalAgent]

    def get_queryset(self):
        try:
            user = self.request.user
            role = getattr(user, 'role', '') or ''

            qs = (
                RebateLedger.objects
                .select_related(
                    'rebate_assignment__rebate_program__brand',
                    'rebate_assignment__client',
                    'rebate_assignment__subsidiary',
                    'liquidated_by',
                )
                .annotate(entries_count=Count('accrual_entries'))
            )

            if role == 'CEO':
                return qs.order_by('-period_start')

            # Agentes: scope por brand asignada
            agent_brand = getattr(user, 'brand_id', None) or getattr(user, 'brand', None)
            if agent_brand:
                brand_id = agent_brand.pk if hasattr(agent_brand, 'pk') else agent_brand
                return qs.filter(
                    rebate_assignment__rebate_program__brand_id=brand_id
                ).order_by('-period_start')

            return qs.none()
        except Exception:
            return RebateLedger.objects.none()

    @action(
        detail=True,
        methods=['post'],
        url_path='approve',
        permission_classes=[IsCEO],
    )
    def approve(self, request, pk=None):
        """
        POST /api/commercial/rebate-ledgers/{id}/approve/
        Cuerpo: { "liquidation_type": "credit_note" | "bank_transfer" | "product_credit" }
        Solo CEO.
        """
        from apps.commercial.services.rebates import approve_rebate_liquidation

        liquidation_type = request.data.get('liquidation_type')
        if not liquidation_type:
            return Response(
                {'detail': 'El campo liquidation_type es obligatorio.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            approve_rebate_liquidation(
                ledger_id=str(pk),
                liquidation_type=liquidation_type,
                approved_by_user=request.user,
            )
        except ValueError as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        ledger = (
            RebateLedger.objects
            .annotate(entries_count=Count('accrual_entries'))
            .get(pk=pk)
        )
        serializer = self.get_serializer(ledger)
        return Response(serializer.data, status=status.HTTP_200_OK)


# ---------------------------------------------------------------------------
# S23-10 — Portal cliente: progreso de rebate (IsClientUser)
# ---------------------------------------------------------------------------

class RebateProgressPortalViewSet(viewsets.ReadOnlyModelViewSet):
    """
    S23-10: Vista de progreso de rebate para el portal del cliente.
    Acceso: solo usuarios CLIENT_*.
    Queryset scoped por subsidiary del usuario autenticado.
    NUNCA expone: rebate_value, accrued_amount, ni umbrales absolutos.
    """
    serializer_class = RebateProgressPortalSerializer
    permission_classes = [IsClientUser]

    def get_queryset(self):
        user = self.request.user

        # El usuario cliente debe tener un subsidiary asociado
        subsidiary_id = (
            getattr(user, 'subsidiary_id', None)
            or getattr(user, 'subsidiary', None)
        )
        if subsidiary_id and hasattr(subsidiary_id, 'pk'):
            subsidiary_id = subsidiary_id.pk

        if not subsidiary_id:
            return RebateLedger.objects.none()

        return (
            RebateLedger.objects
            .select_related(
                'rebate_assignment__rebate_program',
                'rebate_assignment__subsidiary',
                'rebate_assignment',
            )
            .filter(
                rebate_assignment__subsidiary_id=subsidiary_id,
                rebate_assignment__is_active=True,
            )
            .order_by('-period_start')
        )


# ---------------------------------------------------------------------------
# S23-11 — CommissionRule (solo CEO)
# ---------------------------------------------------------------------------

class CommissionRuleViewSet(viewsets.ModelViewSet):
    """
    S23-11: CRUD completo de reglas de comision.
    Acceso EXCLUSIVO para CEO. Nunca AGENT, nunca CLIENT.
    """
    serializer_class = CommissionRuleSerializer
    permission_classes = [IsCEO]

    def get_queryset(self):
        return (
            CommissionRule.objects
            .select_related('brand', 'client', 'subsidiary')
            .order_by('-created_at')
        )


# ---------------------------------------------------------------------------
# S23-12 — BrandArtifactPolicyVersion (CEO + AGENT)
# ---------------------------------------------------------------------------

class ArtifactPolicyViewSet(viewsets.ModelViewSet):
    """
    S23-12: Gestion de versiones de ArtifactPolicy por marca.
    Acceso: CEO o agentes internos.

    Reglas de negocio:
    - NO editar in-place (PUT esta deshabilitado).
      Cada cambio debe crear una nueva version via POST.
    - PATCH solo permite actualizar 'notes' e 'is_active'.
    """
    serializer_class = BrandArtifactPolicyVersionSerializer
    permission_classes = [IsCEOOrInternalAgent]
    # Desactivar PUT — solo PATCH permitido
    http_method_names = ['get', 'post', 'patch', 'head', 'options']

    def get_queryset(self):
        user = self.request.user
        role = getattr(user, 'role', '') or ''

        qs = BrandArtifactPolicyVersion.objects.select_related('brand', 'superseded_by')

        if role == 'CEO':
            return qs.order_by('brand_id', '-version')

        # Agentes: scope por brand asignada
        agent_brand = getattr(user, 'brand_id', None) or getattr(user, 'brand', None)
        if agent_brand:
            brand_id = agent_brand.pk if hasattr(agent_brand, 'pk') else agent_brand
            return qs.filter(brand_id=brand_id).order_by('-version')

        return qs.none()

    def partial_update(self, request, *args, **kwargs):
        """
        PATCH: solo permite actualizar 'notes' e 'is_active'.
        Cualquier otro campo es ignorado silenciosamente.
        """
        allowed_fields = {'notes', 'is_active'}
        filtered_data = {k: v for k, v in request.data.items() if k in allowed_fields}
        serializer = self.get_serializer(
            self.get_object(),
            data=filtered_data,
            partial=True,
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
