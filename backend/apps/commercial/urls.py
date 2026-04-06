"""
S23-10/11/12 — URL routing de la app commercial.

Endpoints resultantes:

  Rebates (CEO + AGENT):
    GET  POST          /api/commercial/rebate-programs/
    GET  PUT PATCH DEL /api/commercial/rebate-programs/{id}/
    GET                /api/commercial/rebate-ledgers/
    GET                /api/commercial/rebate-ledgers/{id}/
    POST               /api/commercial/rebate-ledgers/{id}/approve/      (solo CEO)

  Portal cliente (CLIENT_*):
    GET                /api/commercial/portal/rebate-progress/
    GET                /api/commercial/portal/rebate-progress/{id}/

  Comisiones (solo CEO):
    GET  POST          /api/commercial/commission-rules/
    GET  PUT PATCH DEL /api/commercial/commission-rules/{id}/

  ArtifactPolicy (CEO + AGENT):
    GET  POST          /api/commercial/artifact-policies/
    GET  PATCH         /api/commercial/artifact-policies/{id}/
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.commercial.views import (
    ArtifactPolicyViewSet,
    CommissionRuleViewSet,
    RebateLedgerViewSet,
    RebateProgramViewSet,
    RebateProgressPortalViewSet,
)

router = DefaultRouter()
router.register(r'rebate-programs', RebateProgramViewSet, basename='rebate-program')
router.register(r'rebate-ledgers', RebateLedgerViewSet, basename='rebate-ledger')
router.register(r'portal/rebate-progress', RebateProgressPortalViewSet, basename='rebate-progress-portal')
router.register(r'commission-rules', CommissionRuleViewSet, basename='commission-rule')
router.register(r'artifact-policies', ArtifactPolicyViewSet, basename='artifact-policy')

urlpatterns = [
    path('', include(router.urls)),
]
