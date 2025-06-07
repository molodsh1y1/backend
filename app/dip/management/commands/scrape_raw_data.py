# dip/management/commands/scrape_raw_data.py - оновлена версія
import logging
import json

from django.core.management.base import BaseCommand
from scrapy.crawler import CrawlerProcess
from scrapy.settings import Settings
from scholar.scholar import settings as project_settings
from scholar.scholar.spiders.raw_data_spider import RawDataSpider

custom_settings = Settings()
custom_settings.setmodule(project_settings)

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Scrape raw data from Semantic Scholar API with specified parameters.'

    def add_arguments(self, parser):
        parser.add_argument('--query', type=str, required=True, help='The search query')
        parser.add_argument('--year_from', type=int, help='Start year for publications')
        parser.add_argument('--year_to', type=int, help='End year for publications')
        parser.add_argument('--limit', type=int, default=100, help='Maximum number of results')
        parser.add_argument('--profile_id', type=int, help='Profile ID to associate results with')
        parser.add_argument('--session_id', type=int, help='Session ID to associate results with')

        parser.add_argument('--fields_of_study', type=str, help='JSON list of fields of study')
        parser.add_argument('--publication_types', type=str, help='JSON list of publication types')
        parser.add_argument('--min_citation_count', type=int, help='Minimum citation count filter')
        parser.add_argument('--open_access_only', action='store_true', help='Only open access papers')

    def handle(self, *args, **options):
        query = options['query']
        year_from = options.get('year_from')
        year_to = options.get('year_to')
        limit = options.get('limit', 100)
        profile_id = options.get('profile_id')
        session_id = options.get('session_id')

        fields_of_study = []
        if options.get('fields_of_study'):
            try:
                fields_of_study = json.loads(options['fields_of_study'])
            except json.JSONDecodeError:
                logger.error("Invalid JSON for fields_of_study")
                return

        publication_types = []
        if options.get('publication_types'):
            try:
                publication_types = json.loads(options['publication_types'])
            except json.JSONDecodeError:
                logger.error("Invalid JSON for publication_types")
                return

        min_citation_count = options.get('min_citation_count')
        open_access_only = options.get('open_access_only', False)

        logger.info(f'Starting Semantic Scholar scraping:')
        logger.info(f'  Query: {query}')
        logger.info(f'  Year range: {year_from} - {year_to}')
        logger.info(f'  Limit: {limit}')
        logger.info(f'  Fields: {fields_of_study}')
        logger.info(f'  Publication types: {publication_types}')
        logger.info(f'  Min citations: {min_citation_count}')
        logger.info(f'  Open access only: {open_access_only}')
        logger.info(f'  Profile ID: {profile_id}')
        logger.info(f'  Session ID: {session_id}')

        process = CrawlerProcess(custom_settings)
        process.crawl(
            RawDataSpider,
            query=query,
            year_from=year_from,
            year_to=year_to,
            limit=limit,
            profile_id=profile_id,
            session_id=session_id,
            fields_of_study=fields_of_study,
            publication_types=publication_types,
            min_citation_count=min_citation_count,
            open_access_only=open_access_only
        )
        process.start()

        logger.info('Semantic Scholar scraping completed successfully.')
