from django.urls import path
from .views import DashboardView
from apps.expedientes.views import FinancialDashboardView

app_name = 'core-ui'

urlpatterns = [
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
    path('dashboard/financial/', FinancialDashboardView.as_view(), name='financial-dashboard'),
]
