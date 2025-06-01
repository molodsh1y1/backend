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
    title = models.CharField(max_length=255, blank=True, null=True)
    url = models.URLField(unique=True)
    publication_year = models.IntegerField(blank=True, null=True)
    authors = models.ManyToManyField('ScholarAuthor', blank=True, related_name='scholar_raw_records')
    scraped_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Scholar Raw Record'
        verbose_name_plural = 'Scholar Raw Records'
        ordering = ['-scraped_at']

    def __str__(self):
        return f'{self.title} ({self.scraped_at})'


class ScholarAuthor(models.Model):
    full_name = models.CharField(max_length=255, blank=True, null=True)
    url = models.URLField(blank=True, null=True)

    class Meta:
        verbose_name = 'Scholar Author'
        verbose_name_plural = 'Scholar Authors'
        ordering = ['full_name']
