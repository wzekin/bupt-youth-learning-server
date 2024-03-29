from rest_framework.routers import SimpleRouter

from .views import StudyPeriodViewSet, StudyRecordingViewSet

router = SimpleRouter()
router.register(r"study_period", StudyPeriodViewSet)
router.register(r"study_recording", StudyRecordingViewSet)
urlpatterns = router.urls
