from django.urls import path, include
from rest_framework.routers import DefaultRouter

from dip.scraper.views import ScraperViewSet
from dip.scholar_raw_record.views import ScholarRawRecordViewSet

router = DefaultRouter()
router.register(r'raw-scraper', ScraperViewSet, basename='scraper')
router.register(r'scholar-raw-record', ScholarRawRecordViewSet, basename='scholar-raw-record')


urlpatterns = router.urls
