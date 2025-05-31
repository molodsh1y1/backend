from rest_framework import serializers
from django.contrib.auth.models import User
from django.conf import settings
from core.models import UserPhone, VerificationCode
from django.contrib.auth import authenticate
import re


class ContactFieldValidationMixin:
    """Base mixin for contact field validation."""

    def validate_contact_fields(self, data, both_allowed=False):
        """
        Validates that at least one contact field is provided.

        Args:
            data: The data dictionary to validate
            both_allowed: If False, raises error when both email and phone are provided
        """
        email = data.get('email')
        phone = data.get('phone')

        if not email and not phone:
            raise serializers.ValidationError("Either email or phone must be provided")

        if not both_allowed and email and phone:
            raise serializers.ValidationError("Both email and phone cannot be provided simultaneously")

        return data


class PhoneFormatValidationMixin:
    """Mixin for phone number format validation."""

    def validate_phone_format(self, phone):
        """Validates phone number format using regex."""
        if phone and not re.match(r'^\+?[0-9]{8,15}$', phone):
            raise serializers.ValidationError("Invalid phone number format")
        return phone


class ContactExistenceValidationMixin:
    """Mixin for validating existence of contacts."""

    def validate_contact_exists(self, data):
        """Validates that a user with the provided contact exists."""
        email = data.get('email')
        phone = data.get('phone')

        if email and not User.objects.filter(email=email).exists():
            raise serializers.ValidationError("No user with this email exists")

        if phone and not UserPhone.objects.filter(phone_number=phone, is_current=True).exists():
            raise serializers.ValidationError("No user with this phone number exists")

        return data


class ContactUniqueValidationMixin:
    """Mixin for validating uniqueness of contacts."""

    def validate_contact_unique(self, data):
        """Validates that the provided contact information is unique."""
        email = data.get('email')
        phone = data.get('phone')

        if email and User.objects.filter(email=email).exists():
            raise serializers.ValidationError("User with this email already exists")

        if phone:
            # Check if phone already exists
            if UserPhone.objects.filter(phone_number=phone, is_current=True).exists():
                raise serializers.ValidationError("User with this phone number already exists")

        return data


class ProfileTypeFieldValidationMixin:
    """Mixin for validating profile type field."""

    def validate_profile_type(self, profile_type):
        """Validates that the registration type is valid."""
        if profile_type not in settings.CORE_AUTH_SETTINGS:
            raise serializers.ValidationError("Invalid registration type")
        return profile_type


class PasswordValidationMixin:
    """Mixin for validating password strength."""

    def validate_password_strength(self, password):
        """Validates that password meets strength requirements:
        - At least 6 characters long
        - Contains both letters and numbers
        """
        if len(password) < 6:
            raise serializers.ValidationError("Password must be at least 6 characters long")
        if not re.match(r'^(?=.*[A-Za-z])(?=.*\d).+$', password):
            raise serializers.ValidationError("Password must contain both letters and numbers")
        return password


class RegistrationRequestSerializer(
    serializers.Serializer,
    ContactFieldValidationMixin,
    PhoneFormatValidationMixin,
    ContactUniqueValidationMixin,
    ProfileTypeFieldValidationMixin,
    PasswordValidationMixin
):
    email = serializers.EmailField(required=False)
    phone = serializers.CharField(required=False)
    password = serializers.CharField(write_only=True)
    first_name = serializers.CharField(required=False)
    last_name = serializers.CharField(required=False)

    def validate(self, data):
        if data.get('phone') and not settings.CORE_AUTH_PHONE_REGISTRATION_ENABLED:
            raise serializers.ValidationError("Phone registration is not enabled")

        data = self.validate_contact_fields(data)

        phone = data.get('phone')
        if phone:
            self.validate_phone_format(phone)

        self.validate_password_strength(data.get('password'))

        return self.validate_contact_unique(data)


class RegistrationConfirmSerializer(serializers.Serializer, ContactFieldValidationMixin):
    email = serializers.EmailField(required=False)
    phone = serializers.CharField(required=False)
    code = serializers.CharField(max_length=settings.CORE_AUTH_VERIFICATION_CODE_LENGTH, required=True)

    def validate(self, data):
        return self.validate_contact_fields(data, both_allowed=True)


class LoginSerializer(serializers.Serializer, ContactFieldValidationMixin):
    email = serializers.EmailField(required=False)
    phone = serializers.CharField(required=False)
    password = serializers.CharField(required=True, write_only=True)

    def validate(self, data):
        data = self.validate_contact_fields(data)

        email = data.get('email')
        phone = data.get('phone')
        password = data.get('password')

        # Authenticate based on email or phone
        if email:
            try:
                user = User.objects.get(email=email)
                user = authenticate(username=user.username, password=password)
            except User.DoesNotExist:
                raise serializers.ValidationError("Invalid email or password")
        else:
            try:
                user_phone = UserPhone.objects.get(phone_number=phone, is_current=True)
                user = authenticate(username=user_phone.user.username, password=password)
            except UserPhone.DoesNotExist:
                raise serializers.ValidationError("Invalid phone number or password")

        if not user:
            raise serializers.ValidationError("Invalid credentials")

        data['user'] = user
        return data


class PasswordResetRequestSerializer(serializers.Serializer,
                                     ContactFieldValidationMixin,
                                     ContactExistenceValidationMixin):
    email = serializers.EmailField(required=False)
    phone = serializers.CharField(required=False)

    def validate(self, data):
        data = self.validate_contact_fields(data, both_allowed=True)
        return self.validate_contact_exists(data)


class PasswordResetConfirmSerializer(serializers.Serializer, ContactFieldValidationMixin, PasswordValidationMixin):
    email = serializers.EmailField(required=False)
    phone = serializers.CharField(required=False)
    code = serializers.CharField(max_length=settings.CORE_AUTH_VERIFICATION_CODE_LENGTH, required=True)
    new_password = serializers.CharField(write_only=True)

    def validate(self, data):
        data = self.validate_contact_fields(data, both_allowed=True)
        self.validate_password_strength(data.get('new_password'))
        return data


class ChangeContactRequestSerializer(serializers.Serializer,
                                     ContactFieldValidationMixin,
                                     PhoneFormatValidationMixin,
                                     ContactUniqueValidationMixin):
    email = serializers.EmailField(required=False)
    phone = serializers.CharField(required=False)

    def validate(self, data):
        data = self.validate_contact_fields(data)

        phone = data.get('phone')
        if phone:
            self.validate_phone_format(phone)

        return self.validate_contact_unique(data)


class ChangeContactConfirmSerializer(serializers.Serializer, ContactFieldValidationMixin):
    email = serializers.EmailField(required=False)
    phone = serializers.CharField(required=False)
    code = serializers.CharField(max_length=settings.CORE_AUTH_VERIFICATION_CODE_LENGTH, required=True)

    def validate(self, data):
        return self.validate_contact_fields(data)


class RefreshTokenSerializer(serializers.Serializer):
    refresh_token = serializers.CharField(required=True)
