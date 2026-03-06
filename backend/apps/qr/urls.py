from django.urls import path
from apps.qr import views

app_name = 'qr'

urlpatterns = [
    path("<str:slug>/", views.public_qr_redirect_view, name="qr_redirect"),
]
