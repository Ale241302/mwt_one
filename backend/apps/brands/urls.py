from django.urls import path
from .views import brand_list_create, brand_detail, brand_pricelists

urlpatterns = [
    path('', brand_list_create, name='brand-list-create'),
    path('<str:slug>/', brand_detail, name='brand-detail'),
    path('<str:slug>/pricelists/', brand_pricelists, name='brand-pricelists'),
]
