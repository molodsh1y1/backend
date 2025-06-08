from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from dip.models import ScrapingSession
from .serializers import ScrapingSessionSerializer


class ScrapingSessionViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ScrapingSessionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return ScrapingSession.objects.filter(
            profile=self.request.user.profile,
            status='SUCCESS'
        ).order_by('-completed_at')
