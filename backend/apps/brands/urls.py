from django.urls import path
from .views import BrandListView

urlpatterns = [
    path('', BrandListView.as_view(), name='brand-list'),
]
