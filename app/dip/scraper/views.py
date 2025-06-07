from django.utils import timezone
from datetime import timedelta
from django.db import models
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from django.db.models import Q, Count, Avg
from dip.models import ScholarRawRecord, ScholarAuthor
from .serializers import ScraperInputSerializer
from .result_serializers import ScholarRawRecordSerializer, ScholarAuthorSerializer
from ..tasks import scrape_raw_data


class ResultsPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class ScraperViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]
    pagination_class = ResultsPagination

    @action(detail=False, methods=['post'], url_path='scrape')
    def scrape(self, request):
        """Start scraping task"""
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
        """Get available filter options"""
        return Response(ScraperInputSerializer.get_filter_options(), status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], url_path='results')
    def get_results(self, request):
        """Get user's scraping results with pagination and filtering"""
        # Base queryset for user's papers
        queryset = ScholarRawRecord.objects.filter(
            profile=request.user.profile if hasattr(request.user, 'profile') else None
        ).select_related('profile').prefetch_related('authors')

        # Apply filters from query parameters
        query = request.query_params.get('query')
        if query:
            queryset = queryset.filter(
                Q(title__icontains=query) | Q(abstract__icontains=query)
            )

        year_from = request.query_params.get('year_from')
        if year_from:
            try:
                queryset = queryset.filter(publication_year__gte=int(year_from))
            except ValueError:
                pass

        year_to = request.query_params.get('year_to')
        if year_to:
            try:
                queryset = queryset.filter(publication_year__lte=int(year_to))
            except ValueError:
                pass

        venue = request.query_params.get('venue')
        if venue:
            queryset = queryset.filter(venue__icontains=venue)

        min_citations = request.query_params.get('min_citations')
        if min_citations:
            try:
                queryset = queryset.filter(citation_count__gte=int(min_citations))
            except ValueError:
                pass

        open_access = request.query_params.get('open_access')
        if open_access and open_access.lower() == 'true':
            queryset = queryset.filter(is_open_access=True)

        # Sorting
        sort_by = request.query_params.get('sort_by', '-scraped_at')
        valid_sort_fields = [
            'publication_year', '-publication_year',
            'citation_count', '-citation_count',
            'title', '-title',
            'scraped_at', '-scraped_at'
        ]
        if sort_by in valid_sort_fields:
            queryset = queryset.order_by(sort_by)

        # Pagination
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(queryset, request)

        if page is not None:
            serializer = ScholarRawRecordSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)

        serializer = ScholarRawRecordSerializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='stats')
    def get_stats(self, request):
        """Get statistical analysis of user's scraped data"""
        profile = request.user.profile if hasattr(request.user, 'profile') else None

        # Base queryset
        papers = ScholarRawRecord.objects.filter(profile=profile)

        if not papers.exists():
            return Response({
                "message": "No data available. Start scraping to see statistics.",
                "total_papers": 0
            })

        # Basic counts
        total_papers = papers.count()
        total_authors = ScholarAuthor.objects.filter(
            scholar_raw_records__profile=profile
        ).distinct().count()

        # Papers by year
        papers_by_year = papers.values('publication_year').annotate(
            count=Count('id')
        ).order_by('publication_year')

        papers_by_year_dict = {
            str(item['publication_year']): item['count']
            for item in papers_by_year
            if item['publication_year']
        }

        # Top venues
        top_venues = papers.values('venue').annotate(
            count=Count('id')
        ).filter(venue__isnull=False, venue__gt='').order_by('-count')[:10]

        # Citation statistics
        citation_stats = papers.aggregate(
            total_citations=models.Sum('citation_count'),
            avg_citations=Avg('citation_count'),
            max_citations=models.Max('citation_count')
        )

        # Open access statistics
        open_access_count = papers.filter(is_open_access=True).count()
        open_access_percentage = (open_access_count / total_papers * 100) if total_papers > 0 else 0

        # Recent activity
        recent_papers = papers.filter(
            scraped_at__gte=timezone.now() - timedelta(days=30)
        ).count()

        # Top cited papers
        top_cited = papers.order_by('-citation_count')[:5]
        top_cited_data = ScholarRawRecordSerializer(top_cited, many=True).data

        return Response({
            "total_papers": total_papers,
            "total_authors": total_authors,
            "papers_by_year": papers_by_year_dict,
            "top_venues": [
                {"venue": item['venue'], "count": item['count']}
                for item in top_venues
            ],
            "citation_stats": {
                "total_citations": citation_stats['total_citations'] or 0,
                "average_citations": round(citation_stats['avg_citations'] or 0, 2),
                "max_citations": citation_stats['max_citations'] or 0
            },
            "open_access": {
                "count": open_access_count,
                "percentage": round(open_access_percentage, 1)
            },
            "recent_activity": {
                "papers_last_30_days": recent_papers
            },
            "top_cited_papers": top_cited_data
        })

    @action(detail=False, methods=['delete'], url_path='results/clear')
    def clear_results(self, request):
        """Clear all scraping results for the user"""
        profile = request.user.profile if hasattr(request.user, 'profile') else None

        deleted_count, _ = ScholarRawRecord.objects.filter(profile=profile).delete()

        return Response({
            "message": "All scraping results cleared successfully",
            "deleted_count": deleted_count
        }, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], url_path='results/export')
    def export_results(self, request):
        """Export results to CSV format"""
        import csv
        from django.http import HttpResponse

        profile = request.user.profile if hasattr(request.user, 'profile') else None
        papers = ScholarRawRecord.objects.filter(profile=profile).order_by('-scraped_at')

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="scholar_papers.csv"'

        writer = csv.writer(response)
        writer.writerow([
            'Title', 'Authors', 'Year', 'Venue', 'Citation Count',
            'DOI', 'Open Access', 'URL', 'Scraped Date'
        ])

        for paper in papers:
            authors = ", ".join([author.full_name for author in paper.authors.all()])
            writer.writerow([
                paper.title,
                authors,
                paper.publication_year,
                paper.venue,
                paper.citation_count,
                paper.doi,
                'Yes' if paper.is_open_access else 'No',
                paper.url,
                paper.scraped_at.strftime('%Y-%m-%d %H:%M:%S')
            ])

        return response
