from django.urls import path
from .views import LoginView, LogoutView, MeView, DashboardView

app_name = 'core'

urlpatterns = [
    # Auth Endpoints
    path('auth/login/', LoginView.as_view(), name='login'),
    path('auth/logout/', LogoutView.as_view(), name='logout'),
    path('auth/me/', MeView.as_view(), name='me'),
    
    # Dashboard
    path('ui/dashboard/', DashboardView.as_view(), name='dashboard'),
]
