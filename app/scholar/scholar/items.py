import scrapy


class ScholarItem(scrapy.Item):
    semantic_scholar_id = scrapy.Field()
    title = scrapy.Field()
    abstract = scrapy.Field()
    publication_year = scrapy.Field()
    venue = scrapy.Field()
    doi = scrapy.Field()
    url = scrapy.Field()
    pdf_url = scrapy.Field()
    citation_count = scrapy.Field()
    reference_count = scrapy.Field()
    influential_citation_count = scrapy.Field()
    is_open_access = scrapy.Field()
    profile = scrapy.Field()
    authors_data = scrapy.Field()
