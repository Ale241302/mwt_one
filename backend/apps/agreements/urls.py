from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CreditOverrideViewSet

router = DefaultRouter()
router.register(r'credit-override', CreditOverrideViewSet, basename='credit-override')

urlpatterns = [
    path('', include(router.urls)),
    path('credit-status/', CreditOverrideViewSet.as_view({'get': 'credit_status'}), name='credit-status'),
]
