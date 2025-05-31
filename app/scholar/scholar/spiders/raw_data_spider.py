import scrapy
from asgiref.sync import sync_to_async
from dip.models import Profile
from scholar.scholar.items import ScholarItem


class RawDataSpider(scrapy.Spider):
    name = 'raw_data_spider'
    allowed_domains = ['scholar.google.com']
    start_urls = ['https://scholar.google.com']

    def __init__(self, query, year_from=None, year_to=None, profile_id=1, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.query = query
        self.year_from = year_from
        self.year_to = year_to

    def parse(self, response):
        self.logger.info(f'Query: {self.query}')
        self.logger.info(f'Year From: {self.year_from}')
        self.logger.info(f'Year To: {self.year_to}')

        # Hardcoded sample data
        item = ScholarItem()
        item['title'] = 'Sample Title'
        item['url'] = 'https://example.com/sample-url'
        item['publication_year'] = 2023

        # Directly yield the item instead of making a request
        yield item
