"""
Sprint 1-4 — URL Configuration for /api/expedientes/
Ref: LOTE_SM_SPRINT1 Item 7
Sprint 4: Added C22/C23/C24, costs, invoice, comparison, mirror-pdf
"""
from django.urls import path
from apps.expedientes.views import (
    CreateExpedienteView,
    RegisterOCView, RegisterProformaView, DecideModeView, ConfirmSAPView,
    ConfirmProductionView, RegisterShipmentView, RegisterFreightQuoteView,
    RegisterCustomsView, ApproveDispatchView, ConfirmDepartureView,
    ConfirmArrivalView, IssueInvoiceView, CloseExpedienteView,
    RegisterCostView, CancelExpedienteView, BlockExpedienteView,
    UnblockExpedienteView, RegisterPaymentView,
    SupersedeArtifactView, VoidArtifactView,
    # Sprint 4
    CostsListView, CostsSummaryView,
    InvoiceSuggestionView, InvoiceView,
    FinancialComparisonView,
    MaterializeLogisticsView, AddLogisticsOptionView, DecideLogisticsView,
    MirrorPDFView,
    # Sprint 5
    RegisterCompensationView, LogisticsSuggestionsView, AddShipmentUpdateView,
    HandoffSuggestionView, LiquidationPaymentSuggestionView,
)

app_name = 'expedientes'

urlpatterns = [
    # ── C1: Create ──
    path('create/', CreateExpedienteView.as_view(), name='create'),

    # ── C2-C14: Command endpoints ──
    path('<uuid:pk>/register-oc/', RegisterOCView.as_view(), name='register-oc'),
    path('<uuid:pk>/register-proforma/', RegisterProformaView.as_view(), name='register-proforma'),
    path('<uuid:pk>/decide-mode/', DecideModeView.as_view(), name='decide-mode'),
    path('<uuid:pk>/confirm-sap/', ConfirmSAPView.as_view(), name='confirm-sap'),
    path('<uuid:pk>/confirm-production/', ConfirmProductionView.as_view(), name='confirm-production'),
    path('<uuid:pk>/register-shipment/', RegisterShipmentView.as_view(), name='register-shipment'),
    path('<uuid:pk>/register-freight-quote/', RegisterFreightQuoteView.as_view(), name='register-freight-quote'),
    path('<uuid:pk>/register-customs/', RegisterCustomsView.as_view(), name='register-customs'),
    path('<uuid:pk>/approve-dispatch/', ApproveDispatchView.as_view(), name='approve-dispatch'),
    path('<uuid:pk>/confirm-departure/', ConfirmDepartureView.as_view(), name='confirm-departure'),
    path('<uuid:pk>/confirm-arrival/', ConfirmArrivalView.as_view(), name='confirm-arrival'),
    path('<uuid:pk>/issue-invoice/', IssueInvoiceView.as_view(), name='issue-invoice'),
    path('<uuid:pk>/close/', CloseExpedienteView.as_view(), name='close'),

    # ── C15-C18: Ops ──
    path('<uuid:pk>/register-cost/', RegisterCostView.as_view(), name='register-cost'),
    path('<uuid:pk>/cancel/', CancelExpedienteView.as_view(), name='cancel'),
    path('<uuid:pk>/block/', BlockExpedienteView.as_view(), name='block'),
    path('<uuid:pk>/unblock/', UnblockExpedienteView.as_view(), name='unblock'),

    # ── C19-C21: Sprint 2/3 ──
    path('<uuid:pk>/supersede-artifact/', SupersedeArtifactView.as_view(), name='supersede-artifact'),
    path('<uuid:pk>/void-artifact/', VoidArtifactView.as_view(), name='void-artifact'),
    path('<uuid:pk>/register-payment/', RegisterPaymentView.as_view(), name='register-payment'),

    # ── Sprint 4: C22-C24 Logistics ──
    path('<uuid:pk>/materialize-logistics/', MaterializeLogisticsView.as_view(), name='materialize-logistics'),
    path('<uuid:pk>/add-logistics-option/', AddLogisticsOptionView.as_view(), name='add-logistics-option'),
    path('<uuid:pk>/decide-logistics/', DecideLogisticsView.as_view(), name='decide-logistics'),

    # ── Sprint 4: Read endpoints ──
    path('<uuid:pk>/costs/', CostsListView.as_view(), name='costs'),
    path('<uuid:pk>/costs/summary/', CostsSummaryView.as_view(), name='costs-summary'),
    path('<uuid:pk>/invoice-suggestion/', InvoiceSuggestionView.as_view(), name='invoice-suggestion'),
    path('<uuid:pk>/invoice/', InvoiceView.as_view(), name='invoice'),
    path('<uuid:pk>/financial-comparison/', FinancialComparisonView.as_view(), name='financial-comparison'),
    path('<uuid:pk>/mirror-pdf/', MirrorPDFView.as_view(), name='mirror-pdf'),

    # ── Sprint 5: C29, C36, Suggestions ──
    path('<uuid:pk>/register-compensation/', RegisterCompensationView.as_view(), name='register-compensation'),
    path('<uuid:pk>/logistics-suggestions/', LogisticsSuggestionsView.as_view(), name='logistics-suggestions'),
    path('<uuid:pk>/add-shipment-update/', AddShipmentUpdateView.as_view(), name='add-shipment-update'),
    # S5-06: Handoff suggestion
    path('<uuid:pk>/handoff-suggestion/', HandoffSuggestionView.as_view(), name='handoff-suggestion'),
    # S5-10: Liquidation payment suggestion
    path('<uuid:pk>/liquidation-payment-suggestion/', LiquidationPaymentSuggestionView.as_view(), name='liquidation-payment-suggestion'),
]
