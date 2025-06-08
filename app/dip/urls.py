from django.urls import path, include
from rest_framework.routers import DefaultRouter

from dip.scraper.views import ScraperViewSet
from dip.scholar_raw_record.views import ScholarRawRecordViewSet
from dip.scraping_session.views import ScrapingSessionViewSet


router = DefaultRouter()
router.register(r'raw-scraper', ScraperViewSet, basename='scraper')
router.register(r'scholar-raw-record', ScholarRawRecordViewSet, basename='scholar-raw-record')
router.register(r'scraping-session', ScrapingSessionViewSet, basename='scraping-session')


urlpatterns = router.urls
