import subprocess
import logging
from celery import shared_task

logger = logging.getLogger(__name__)

@shared_task
def scrape_raw_data(query=None, year_from=None, year_to=None):
    logger.info(f"Запускаємо Scrapy з query={query}, year_from={year_from}, year_to={year_to}")

    cmd = ['python', 'manage.py', 'scrape_raw_data']

    if query:
        cmd += ['--query', query]
    if year_from:
        cmd += ['--year_from', str(year_from)]
    if year_to:
        cmd += ['--year_to', str(year_to)]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        logger.info(f"[Scrapy STDOUT]\n{result.stdout}")
        logger.info(f"[Scrapy STDERR]\n{result.stderr}")
    except subprocess.CalledProcessError as e:
        logger.error(f"Scrapy завершився з помилкою: {e.returncode}")
        logger.error(f"STDOUT:\n{e.stdout}")
        logger.error(f"STDERR:\n{e.stderr}")
