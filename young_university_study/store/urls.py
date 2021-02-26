from rest_framework.routers import SimpleRouter

from .views import CommodityViewSet, PurchaseViewSet

router = SimpleRouter()
router.register(r"commodity", CommodityViewSet)
router.register(r"purchase", PurchaseViewSet)
urlpatterns = router.urls
