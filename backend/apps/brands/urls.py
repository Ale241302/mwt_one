from django.urls import path
from .views import brand_list_create, brand_detail

urlpatterns = [
    path('', brand_list_create, name='brand-list-create'),
    path('<str:slug>/', brand_detail, name='brand-detail'),
]
