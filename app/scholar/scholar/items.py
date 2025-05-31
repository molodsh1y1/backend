import scrapy
from scrapy_djangoitem import DjangoItem
from dip.models import ScholarRawRecord

class ScholarItem(DjangoItem):
    django_model = ScholarRawRecord
