from django.urls import path
from apps.transfers import views

app_name = 'transfers'

urlpatterns = [
    path("", views.list_transfers_view, name="list"),
    path("create/", views.create_transfer_view, name="create"),
    path("<str:transfer_id>/approve/", views.approve_transfer_view, name="approve"),
    path("<str:transfer_id>/dispatch/", views.dispatch_transfer_view, name="dispatch"),
    path("<str:transfer_id>/receive/", views.receive_transfer_view, name="receive"),
    path("<str:transfer_id>/reconcile/", views.reconcile_transfer_view, name="reconcile"),
    path("<str:transfer_id>/cancel/", views.cancel_transfer_view, name="cancel"),
    path("<str:transfer_id>/preparation-artifact/", views.create_preparation_artifact_view, name="create_preparation_artifact"),
    path("<str:transfer_id>/dispatch-artifact/", views.create_dispatch_artifact_view, name="create_dispatch_artifact"),
    path("<str:transfer_id>/reception-artifact/", views.create_reception_artifact_view, name="create_reception_artifact"),
    path("<str:transfer_id>/pricing-artifact/", views.create_pricing_approval_artifact_view, name="create_pricing_approval_artifact"),
    path("<str:transfer_id>/", views.get_transfer_view, name="detail"),
]
