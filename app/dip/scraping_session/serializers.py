from rest_framework import serializers
from dip.models import ScrapingSession


class ScrapingSessionSerializer(serializers.ModelSerializer):
    title = serializers.SerializerMethodField()

    class Meta:
        model = ScrapingSession
        fields = '__all__'

    def get_title(self, obj):
        query_words = obj.query.split()[:3]
        base_title = " ".join(query_words).title()

        if obj.year_from and obj.year_to:
            year_info = f"({obj.year_from}-{obj.year_to})"
        elif obj.year_from:
            year_info = f"(від {obj.year_from})"
        elif obj.year_to:
            year_info = f"(до {obj.year_to})"
        else:
            year_info = ""

        if obj.fields_of_study:
            if len(obj.fields_of_study) == 1:
                field_info = f"в {obj.fields_of_study[0]}"
            else:
                field_info = f"в {len(obj.fields_of_study)} галузях"
        else:
            field_info = ""

        title_parts = [base_title]
        if field_info:
            title_parts.append(field_info)
        if year_info:
            title_parts.append(year_info)

        if obj.status != 'SUCCESS':
            title_parts.append(f"[{obj.status}]")

        return " ".join(title_parts)
