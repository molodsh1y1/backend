from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from django.utils.module_loading import import_string

from core.models import VerificationCode
import logging

logger = logging.getLogger(__name__)


def send_verification_code_email(email, code):
    """Send verification code to email"""
    try:
        subject = "Your verification code"
        message = f"Your verification code is: {code}"
        from_email = settings.DEFAULT_FROM_EMAIL
        logger.info(f"Sending verification code {code} to {email}")
        send_mail(subject, message, from_email, [email], fail_silently=False)
        return True
    except Exception as e:
        logger.error(f"Failed to send verification email: {str(e)}")
        return False


def send_verification_code_sms(phone, code):
    """Send verification code via SMS using your SMS provider"""
    try:
        # This is a placeholder. Implement your SMS sending logic here
        # using your preferred SMS provider API
        logger.info(f"Sending verification code {code} to {phone}")
        # Example: sms_provider.send_message(phone, f"Your verification code is: {code}")
        return True
    except Exception as e:
        logger.error(f"Failed to send verification SMS: {str(e)}")
        return False


def generate_verification_code(user=None, email=None, phone=None, code_type='registration', additional_data=None):
    """Generate and save a verification code"""
    filters = {'is_used': False, 'code_type': code_type}

    if email:
        filters['email'] = email
    if phone:
        filters['phone'] = phone

    VerificationCode.objects.filter(**filters).update(is_used=True)

    verification_code = VerificationCode(
        user=user,
        email=email,
        phone=phone,
        code_type=code_type,
        additional_data=additional_data,
    )
    verification_code.save()

    # Send code to the specified channel
    if email:
        send_verification_code_email(email, verification_code.code)
    elif phone:
        send_verification_code_sms(phone, verification_code.code)

    return verification_code


def get_auth_class_by_profile_type(settings_key: str, profile_type: str):
    try:
        return import_string(settings.CORE_AUTH_SETTINGS[profile_type][settings_key])
    except KeyError:
        raise ValueError(f"Invalid registration type: {profile_type}")
