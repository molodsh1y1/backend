from dip.exceptions import CustomErrorSerializerMixin
from rest_framework import serializers


class ScraperInputSerializer(CustomErrorSerializerMixin, serializers.Serializer):
    VALID_FIELDS_OF_STUDY = [
        'Computer Science', 'Medicine', 'Chemistry', 'Biology', 'Materials Science',
        'Physics', 'Geology', 'Psychology', 'Art', 'History', 'Geography',
        'Sociology', 'Business', 'Political Science', 'Economics', 'Philosophy',
        'Mathematics', 'Engineering', 'Environmental Science', 'Agricultural and Food Sciences',
        'Education', 'Law', 'Linguistics'
    ]

    VALID_PUBLICATION_TYPES = [
        'JournalArticle', 'Conference', 'Review', 'Book', 'BookSection', 'Dataset'
    ]

    query = serializers.CharField(
        required=True,
        max_length=500,
        help_text="Search query for papers (max 10 words)"
    )

    year_from = serializers.IntegerField(
        required=False,
        allow_null=True,
        min_value=1900,
        max_value=2099,
        help_text="Start year for publication date filter"
    )

    year_to = serializers.IntegerField(
        required=False,
        allow_null=True,
        min_value=1900,
        max_value=2099,
        help_text="End year for publication date filter"
    )

    limit = serializers.IntegerField(
        required=False,
        allow_null=True,
        min_value=1,
        max_value=1000,
        default=100,
        help_text="Maximum number of results to return (1-1000)"
    )

    fields_of_study = serializers.ListField(
        child=serializers.CharField(max_length=100),
        required=False,
        allow_empty=True,
        help_text=f"List of scientific fields. Valid options: {', '.join(VALID_FIELDS_OF_STUDY)}"
    )

    publication_types = serializers.ListField(
        child=serializers.CharField(max_length=50),
        required=False,
        allow_empty=True,
        help_text=f"List of publication types. Valid options: {', '.join(VALID_PUBLICATION_TYPES)}"
    )

    min_citation_count = serializers.IntegerField(
        required=False,
        allow_null=True,
        min_value=0,
        help_text="Minimum number of citations required"
    )

    open_access_only = serializers.BooleanField(
        required=False,
        default=False,
        help_text="Filter for open access papers only"
    )

    def validate_query(self, value):
        if len(value.strip()) < 3:
            raise serializers.ValidationError("Query must be at least 3 characters long.")

        word_count = len(value.split())
        if word_count > 10:
            raise serializers.ValidationError("Query cannot contain more than 10 words.")

        return value.strip()

    def validate_fields_of_study(self, value):
        if not value:
            return value

        invalid_fields = [field for field in value if field not in self.VALID_FIELDS_OF_STUDY]
        if invalid_fields:
            raise serializers.ValidationError(
                f"Invalid fields of study: {invalid_fields}. "
                f"Valid options: {self.VALID_FIELDS_OF_STUDY}"
            )

        return list(set(value))

    def validate_publication_types(self, value):
        if not value:
            return value

        invalid_types = [ptype for ptype in value if ptype not in self.VALID_PUBLICATION_TYPES]
        if invalid_types:
            raise serializers.ValidationError(
                f"Invalid publication types: {invalid_types}. "
                f"Valid options: {self.VALID_PUBLICATION_TYPES}"
            )

        return list(set(value))

    def validate(self, data):
        year_from = data.get('year_from')
        year_to = data.get('year_to')

        if year_from and year_to:
            if year_from > year_to:
                raise serializers.ValidationError({
                    'year_from': "Start year cannot be greater than end year."
                })

        limit = data.get('limit', 100)
        min_citations = data.get('min_citation_count')

        if min_citations and min_citations > 100 and limit > 100:
            pass

        return data

    @classmethod
    def get_filter_options(cls):
        return {
            'fields_of_study': cls.VALID_FIELDS_OF_STUDY,
            'publication_types': cls.VALID_PUBLICATION_TYPES,
            'year_range': {
                'min': 1900,
                'max': 2099
            },
            'limit_range': {
                'min': 1,
                'max': 1000,
                'default': 100
            }
        }
