import logging

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from scrapy.crawler import CrawlerProcess
from scrapy.settings import Settings
from scholar.scholar import settings as project_settings
from scholar.scholar.spiders.raw_data_spider import RawDataSpider

custom_settings = Settings()
custom_settings.setmodule(project_settings)

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Scrape raw data from the specified query and year range.'

    def add_arguments(self, parser):
        parser.add_argument('--query', type=str, default=None, help='The query to scrape data for.')
        parser.add_argument('--year_from', type=int, default=None, help='Start year for the data range.')
        parser.add_argument('--year_to', type=int, default=None, help='End year for the data range.')

    def handle(self, *args, **options):
        query = options.get('query')
        year_from = options.get('year_from')
        year_to = options.get('year_to')

        logger.info(f'Starting to scrape data for query: {query}, from {year_from} to {year_to}')
        process = CrawlerProcess(custom_settings)
        process.crawl(RawDataSpider, query=query, year_from=year_from, year_to=year_to)
        process.start()
        logger.info('Scraping completed successfully.')
