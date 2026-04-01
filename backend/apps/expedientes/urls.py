"""
Sprint 1-5 – URL Configuration for /api/expedientes/
Ref: LOTE_SM_SPRINT1 Item 7
Sprint 12: Unified Command Dispatching
Sprint 17: Portal endpoints added (S17-04)
Sprint 20: S20-11 ProformaCreateView, S20-10 ProformaModeChangeView
Sprint 20+: Alias /commands/ para compatibilidad con frontend
Sprint 21 (S21): Admin advance/revert state + add/remove artifact policy
"""
from django.urls import path
from apps.expedientes.views import (
    CreateExpedienteView,
    CommandDispatchView,
    # Read views
    CostsListView, CostsSummaryView,
    InvoiceSuggestionView, InvoiceView,
    FinancialComparisonView,
    LogisticsSuggestionsView,
    HandoffSuggestionView, LiquidationPaymentSuggestionView,
    MirrorPDFView,
    FinancialSummaryView, DocumentsListView,
    CEOOverrideView,
)
# S17-04: Portal views
from apps.expedientes.views_portal import (
    PortalExpedienteListView,
    PortalExpedienteDetailView,
    PortalExpedienteArtifactsView,
)
# S20-11 / S20-10
from apps.expedientes.views_s20 import (
    ProformaCreateView,
    ProformaModeChangeView,
)
# S21: Admin views (state navigation + policy management)
from apps.expedientes.views_admin import (
    AdvanceStateView,
    RevertStateView,
    AddArtifactToPolicyView,
    RemoveArtifactFromPolicyView,
)

app_name = 'expedientes'

