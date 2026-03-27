from rest_framework.routers import DefaultRouter
from .views import SizeSystemViewSet

router = DefaultRouter()
router.register(r'size-systems', SizeSystemViewSet, basename='size-system')

urlpatterns = router.urls
