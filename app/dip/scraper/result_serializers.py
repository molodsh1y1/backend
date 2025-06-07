from rest_framework import serializers

from dip.models import ScholarAuthor, ScholarRawRecord

class ScholarAuthorSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScholarAuthor
        fields = ['id', 'semantic_scholar_id', 'full_name', 'url', 'h_index',
                  'paper_count', 'citation_count', 'affiliations']


class ScholarRawRecordSerializer(serializers.ModelSerializer):
    authors = ScholarAuthorSerializer(many=True, read_only=True)

    class Meta:
        model = ScholarRawRecord
        fields = ['id', 'semantic_scholar_id', 'title', 'abstract', 'publication_year',
                  'venue', 'doi', 'url', 'pdf_url', 'citation_count', 'reference_count',
                  'influential_citation_count', 'is_open_access', 'authors', 'scraped_at']