urlpatterns = [
    # ── C1: Create ──
    path('create/', CreateExpedienteView.as_view(), name='create'),

    # ── Sprint 12: Generic Dispatcher (New) ──
    path('<uuid:pk>/command/<str:cmd_id>/', CommandDispatchView.as_view(), name='command-dispatch'),

    # ── Backward Compatibility: Map specific command URLs to Dispatcher ──
    path('<uuid:pk>/register-oc/', CommandDispatchView.as_view(), {'cmd_id': 'C3'}, name='register-oc'),
    path('<uuid:pk>/register-proforma/', CommandDispatchView.as_view(), {'cmd_id': 'C2'}, name='register-proforma'),
    path('<uuid:pk>/decide-mode/', CommandDispatchView.as_view(), {'cmd_id': 'C4'}, name='decide-mode'),
    path('<uuid:pk>/confirm-sap/', CommandDispatchView.as_view(), {'cmd_id': 'C5'}, name='confirm-sap'),
    path('<uuid:pk>/confirm-production/', CommandDispatchView.as_view(), {'cmd_id': 'C6'}, name='confirm-production'),
    path('<uuid:pk>/register-shipment/', CommandDispatchView.as_view(), {'cmd_id': 'C7'}, name='register-shipment'),
    path('<uuid:pk>/register-freight-quote/', CommandDispatchView.as_view(), {'cmd_id': 'C8'}, name='register-freight-quote'),
    path('<uuid:pk>/register-customs/', CommandDispatchView.as_view(), {'cmd_id': 'C9'}, name='register-customs'),
    path('<uuid:pk>/approve-dispatch/', CommandDispatchView.as_view(), {'cmd_id': 'C10'}, name='approve-dispatch'),
    path('<uuid:pk>/confirm-departure/', CommandDispatchView.as_view(), {'cmd_id': 'C11B'}, name='confirm-departure-china'),
    path('<uuid:pk>/confirm-departure-mwt/', CommandDispatchView.as_view(), {'cmd_id': 'C11'}, name='confirm-departure'),
    path('<uuid:pk>/confirm-arrival/', CommandDispatchView.as_view(), {'cmd_id': 'C12'}, name='confirm-arrival'),
    path('<uuid:pk>/issue-invoice/', CommandDispatchView.as_view(), {'cmd_id': 'C13'}, name='issue-invoice'),
    path('<uuid:pk>/close/', CommandDispatchView.as_view(), {'cmd_id': 'C14'}, name='close'),

    # ── C15-C18: Ops ──
    path('<uuid:pk>/register-cost/', CommandDispatchView.as_view(), {'cmd_id': 'C15'}, name='register-cost'),
    path('<uuid:pk>/cancel/', CommandDispatchView.as_view(), {'cmd_id': 'C16'}, name='cancel'),
    path('<uuid:pk>/block/', CommandDispatchView.as_view(), {'cmd_id': 'C17'}, name='block'),
    path('<uuid:pk>/unblock/', CommandDispatchView.as_view(), {'cmd_id': 'C18'}, name='unblock'),

    # ── C19-C21: Sprint 2/3 ──
    path('<uuid:pk>/supersede-artifact/', CommandDispatchView.as_view(), {'cmd_id': 'C19'}, name='supersede-artifact'),
    path('<uuid:pk>/void-artifact/', CommandDispatchView.as_view(), {'cmd_id': 'C20'}, name='void-artifact'),
    path('<uuid:pk>/register-payment/', CommandDispatchView.as_view(), {'cmd_id': 'C21'}, name='register-payment'),

    # ── C22 Factura Comisión ──
    path('<uuid:pk>/issue-commission-invoice/', CommandDispatchView.as_view(), {'cmd_id': 'C22'}, name='issue-commission-invoice'),

    # ── Logistics Commands ──
    path('<uuid:pk>/materialize-logistics/', CommandDispatchView.as_view(), {'cmd_id': 'C30'}, name='materialize-logistics'),
    path('<uuid:pk>/add-logistics-option/', CommandDispatchView.as_view(), {'cmd_id': 'C23'}, name='add-logistics-option'),
    path('<uuid:pk>/decide-logistics/', CommandDispatchView.as_view(), {'cmd_id': 'C24'}, name='decide-logistics'),

    # ── Sprint 5 Commands ──
    path('<uuid:pk>/register-compensation/', CommandDispatchView.as_view(), {'cmd_id': 'C29'}, name='register-compensation'),
    path('<uuid:pk>/add-shipment-update/', CommandDispatchView.as_view(), {'cmd_id': 'C36'}, name='add-shipment-update'),

    # ── S17-03: REOPEN ──
    path('<uuid:pk>/reopen/', CommandDispatchView.as_view(), {'cmd_id': 'REOPEN'}, name='reopen'),

    # ── S20-11: Crear proforma ──
    path('<uuid:pk>/proformas/', ProformaCreateView.as_view(), name='proforma-create'),

    # ── S20-10: Cambiar modo de proforma ──
    path('<uuid:pk>/proforma/<uuid:pf_id>/change-mode/', ProformaModeChangeView.as_view(), name='proforma-change-mode'),

    # ── Read endpoints ──
    path('<uuid:pk>/costs/', CostsListView.as_view(), name='costs'),
    path('<uuid:pk>/costs/summary/', CostsSummaryView.as_view(), name='costs-summary'),
    path('<uuid:pk>/invoice-suggestion/', InvoiceSuggestionView.as_view(), name='invoice-suggestion'),
    path('<uuid:pk>/invoice/', InvoiceView.as_view(), name='invoice'),
    path('<uuid:pk>/financial-comparison/', FinancialComparisonView.as_view(), name='financial-comparison'),
    path('<uuid:pk>/mirror-pdf/', MirrorPDFView.as_view(), name='mirror-pdf'),
    path('<uuid:pk>/logistics-suggestions/', LogisticsSuggestionsView.as_view(), name='logistics-suggestions'),
    path('<uuid:pk>/handoff-suggestion/', HandoffSuggestionView.as_view(), name='handoff-suggestion'),
    path('<uuid:pk>/liquidation-payment-suggestion/', LiquidationPaymentSuggestionView.as_view(), name='liquidation-payment-suggestion'),

    # ── Sprint 6: Frontend panel endpoints ──
    path('<uuid:pk>/financial-summary/', FinancialSummaryView.as_view(), name='financial-summary'),
    path('<uuid:pk>/documents/', DocumentsListView.as_view(), name='documents'),

    # S14-15: CEO Override
    path('<uuid:pk>/ceo-override/', CEOOverrideView.as_view(), name='ceo-override'),

    # ── S21: Admin — Navegación de Estado ──
    path('<uuid:pk>/admin/advance-state/', AdvanceStateView.as_view(), name='admin-advance-state'),
    path('<uuid:pk>/admin/revert-state/', RevertStateView.as_view(), name='admin-revert-state'),

    # ── S21: Admin — Política de Artefactos ──
    path('<uuid:pk>/admin/policy/add-artifact/', AddArtifactToPolicyView.as_view(), name='admin-policy-add-artifact'),
    path('<uuid:pk>/admin/policy/remove-artifact/', RemoveArtifactFromPolicyView.as_view(), name='admin-policy-remove-artifact'),

    # ── S17-04: Portal endpoints (tenant-scoped, no CEO fields) ──
    path('portal/', PortalExpedienteListView.as_view(), name='portal-list'),
    path('portal/<uuid:pk>/', PortalExpedienteDetailView.as_view(), name='portal-detail'),
    path('portal/<uuid:pk>/artifacts/', PortalExpedienteArtifactsView.as_view(), name='portal-artifacts'),

    # ── Alias /commands/ — compatibilidad con frontend Sprint 20+ ──
    path('<uuid:pk>/commands/register-oc/', CommandDispatchView.as_view(), {'cmd_id': 'C3'}, name='commands-register-oc'),
    path('<uuid:pk>/commands/register-proforma/', CommandDispatchView.as_view(), {'cmd_id': 'C2'}, name='commands-register-proforma'),
    path('<uuid:pk>/commands/decide-mode/', CommandDispatchView.as_view(), {'cmd_id': 'C4'}, name='commands-decide-mode'),
    path('<uuid:pk>/commands/confirm-sap/', CommandDispatchView.as_view(), {'cmd_id': 'C5'}, name='commands-confirm-sap'),
    path('<uuid:pk>/commands/confirm-production/', CommandDispatchView.as_view(), {'cmd_id': 'C6'}, name='commands-confirm-production'),
    path('<uuid:pk>/commands/register-shipment/', CommandDispatchView.as_view(), {'cmd_id': 'C7'}, name='commands-register-shipment'),
    path('<uuid:pk>/commands/register-freight-quote/', CommandDispatchView.as_view(), {'cmd_id': 'C8'}, name='commands-register-freight-quote'),
    path('<uuid:pk>/commands/register-customs/', CommandDispatchView.as_view(), {'cmd_id': 'C9'}, name='commands-register-customs'),
    path('<uuid:pk>/commands/approve-dispatch/', CommandDispatchView.as_view(), {'cmd_id': 'C10'}, name='commands-approve-dispatch'),
    path('<uuid:pk>/commands/confirm-departure/', CommandDispatchView.as_view(), {'cmd_id': 'C11B'}, name='commands-confirm-departure-china'),
    path('<uuid:pk>/commands/confirm-departure-mwt/', CommandDispatchView.as_view(), {'cmd_id': 'C11'}, name='commands-confirm-departure'),
    path('<uuid:pk>/commands/confirm-arrival/', CommandDispatchView.as_view(), {'cmd_id': 'C12'}, name='commands-confirm-arrival'),
    path('<uuid:pk>/commands/issue-invoice/', CommandDispatchView.as_view(), {'cmd_id': 'C13'}, name='commands-issue-invoice'),
    path('<uuid:pk>/commands/close/', CommandDispatchView.as_view(), {'cmd_id': 'C14'}, name='commands-close'),
    path('<uuid:pk>/commands/register-cost/', CommandDispatchView.as_view(), {'cmd_id': 'C15'}, name='commands-register-cost'),
    path('<uuid:pk>/commands/cancel/', CommandDispatchView.as_view(), {'cmd_id': 'C16'}, name='commands-cancel'),
    path('<uuid:pk>/commands/block/', CommandDispatchView.as_view(), {'cmd_id': 'C17'}, name='commands-block'),
    path('<uuid:pk>/commands/unblock/', CommandDispatchView.as_view(), {'cmd_id': 'C18'}, name='commands-unblock'),
    path('<uuid:pk>/commands/supersede-artifact/', CommandDispatchView.as_view(), {'cmd_id': 'C19'}, name='commands-supersede-artifact'),
    path('<uuid:pk>/commands/void-artifact/', CommandDispatchView.as_view(), {'cmd_id': 'C20'}, name='commands-void-artifact'),
    path('<uuid:pk>/commands/register-payment/', CommandDispatchView.as_view(), {'cmd_id': 'C21'}, name='commands-register-payment'),
    path('<uuid:pk>/commands/issue-commission-invoice/', CommandDispatchView.as_view(), {'cmd_id': 'C22'}, name='commands-issue-commission-invoice'),
    path('<uuid:pk>/commands/materialize-logistics/', CommandDispatchView.as_view(), {'cmd_id': 'C30'}, name='commands-materialize-logistics'),
    path('<uuid:pk>/commands/add-logistics-option/', CommandDispatchView.as_view(), {'cmd_id': 'C23'}, name='commands-add-logistics-option'),
    path('<uuid:pk>/commands/decide-logistics/', CommandDispatchView.as_view(), {'cmd_id': 'C24'}, name='commands-decide-logistics'),
    path('<uuid:pk>/commands/register-compensation/', CommandDispatchView.as_view(), {'cmd_id': 'C29'}, name='commands-register-compensation'),
    path('<uuid:pk>/commands/add-shipment-update/', CommandDispatchView.as_view(), {'cmd_id': 'C36'}, name='commands-add-shipment-update'),
    path('<uuid:pk>/commands/reopen/', CommandDispatchView.as_view(), {'cmd_id': 'REOPEN'}, name='commands-reopen'),
]
