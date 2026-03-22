from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import InventoryEntryViewSet

router = DefaultRouter()
router.register('', InventoryEntryViewSet, basename='inventory')

urlpatterns = [
    path('', include(router.urls)),
]
