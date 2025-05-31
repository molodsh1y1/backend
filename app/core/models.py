import random
from datetime import timedelta

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.conf import settings


class UserPhone(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='phones')
    phone_number = models.CharField(max_length=30)
    is_current = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'phone_number')

    def save(self, *args, **kwargs):
        if self.is_current:
            # Set all other phones for this user to not current
            UserPhone.objects.filter(user=self.user, is_current=True).exclude(id=self.id).update(is_current=False)
        super().save(*args, **kwargs)


class VerificationCode(models.Model):
    DIGITS_COUNT = settings.CORE_AUTH_VERIFICATION_CODE_LENGTH
    CODE_TYPE_CHOICES = (
        ('registration', 'Registration'),
        ('password_reset', 'Password Reset'),
        ('email_change', 'Email Change'),
        ('phone_change', 'Phone Change'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='verification_codes')
    email = models.EmailField(null=True, blank=True)
    phone = models.CharField(max_length=30, null=True, blank=True)
    code = models.CharField(max_length=DIGITS_COUNT)
    code_type = models.CharField(max_length=20, choices=CODE_TYPE_CHOICES)
    additional_data = models.JSONField(null=True, blank=True)
    attempts_count = models.PositiveIntegerField(default=0)
    is_used = models.BooleanField(default=False)
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.code:
            self.code = ''.join([str(random.randint(0, 9)) for _ in range(self.DIGITS_COUNT)])

        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(minutes=30)

        super().save(*args, **kwargs)

    def is_valid(self):
        max_attempts = getattr(settings, 'VERIFICATION_CODE_MAX_ATTEMPTS', 5)
        return (not self.is_used and
                self.expires_at > timezone.now() and
                self.attempts_count <= max_attempts)

    @classmethod
    def increment_attempts_for_last_code(cls, email=None, phone=None, code_type=None):
        if not email and not phone:
            return None

        filters = {'is_used': False}

        if email:
            filters['email'] = email
        if phone:
            filters['phone'] = phone
        if code_type:
            filters['code_type'] = code_type

        try:
            verification = cls.objects.filter(**filters).latest('created_at')
            verification.attempts_count += 1
            verification.save(update_fields=['attempts_count', 'is_used'])
            return verification

        except cls.DoesNotExist:
            return None
