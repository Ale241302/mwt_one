"""
Sprint 1 — URL Registry (Tarea 8)
18 URL patterns under /api/expedientes/
Ref: LOTE_SM_SPRINT1 Item 7
"""
from django.urls import path
from apps.expedientes.views import (
    CreateExpedienteView,
    RegisterOCView,
    RegisterProformaView,
    DecideModeView,
    ConfirmSAPView,
    ConfirmProductionView,
    RegisterShipmentView,
    RegisterFreightQuoteView,
    RegisterCustomsView,
    ApproveDispatchView,
    ConfirmDepartureView,
    ConfirmArrivalView,
    IssueInvoiceView,
    CloseExpedienteView,
    RegisterCostView,
    CancelExpedienteView,
    BlockExpedienteView,
    UnblockExpedienteView,
    RegisterPaymentView,
    SupersedeArtifactView,
    VoidArtifactView,
    ListExpedientesView,
    ExpedienteBundleView,
)

app_name = 'expedientes'

urlpatterns = [
    # C1: CreateExpediente (POST /api/expedientes/)
    path('', CreateExpedienteView.as_view(), name='create'),
    
    # C2-C5: REGISTRO phase
    path('<uuid:pk>/register-oc/', RegisterOCView.as_view(), name='register-oc'),
    path('<uuid:pk>/register-proforma/', RegisterProformaView.as_view(), name='register-proforma'),
    path('<uuid:pk>/decide-mode/', DecideModeView.as_view(), name='decide-mode'),
    path('<uuid:pk>/confirm-sap/', ConfirmSAPView.as_view(), name='confirm-sap'),

    # C6-C10: PRODUCCION + PREPARACION phase
    path('<uuid:pk>/confirm-production/', ConfirmProductionView.as_view(), name='confirm-production'),
    path('<uuid:pk>/register-shipment/', RegisterShipmentView.as_view(), name='register-shipment'),
    path('<uuid:pk>/register-freight-quote/', RegisterFreightQuoteView.as_view(), name='register-freight-quote'),
    path('<uuid:pk>/register-customs/', RegisterCustomsView.as_view(), name='register-customs'),
    path('<uuid:pk>/approve-dispatch/', ApproveDispatchView.as_view(), name='approve-dispatch'),

    # C11-C14: DESPACHO → CERRADO phase
    path('<uuid:pk>/confirm-departure/', ConfirmDepartureView.as_view(), name='confirm-departure'),
    path('<uuid:pk>/confirm-arrival/', ConfirmArrivalView.as_view(), name='confirm-arrival'),
    path('<uuid:pk>/issue-invoice/', IssueInvoiceView.as_view(), name='issue-invoice'),
    path('<uuid:pk>/close/', CloseExpedienteView.as_view(), name='close'),

    # C15: RegisterCost
    path('<uuid:pk>/register-cost/', RegisterCostView.as_view(), name='register-cost'),

    # C16-C18: Cancel + Block + Unblock
    path('<uuid:pk>/cancel/', CancelExpedienteView.as_view(), name='cancel'),
    path('<uuid:pk>/block/', BlockExpedienteView.as_view(), name='block'),
    path('<uuid:pk>/unblock/', UnblockExpedienteView.as_view(), name='unblock'),

    # C21: RegisterPayment
    path('<uuid:pk>/register-payment/', RegisterPaymentView.as_view(), name='register-payment'),
]
