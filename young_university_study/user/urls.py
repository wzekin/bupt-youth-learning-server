from rest_framework.routers import SimpleRouter

from .views import CollegeViewSet, LeagueBranchViewSet, PermissionViewSet, UserViewSet

router = SimpleRouter()
router.register(r"user", UserViewSet)
router.register(r"college", CollegeViewSet)
router.register(r"league_branch", LeagueBranchViewSet)
router.register(r"permission", PermissionViewSet)
urlpatterns = router.urls
