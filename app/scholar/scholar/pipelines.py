import logging
from typing import Dict, Any
from asgiref.sync import sync_to_async
from django.db import transaction
from dip.models import ScholarRawRecord, ScholarAuthor

logger = logging.getLogger(__name__)

class ScholarPipeline:
    async def process_item(self, item: Dict[str, Any], spider):
        try:
            authors_data = item.pop('authors_data', [])
            session_id = item.pop('session_id', None)

            paper_defaults = {
                'title': item.get('title', ''),
                'abstract': item.get('abstract', ''),
                'publication_year': item.get('publication_year'),
                'venue': item.get('venue', ''),
                'doi': item.get('doi', ''),
                'url': item.get('url', ''),
                'pdf_url': item.get('pdf_url', ''),
                'citation_count': item.get('citation_count', 0),
                'reference_count': item.get('reference_count', 0),
                'influential_citation_count': item.get('influential_citation_count', 0),
                'is_open_access': item.get('is_open_access', False),
                'profile': item.get('profile'),
            }

            if session_id:
                paper_defaults['scraping_session_id'] = session_id

            paper, created = await sync_to_async(ScholarRawRecord.objects.update_or_create)(
                semantic_scholar_id=item['semantic_scholar_id'],
                defaults=paper_defaults
            )

            if authors_data:
                authors = []
                for author_data in authors_data:
                    if not author_data.get('semantic_scholar_id'):
                        continue

                    author, author_created = await sync_to_async(ScholarAuthor.objects.update_or_create)(
                        semantic_scholar_id=author_data['semantic_scholar_id'],
                        defaults={
                            'full_name': author_data.get('full_name', ''),
                            'url': author_data.get('url', ''),
                            'h_index': author_data.get('h_index'),
                            'paper_count': author_data.get('paper_count', 0),
                            'citation_count': author_data.get('citation_count', 0),
                            'affiliations': author_data.get('affiliations', []),
                        }
                    )
                    authors.append(author)

                await sync_to_async(paper.authors.set)(authors)

            action = "Created" if created else "Updated"
            session_info = f" (Session: {session_id})" if session_id else ""
            logger.info(f"{action} paper: {paper.title[:50]}... {session_info}")

            if hasattr(spider, 'papers_saved'):
                spider.papers_saved += 1

            return item

        except Exception as e:
            logger.error(f"Error saving paper {item.get('semantic_scholar_id', 'unknown')}: {e}")
            if hasattr(spider, 'errors_count'):
                spider.errors_count += 1
            raise
