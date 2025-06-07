import logging
from typing import Optional, List, Dict, Any
import scrapy
from scrapy import signals
from asgiref.sync import sync_to_async
from dip.models import Profile
from scholar.scholar.items import ScholarItem
from dip.clients.semantic_scholar import SemanticScholarAPI

logger = logging.getLogger(__name__)

class RawDataSpider(scrapy.Spider):
    name = 'raw_data_spider'
    allowed_domains = []
    start_urls = []

    def __init__(self,
                 query: str,
                 year_from: Optional[int] = None,
                 year_to: Optional[int] = None,
                 limit: int = 100,
                 fields_of_study: Optional[List[str]] = None,
                 publication_types: Optional[List[str]] = None,
                 min_citation_count: Optional[int] = None,
                 open_access_only: bool = False,
                 profile_id: Optional[int] = None,
                 session_id: Optional[int] = None,
                 *args, **kwargs):

        super().__init__(*args, **kwargs)

        self.query = query
        self.year_from = int(year_from) if year_from else None
        self.year_to = int(year_to) if year_to else None
        self.limit = int(limit) if limit else 100
        self.fields_of_study = fields_of_study or []
        self.publication_types = publication_types or []
        self.min_citation_count = int(min_citation_count) if min_citation_count else None
        self.open_access_only = bool(open_access_only)
        self.profile_id = int(profile_id) if profile_id else None
        self.session_id = int(session_id) if session_id else None

        self.api_client = SemanticScholarAPI()
        self.papers_processed = 0
        self.papers_saved = 0
        self.errors_count = 0

        logger.info(f"Spider initialized: query={self.query}, session_id={self.session_id}")

    def start_requests(self):
        return []

    async def start(self):
        try:
            logger.info("Starting paper search via Semantic Scholar API")

            papers = self.api_client.search_multiple_pages(
                query=self.query,
                total_limit=self.limit,
                year_from=self.year_from,
                year_to=self.year_to,
                fields_of_study=self.fields_of_study,
                publication_types=self.publication_types,
                min_citation_count=self.min_citation_count,
                open_access_only=self.open_access_only
            )

            logger.info(f"Found {len(papers)} papers from API")

            for paper_data in papers:
                try:
                    item = await self.create_scholar_item(paper_data)
                    if item:
                        self.papers_processed += 1
                        yield item
                except Exception as e:
                    self.errors_count += 1
                    logger.error(f"Error processing paper {paper_data.get('paperId', 'unknown')}: {e}")
                    continue

        except Exception as e:
            logger.error(f"Error in paper search: {e}")
            raise

    async def create_scholar_item(self, paper_data: Dict[str, Any]) -> Optional[ScholarItem]:
        try:
            if not paper_data.get('paperId') or not paper_data.get('title'):
                return None

            item = ScholarItem()

            item['semantic_scholar_id'] = paper_data['paperId']
            item['title'] = paper_data.get('title', '').strip()
            item['abstract'] = paper_data.get('abstract', '') or ''
            item['publication_year'] = paper_data.get('year')
            item['venue'] = paper_data.get('venue', '') or ''
            item['url'] = f"https://www.semanticscholar.org/paper/{paper_data['paperId']}"

            open_access_pdf = paper_data.get('openAccessPdf')
            if open_access_pdf and isinstance(open_access_pdf, dict):
                item['pdf_url'] = open_access_pdf.get('url', '')
            else:
                item['pdf_url'] = ''

            external_ids = paper_data.get('externalIds') or {}
            item['doi'] = external_ids.get('DOI', '') or ''

            item['citation_count'] = paper_data.get('citationCount', 0) or 0
            item['reference_count'] = paper_data.get('referenceCount', 0) or 0
            item['influential_citation_count'] = paper_data.get('influentialCitationCount', 0) or 0
            item['is_open_access'] = bool(paper_data.get('isOpenAccess', False))

            authors_data = []
            for author in paper_data.get('authors', []):
                if not author.get('authorId'):
                    continue

                author_data = {
                    'semantic_scholar_id': author['authorId'],
                    'full_name': author.get('name', '') or '',
                    'url': f"https://www.semanticscholar.org/author/{author['authorId']}",
                    'h_index': None,
                    'paper_count': 0,
                    'citation_count': 0,
                    'affiliations': []
                }
                authors_data.append(author_data)

            item['authors_data'] = authors_data
            item['session_id'] = self.session_id

            if self.profile_id:
                try:
                    profile = await sync_to_async(Profile.objects.get)(id=self.profile_id)
                    item['profile'] = profile
                except Profile.DoesNotExist:
                    item['profile'] = None
            else:
                item['profile'] = None

            return item

        except Exception as e:
            logger.error(f"Error creating item for paper {paper_data.get('paperId')}: {e}")
            return None

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = cls(*args, **kwargs)
        crawler.signals.connect(spider.spider_closed, signal=signals.spider_closed)
        return spider

    def spider_closed(self, spider):
        logger.info(f"SPIDER CLOSED - Query: {self.query}, Papers: {self.papers_processed}, Saved: {self.papers_saved}, Errors: {self.errors_count}")
