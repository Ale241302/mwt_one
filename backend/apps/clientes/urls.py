from django.urls import path
from apps.clientes import views

urlpatterns = [
    path('', views.clientes_list_create, name='clientes-list'),
    path('<int:pk>/', views.clientes_detail, name='clientes-detail'),
]
