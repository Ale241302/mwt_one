# Sprint 22 - URLs del pricing engine
from django.urls import path
from apps.pricing.views import (
    BulkAssignmentView,
    ResolvePriceView,
    ActivatePriceListView,
    ValidateMOQView,
    PriceListUploadView,
    PriceListConfirmView,
)

urlpatterns = [
    # S22-08: Bulk assignment
    path(
        'client-assignments/bulk/',
        BulkAssignmentView.as_view(),
        name='pricing-bulk-assignment',
    ),
    # S22-05: Resolve precio
    path(
        'resolve/',
        ResolvePriceView.as_view(),
        name='pricing-resolve',
    ),
    # S22-06: Activar pricelist
    path(
        'pricelists/<int:version_id>/activate/',
        ActivatePriceListView.as_view(),
        name='pricing-activate-pricelist',
    ),
    # S22-07: Validar MOQ
    path(
        'validate-moq/',
        ValidateMOQView.as_view(),
        name='pricing-validate-moq',
    ),
    # S22-11: Upload pricelist CSV/Excel (preview, sin crear versión)
    path(
        'pricelists/upload/',
        PriceListUploadView.as_view(),
        name='pricing-pricelist-upload',
    ),
    # S22-12: Confirmar upload → crear PriceListVersion + GradeItems
    path(
        'pricelists/confirm/',
        PriceListConfirmView.as_view(),
        name='pricing-pricelist-confirm',
    ),
]
