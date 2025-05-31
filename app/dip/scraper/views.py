from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from .serializers import ScraperInputSerializer
from ..tasks import scrape_raw_data


class ScraperViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['post'], url_path='scrape')
    def scrape(self, request):
        serializer = ScraperInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        scrape_raw_data.delay(
            query=serializer.validated_data['query'],
            year_from=serializer.validated_data.get('year_from'),
            year_to=serializer.validated_data.get('year_to')
        )
        return Response({"message": "Scraping task has been initiated."}, status=status.HTTP_202_ACCEPTED)
