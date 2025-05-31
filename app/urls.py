import logging

from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from core.views import start, error, static
from core.auth.views import AuthViewSet
import settings


logger = logging.getLogger(__name__)

router = DefaultRouter()
router.register(r'auth', AuthViewSet, basename='auth')

urlpatterns = [
    path('', start),
    path('error/', error),
    path('admin/', admin.site.urls),
    static(settings.STATIC_URL, document_root=settings.STATIC_ROOT),

    path('o/', include('oauth2_provider.urls', namespace='oauth2_provider')),
    path('api/v1/core/', include(router.urls)),
    # path('api/v1/', include('dip.urls')),
]
