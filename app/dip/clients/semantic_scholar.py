import requests
import time
import logging
from typing import List, Dict, Optional, Any
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)


class SemanticScholarAPI:
    """
    Client for Semantic Scholar Academic Graph API
    """

    BASE_URL = "https://api.semanticscholar.org/graph/v1"

    # Rate limiting: 100 requests per 5 minutes for public API
    REQUEST_DELAY = 3.0  # seconds between requests
    MAX_RETRIES = 3

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.session = self._create_session()
        self.last_request_time = 0

    def _create_session(self) -> requests.Session:
        """Create session with retry strategy"""
        session = requests.Session()

        retry_strategy = Retry(
            total=self.MAX_RETRIES,
            status_forcelist=[429, 500, 502, 503, 504],
            backoff_factor=2,
            respect_retry_after_header=True
        )

        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        return session

    def _rate_limit(self):
        """Implement rate limiting"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time

        if time_since_last < self.REQUEST_DELAY:
            sleep_time = self.REQUEST_DELAY - time_since_last
            logger.debug(f"Rate limiting: sleeping for {sleep_time:.2f} seconds")
            time.sleep(sleep_time)

        self.last_request_time = time.time()

    def _make_request(self, endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Make API request with rate limiting and error handling"""
        self._rate_limit()

        url = f"{self.BASE_URL}/{endpoint}"
        headers = {"User-Agent": "DIP-Scholar-Scraper/1.0"}

        if self.api_key:
            headers["x-api-key"] = self.api_key

        try:
            logger.debug(f"Making request to: {url} with params: {params}")
            response = self.session.get(url, headers=headers, params=params, timeout=30)
            response.raise_for_status()

            return response.json()

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                logger.warning("Rate limit exceeded, waiting longer...")
                time.sleep(60)  # Wait 1 minute for rate limit reset
                return self._make_request(endpoint, params)
            else:
                logger.error(f"HTTP error {e.response.status_code}: {e}")
                raise

        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {e}")
            raise

    def search_papers(self,
                      query: str,
                      year_from: Optional[int] = None,
                      year_to: Optional[int] = None,
                      fields_of_study: Optional[List[str]] = None,
                      publication_types: Optional[List[str]] = None,
                      min_citation_count: Optional[int] = None,
                      open_access_only: bool = False,
                      limit: int = 100,
                      offset: int = 0) -> Dict[str, Any]:
        """
        Search for papers using Semantic Scholar API

        Args:
            query: Search query
            year_from: Start year filter
            year_to: End year filter
            fields_of_study: List of fields to filter by
            publication_types: List of publication types
            min_citation_count: Minimum citation count
            open_access_only: Filter for open access papers
            limit: Number of results (max 100 per request)
            offset: Pagination offset

        Returns:
            API response with papers data
        """

        # Build search parameters
        params = {
            "query": query,
            "limit": min(limit, 100),  # API max is 100 per request
            "offset": offset,
            "fields": "paperId,title,abstract,year,venue,authors,citationCount,referenceCount,influentialCitationCount,isOpenAccess,openAccessPdf,externalIds"
        }

        # Add year filters
        if year_from or year_to:
            year_filter = []
            if year_from:
                year_filter.append(f"{year_from}-")
            if year_to:
                if year_from:
                    year_filter = [f"{year_from}-{year_to}"]
                else:
                    year_filter.append(f"-{year_to}")
            params["year"] = ",".join(year_filter)

        # Add fields of study filter
        if fields_of_study:
            params["fieldsOfStudy"] = ",".join(fields_of_study)

        # Add publication type filter (Semantic Scholar uses different naming)
        if publication_types:
            # Map our types to Semantic Scholar types
            type_mapping = {
                "JournalArticle": "JournalArticle",
                "Conference": "Conference",
                "Review": "Review",
                "Book": "Book",
                "BookSection": "BookSection",
                "Dataset": "Dataset"
            }
            mapped_types = [type_mapping.get(t, t) for t in publication_types]
            params["publicationTypes"] = ",".join(mapped_types)

        # Add minimum citation filter
        if min_citation_count is not None:
            params["minCitationCount"] = min_citation_count

        # Add open access filter
        if open_access_only:
            params["openAccessPdf"] = ""

        return self._make_request("paper/search", params)

    def get_paper_details(self, paper_id: str) -> Dict[str, Any]:
        """Get detailed information about a specific paper"""
        params = {
            "fields": "paperId,title,abstract,year,venue,authors,citationCount,referenceCount,influentialCitationCount,isOpenAccess,openAccessPdf,externalIds,citations,references"
        }

        return self._make_request(f"paper/{paper_id}", params)

    def get_author_details(self, author_id: str) -> Dict[str, Any]:
        """Get detailed information about an author"""
        params = {
            "fields": "authorId,name,affiliations,homepage,paperCount,citationCount,hIndex"
        }

        return self._make_request(f"author/{author_id}", params)

    def search_multiple_pages(self,
                              query: str,
                              total_limit: int = 100,
                              **kwargs) -> List[Dict[str, Any]]:
        """
        Search multiple pages to get more than 100 results

        Args:
            query: Search query
            total_limit: Total number of results to fetch
            **kwargs: Other search parameters

        Returns:
            List of all papers from multiple pages
        """
        all_papers = []
        offset = 0
        page_size = 100

        while len(all_papers) < total_limit:
            remaining = total_limit - len(all_papers)
            current_limit = min(page_size, remaining)

            logger.info(f"Fetching page {offset // page_size + 1}, offset: {offset}, limit: {current_limit}")

            try:
                response = self.search_papers(
                    query=query,
                    limit=current_limit,
                    offset=offset,
                    **kwargs
                )

                papers = response.get("data", [])
                if not papers:
                    logger.info("No more papers found, stopping pagination")
                    break

                all_papers.extend(papers)

                # Check if we've reached the end
                total_available = response.get("total", 0)
                if offset + len(papers) >= total_available:
                    logger.info(f"Reached end of results. Total available: {total_available}")
                    break

                offset += page_size

            except Exception as e:
                logger.error(f"Error fetching page at offset {offset}: {e}")
                break

        logger.info(f"Retrieved {len(all_papers)} papers total")
        return all_papers[:total_limit]
