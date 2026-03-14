from django.urls import path
from .views import LoginView, LogoutView, MeView
from .views_clients import ClientListCreateView, ClientDetailView

app_name = 'core'

urlpatterns = [
    # Auth Endpoints
    path('auth/login/',  LoginView.as_view(),  name='login'),
    path('auth/logout/', LogoutView.as_view(), name='logout'),
    path('auth/me/',     MeView.as_view(),     name='me'),
    # S9-P03 — Clientes CRUD (LegalEntity)
    path('clients/',              ClientListCreateView.as_view(), name='client-list'),
    path('clients/<int:client_id>/', ClientDetailView.as_view(),  name='client-detail'),
]
