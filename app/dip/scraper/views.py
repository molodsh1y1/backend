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

        task_params = {
            'query': serializer.validated_data['query'],
            'year_from': serializer.validated_data.get('year_from'),
            'year_to': serializer.validated_data.get('year_to'),
            'limit': serializer.validated_data.get('limit', 100),
            'fields_of_study': serializer.validated_data.get('fields_of_study', []),
            'publication_types': serializer.validated_data.get('publication_types', []),
            'min_citation_count': serializer.validated_data.get('min_citation_count'),
            'open_access_only': serializer.validated_data.get('open_access_only', False),
            'profile_id': request.user.profile.id if hasattr(request.user, 'profile') else None
        }

        task = scrape_raw_data.delay(**task_params)

        return Response({
            "message": "Scraping task has been initiated.",
            "task_id": task.id,
            "parameters": {
                "query": task_params['query'],
                "year_range": f"{task_params['year_from'] or 'Any'} - {task_params['year_to'] or 'Any'}",
                "limit": task_params['limit'],
                "filters_applied": len([f for f in [
                    task_params['fields_of_study'],
                    task_params['publication_types'],
                    task_params['min_citation_count'],
                    task_params['open_access_only']
                ] if f])
            }
        }, status=status.HTTP_202_ACCEPTED)

    @action(detail=False, methods=['get'], url_path='filter-options')
    def get_filter_options(self, request):
        return Response(ScraperInputSerializer.get_filter_options(), status=status.HTTP_200_OK)
