from django.urls import path
from apps.clientes import views

urlpatterns = [
    path('', views.clientes_list_create, name='clientes-list'),
    path('<int:pk>/', views.clientes_detail, name='clientes-detail'),
    path('<int:pk>/credit-actions/freeze/', views.cliente_freeze_credit, name='cliente-freeze'),
    path('<int:pk>/credit-policy/', views.cliente_credit_policy, name='cliente-policy'),
]
