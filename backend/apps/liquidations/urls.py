from django.urls import path
from apps.liquidations import views

app_name = 'liquidations'

urlpatterns = [
    # S9-P01 — Preview Excel sin persistir
    path("preview/", views.preview_liquidation_view, name="preview"),
    # Sprint 5 — endpoints existentes
    path("", views.list_liquidations_view, name="list"),
    path("upload/", views.upload_liquidation_view, name="upload"),
    path("<str:liquidation_id>/", views.get_liquidation_view, name="detail"),
    path("<str:liquidation_id>/lines/", views.get_liquidation_lines_view, name="lines"),
    path("<str:liquidation_id>/match-line/", views.manual_match_line_view, name="match-line"),
]
