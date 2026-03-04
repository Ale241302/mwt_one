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
    path("<str:transfer_id>/", views.get_transfer_view, name="detail"),
]
