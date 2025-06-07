from rest_framework.pagination import PageNumberPagination
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from dip.scholar_raw_record.serializers import ScholarRawRecordSerializer
from dip.models import ScholarRawRecord
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
