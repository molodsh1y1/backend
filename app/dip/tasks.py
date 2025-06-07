import subprocess
import logging
import json
from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task
def scrape_raw_data(query=None, year_from=None, year_to=None, limit=100,
                    fields_of_study=None, publication_types=None,
                    min_citation_count=None, open_access_only=False, profile_id=None):
    logger.info(f"Запускаємо Scrapy з параметрами:")
    logger.info(f"  query={query}")
    logger.info(f"  year_from={year_from}, year_to={year_to}")
    logger.info(f"  limit={limit}")
    logger.info(f"  fields_of_study={fields_of_study}")
    logger.info(f"  publication_types={publication_types}")
    logger.info(f"  min_citation_count={min_citation_count}")
    logger.info(f"  open_access_only={open_access_only}")
    logger.info(f"  profile_id={profile_id}")

    cmd = ['python', 'manage.py', 'scrape_raw_data']

    # Основні параметри
    if query:
        cmd += ['--query', query]
    if year_from:
        cmd += ['--year_from', str(year_from)]
    if year_to:
        cmd += ['--year_to', str(year_to)]
    if limit:
        cmd += ['--limit', str(limit)]
    if profile_id:
        cmd += ['--profile_id', str(profile_id)]

    # Додаткові параметри (передаємо як JSON)
    if fields_of_study:
        cmd += ['--fields_of_study', json.dumps(fields_of_study)]
    if publication_types:
        cmd += ['--publication_types', json.dumps(publication_types)]
    if min_citation_count is not None:
        cmd += ['--min_citation_count', str(min_citation_count)]
    if open_access_only:
        cmd += ['--open_access_only']

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        logger.info(f"[Scrapy STDOUT]\n{result.stdout}")
        if result.stderr:
            logger.warning(f"[Scrapy STDERR]\n{result.stderr}")

        return {
            "status": "success",
            "message": "Scraping completed successfully",
            "query": query,
            "profile_id": profile_id
        }

    except subprocess.CalledProcessError as e:
        logger.error(f"Scrapy завершився з помилкою: {e.returncode}")
        logger.error(f"STDOUT:\n{e.stdout}")
        logger.error(f"STDERR:\n{e.stderr}")

        return {
            "status": "error",
            "message": f"Scraping failed with return code {e.returncode}",
            "error": e.stderr,
            "query": query,
            "profile_id": profile_id
        }
