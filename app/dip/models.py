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
    semantic_scholar_id = models.CharField(max_length=100, unique=True)
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
