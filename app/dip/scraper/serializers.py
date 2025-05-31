from rest_framework import serializers
from dip.exceptions import CustomErrorSerializerMixin

class ScraperInputSerializer(CustomErrorSerializerMixin, serializers.Serializer):
    query = serializers.CharField(required=True)
    year_from = serializers.IntegerField(required=False, allow_null=True, min_value=100, max_value=2099)
    year_to = serializers.IntegerField(required=False, allow_null=True, min_value=100, max_value=2099)

    def validate(self, data):
        if data.get('year_from') and data.get('year_to'):
            if data['year_from'] > data['year_to']:
                raise serializers.ValidationError("year_from cannot be greater than year_to.")

        if data.get('year_from') and data['year_from'] < 100:
            raise serializers.ValidationError("year_from must be at least 100.")

        if data.get('year_to') and data['year_to'] > 2099:
            raise serializers.ValidationError("year_to cannot be greater than 2099.")

        if data.get('query') and len(data['query'].split()) >= 5:
            raise serializers.ValidationError("Query cannot be longer than 5 characters.")

        return data
