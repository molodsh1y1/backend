from rest_framework import serializers

from dip.models import ScholarRawRecord


class ScholarRawRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScholarRawRecord
        fields = '__all__'
