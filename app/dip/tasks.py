import logging

from celery import shared_task
from django.core.management import call_command
from django.conf import settings
from django.db import transaction

logger = logging.getLogger(__name__)


@shared_task
def scrape_raw_data(query=None, year_from=None, year_to=None):
    logger.info(f"Task started with query={query}, year_from={year_from}, year_to={year_to}")

    cmd_args = {}
    if query:
        cmd_args['query'] = query
    if year_from:
        cmd_args['year_from'] = year_from
    if year_to:
        cmd_args['year_to'] = year_to

    call_command('scrape_raw_data', **cmd_args)
