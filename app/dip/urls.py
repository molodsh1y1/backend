from django.urls import path, include
from rest_framework.routers import DefaultRouter

from dip.scraper.views import ScraperViewSet

router = DefaultRouter()
router.register(r'raw-scraper', ScraperViewSet, basename='scraper')


urlpatterns = router.urls
