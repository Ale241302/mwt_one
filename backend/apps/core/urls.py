from django.urls import path
from .views import LoginView, LogoutView, MeView, list_legal_entities, HealthView

app_name = 'core'

urlpatterns = [
    path('health/', HealthView.as_view(), name='health'),
    path('auth/login/', LoginView.as_view(), name='login'),
    path('auth/logout/', LogoutView.as_view(), name='logout'),
    path('auth/me/', MeView.as_view(), name='me'),
    path('legal-entities/', list_legal_entities, name='legal-entities'),
]
