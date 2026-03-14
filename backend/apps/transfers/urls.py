from django.urls import path
from apps.transfers import views

app_name = 'transfers'

urlpatterns = [
    # S9-P02 — Nodes (URL canónica: /api/transfers/nodes/)
    path("nodes/", views.list_nodes_view, name="nodes"),
    # Sprint 5 — Transfer CRUD
    path("", views.list_transfers_view, name="list"),
    path("create/", views.create_transfer_view, name="create"),
    path("<str:transfer_id>/approve/", views.approve_transfer_view, name="approve"),
    path("<str:transfer_id>/dispatch/", views.dispatch_transfer_view, name="dispatch"),
    path("<str:transfer_id>/receive/", views.receive_transfer_view, name="receive"),
    path("<str:transfer_id>/reconcile/", views.reconcile_transfer_view, name="reconcile"),
    path("<str:transfer_id>/cancel/", views.cancel_transfer_view, name="cancel"),
    path("<str:transfer_id>/complete-reception/", views.create_reception_artifact_view, name="complete_reception"),
    path("<str:transfer_id>/complete-preparation/", views.create_preparation_artifact_view, name="complete_preparation"),
    path("<str:transfer_id>/complete-dispatch/", views.create_dispatch_artifact_view, name="complete_dispatch"),
    path("<str:transfer_id>/approve-pricing/", views.create_pricing_approval_artifact_view, name="approve_pricing"),
    path("<str:transfer_id>/", views.get_transfer_view, name="detail"),
]
