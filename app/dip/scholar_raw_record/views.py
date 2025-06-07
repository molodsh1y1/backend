from rest_framework.pagination import PageNumberPagination
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from dip.scholar_raw_record.serializers import ScholarRawRecordSerializer
from dip.models import ScholarRawRecord, ScholarAuthor
from django.db.models import Q


class ScholarRawRecordPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


class ScholarRawRecordViewSet(viewsets.ModelViewSet):
    serializer_class = ScholarRawRecordSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = ScholarRawRecordPagination

    def get_queryset(self):
        return ScholarRawRecord.objects.filter(profile=self.request.profile)

    @action(detail=False, methods=['get'], url_path='results/export-csv')
    def export_results_csv(self, request):
        """Export scraping results to CSV for analysts"""
        import csv
        from django.http import HttpResponse
        from datetime import datetime

        profile = request.profile

        queryset = ScholarRawRecord.objects.filter(profile=profile).select_related('profile').prefetch_related('authors')

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

        # Limit results for performance
        limit = request.query_params.get('limit', 10000)
        try:
            limit = min(int(limit), 50000)  # Max 50k records
        except ValueError:
            limit = 10000

        queryset = queryset.order_by('-scraped_at')[:limit]

        # Create CSV response
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = f'attachment; filename="scholar_papers_{timestamp}.csv"'

        response.write('\ufeff')

        writer = csv.writer(response)

        # Write headers
        headers = [
            'ID', 'Semantic Scholar ID', 'Title', 'Abstract', 'Publication Year', 'Venue',
            'DOI', 'URL', 'PDF URL', 'Citation Count', 'Reference Count',
            'Influential Citation Count', 'Open Access', 'Authors', 'Author Count',
            'Scraped Date', 'Updated Date'
        ]
        writer.writerow(headers)

        # Write data rows
        for paper in queryset:
            authors_list = [author.full_name for author in paper.authors.all()]
            authors_str = "; ".join(authors_list)

            writer.writerow([
                paper.id,
                paper.semantic_scholar_id,
                paper.title,
                paper.abstract,
                paper.publication_year,
                paper.venue,
                paper.doi,
                paper.url,
                paper.pdf_url,
                paper.citation_count,
                paper.reference_count,
                paper.influential_citation_count,
                'Yes' if paper.is_open_access else 'No',
                authors_str,
                len(authors_list),
                paper.scraped_at.strftime('%Y-%m-%d %H:%M:%S'),
                paper.updated_at.strftime('%Y-%m-%d %H:%M:%S')
            ])

        return response

    @action(detail=False, methods=['get'], url_path='results/export-excel')
    def export_results_excel(self, request):
        """Export scraping results to Excel for analysts"""
        try:
            import openpyxl
            from openpyxl.styles import Font, PatternFill
        except ImportError:
            return Response({
                "error": "Excel export requires openpyxl library. Please install it."
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        from django.http import HttpResponse
        from datetime import datetime
        import io

        profile = request.profile

        # Get filtered queryset (same logic as CSV)
        queryset = ScholarRawRecord.objects.filter(profile=profile).select_related('profile').prefetch_related(
            'authors')

        # Apply filters (same as CSV)
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

        limit = request.query_params.get('limit', 10000)
        try:
            limit = min(int(limit), 50000)
        except ValueError:
            limit = 10000

        queryset = queryset.order_by('-scraped_at')[:limit]

        # Create Excel workbook
        wb = openpyxl.Workbook()

        # Papers sheet
        ws_papers = wb.active
        ws_papers.title = "Papers"

        # Headers with styling
        headers = [
            'ID', 'Semantic Scholar ID', 'Title', 'Abstract', 'Publication Year', 'Venue',
            'DOI', 'URL', 'PDF URL', 'Citation Count', 'Reference Count',
            'Influential Citation Count', 'Open Access', 'Authors', 'Author Count',
            'Scraped Date', 'Updated Date'
        ]

        # Style headers
        header_font = Font(bold=True, color="FFFFFF")
        header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")

        for col, header in enumerate(headers, 1):
            cell = ws_papers.cell(row=1, column=col, value=header)
            cell.font = header_font
            cell.fill = header_fill

        for row, paper in enumerate(queryset, 2):
            authors_list = [author.full_name for author in paper.authors.all()]
            authors_str = "; ".join(authors_list)

            # Convert timezone-aware datetimes to naive datetimes for Excel
            scraped_at_naive = paper.scraped_at.replace(tzinfo=None) if paper.scraped_at else None
            updated_at_naive = paper.updated_at.replace(tzinfo=None) if paper.updated_at else None

            data = [
                paper.id,
                paper.semantic_scholar_id,
                paper.title,
                paper.abstract,
                paper.publication_year,
                paper.venue,
                paper.doi,
                paper.url,
                paper.pdf_url,
                paper.citation_count,
                paper.reference_count,
                paper.influential_citation_count,
                'Yes' if paper.is_open_access else 'No',
                authors_str,
                len(authors_list),
                scraped_at_naive,
                updated_at_naive
            ]

            for col, value in enumerate(data, 1):
                ws_papers.cell(row=row, column=col, value=value)

        # Auto-adjust column widths
        for column in ws_papers.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max_length + 2, 50)  # Max width 50
            ws_papers.column_dimensions[column_letter].width = adjusted_width

        # Authors summary sheet
        ws_authors = wb.create_sheet("Authors Summary")

        # Get author statistics
        from django.db.models import Count
        author_stats = ScholarAuthor.objects.filter(
            scholar_raw_records__profile=profile
        ).annotate(
            papers_count=Count('scholar_raw_records', distinct=True)
        ).order_by('-papers_count')[:100]  # Top 100 authors

        # Authors headers
        author_headers = ['Author Name', 'Papers Count', 'H-Index', 'Total Citations', 'Affiliations']
        for col, header in enumerate(author_headers, 1):
            cell = ws_authors.cell(row=1, column=col, value=header)
            cell.font = header_font
            cell.fill = header_fill

        # Authors data
        for row, author in enumerate(author_stats, 2):
            affiliations_str = "; ".join(author.affiliations) if author.affiliations else ""
            data = [
                author.full_name,
                author.papers_count,
                author.h_index,
                author.citation_count,
                affiliations_str
            ]

            for col, value in enumerate(data, 1):
                ws_authors.cell(row=row, column=col, value=value)

        # Save to BytesIO
        excel_buffer = io.BytesIO()
        wb.save(excel_buffer)
        excel_buffer.seek(0)

        # Create response
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        response = HttpResponse(
            excel_buffer.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="scholar_analysis_{timestamp}.xlsx"'

        return response

    @action(detail=False, methods=['get'], url_path='results/export-authors-csv')
    def export_authors_csv(self, request):
        """Export authors data to CSV for analysts"""
        import csv
        from django.http import HttpResponse
        from datetime import datetime

        profile = request.profile

        # Get authors related to user's papers
        authors = ScholarAuthor.objects.filter(
            scholar_raw_records__profile=profile
        ).distinct().prefetch_related('scholar_raw_records')

        # Create CSV response
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = f'attachment; filename="scholar_authors_{timestamp}.csv"'

        response.write('\ufeff')  # BOM

        writer = csv.writer(response)

        # Headers
        headers = [
            'ID', 'Semantic Scholar ID', 'Full Name', 'URL', 'H-Index',
            'Paper Count', 'Citation Count', 'Affiliations', 'Papers in Dataset',
            'Created Date', 'Updated Date'
        ]
        writer.writerow(headers)

        # Data
        for author in authors:
            papers_in_dataset = author.scholar_raw_records.filter(profile=profile).count()
            affiliations_str = "; ".join(author.affiliations) if author.affiliations else ""

            writer.writerow([
                author.id,
                author.semantic_scholar_id,
                author.full_name,
                author.url,
                author.h_index,
                author.paper_count,
                author.citation_count,
                affiliations_str,
                papers_in_dataset,
                author.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                author.updated_at.strftime('%Y-%m-%d %H:%M:%S')
            ])

        return response
