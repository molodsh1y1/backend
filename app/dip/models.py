from django.db import models
from django.contrib.auth.models import User


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=31, blank=True, null=True)
    last_name = models.CharField(max_length=31, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Profile'
        verbose_name_plural = 'Profiles'

    def __str__(self):
        return f'{self.id} {self.first_name}, {self.last_name}'


class ScholarRawRecord(models.Model):
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, blank=True, null=True, related_name='scholar_raw_records')
    scraping_session = models.ForeignKey('ScrapingSession', on_delete=models.CASCADE, blank=True, null=True,related_name='papers')
    semantic_scholar_id = models.CharField(max_length=100, unique=True, null=True, blank=True)
    title = models.CharField(max_length=1000, blank=True, null=True)
    abstract = models.TextField(blank=True, null=True)
    publication_year = models.IntegerField(blank=True, null=True)
    venue = models.CharField(max_length=500, blank=True, null=True)
    doi = models.CharField(max_length=255, blank=True, null=True, db_index=True)
    url = models.URLField(blank=True, null=True)
    pdf_url = models.URLField(blank=True, null=True)
    citation_count = models.IntegerField(default=0)
    reference_count = models.IntegerField(default=0)
    influential_citation_count = models.IntegerField(default=0)
    is_open_access = models.BooleanField(default=False)
    authors = models.ManyToManyField('ScholarAuthor', blank=True, related_name='scholar_raw_records')
    scraped_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Scholar Raw Record'
        verbose_name_plural = 'Scholar Raw Records'
        ordering = ['-scraped_at']
        indexes = [
            models.Index(fields=['publication_year']),
            models.Index(fields=['citation_count']),
            models.Index(fields=['venue']),
        ]

    def __str__(self):
        return f'{self.title} ({self.publication_year})'


class ScholarAuthor(models.Model):
    semantic_scholar_id = models.CharField(max_length=100, unique=True)
    full_name = models.CharField(max_length=255, blank=True, null=True)
    url = models.URLField(blank=True, null=True)
    h_index = models.IntegerField(blank=True, null=True)
    paper_count = models.IntegerField(default=0)
    citation_count = models.IntegerField(default=0)
    affiliations = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Scholar Author'
        verbose_name_plural = 'Scholar Authors'
        ordering = ['full_name']
        indexes = [
            models.Index(fields=['h_index']),
            models.Index(fields=['citation_count']),
        ]

    def __str__(self):
        return f'{self.full_name} (h-index: {self.h_index})'


class ScrapingSession(models.Model):
    """
    Represents a single scraping session/request with specific parameters
    """
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='scraping_sessions')

    # Search parameters
    query = models.CharField(max_length=500)
    year_from = models.IntegerField(blank=True, null=True)
    year_to = models.IntegerField(blank=True, null=True)
    limit = models.IntegerField(default=100)
    fields_of_study = models.JSONField(default=list)
    publication_types = models.JSONField(default=list)
    min_citation_count = models.IntegerField(blank=True, null=True)
    open_access_only = models.BooleanField(default=False)

    # Session metadata
    task_id = models.CharField(max_length=100, blank=True, null=True)
    status = models.CharField(max_length=20, choices=[
        ('PENDING', 'Pending'),
        ('STARTED', 'Started'),
        ('SUCCESS', 'Success'),
        ('FAILURE', 'Failure'),
        ('RETRY', 'Retry'),
        ('REVOKED', 'Revoked')
    ], default='PENDING')

    # Results
    papers_found = models.IntegerField(default=0)
    papers_saved = models.IntegerField(default=0)
    errors_count = models.IntegerField(default=0)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(blank=True, null=True)
    completed_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        verbose_name = 'Scraping Session'
        verbose_name_plural = 'Scraping Sessions'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['profile', 'status']),
            models.Index(fields=['task_id']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"Session {self.id}: {self.query} ({self.status})"

    @property
    def duration(self):
        """Calculate scraping duration"""
        if self.started_at and self.completed_at:
            return self.completed_at - self.started_at
        return None

    def get_search_params_display(self):
        """Human readable search parameters"""
        params = [f"Query: {self.query}"]

        if self.year_from or self.year_to:
            year_range = f"{self.year_from or 'Any'} - {self.year_to or 'Any'}"
            params.append(f"Years: {year_range}")

        if self.fields_of_study:
            params.append(f"Fields: {', '.join(self.fields_of_study)}")

        if self.publication_types:
            params.append(f"Types: {', '.join(self.publication_types)}")

        if self.min_citation_count:
            params.append(f"Min citations: {self.min_citation_count}")

        if self.open_access_only:
            params.append("Open access only")

        return " | ".join(params)
