from django.urls import path
from apps.liquidations import views

app_name = 'liquidations'

urlpatterns = [
    path("", views.list_liquidations_view, name="list"),
    path("upload/", views.upload_liquidation_view, name="upload"),
    path("<str:liquidation_id>/", views.get_liquidation_view, name="detail"),
    path("<str:liquidation_id>/lines/", views.get_liquidation_lines_view, name="lines"),
    path("<str:liquidation_id>/match-line/", views.manual_match_line_view, name="match-line"),
    path("<str:liquidation_id>/reconcile/", views.reconcile_liquidation_view, name="reconcile"),
    path("<str:liquidation_id>/dispute/", views.dispute_liquidation_view, name="dispute"),
]
