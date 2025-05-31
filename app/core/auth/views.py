import logging

from django.contrib.auth.models import Permission
from django.contrib.auth.models import User
from django.utils.module_loading import import_string
from django.conf import settings

from rest_framework.views import APIView
from rest_framework import viewsets, status, mixins
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from core.models import VerificationCode, UserPhone
from core.auth.tokens import get_or_create_tokens_for_user, refresh_access_token
from .serializers import (
    RegistrationConfirmSerializer,
    LoginSerializer, PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer, ChangeContactRequestSerializer, ChangeContactConfirmSerializer,
    RefreshTokenSerializer, RegistrationRequestSerializer
)
from .utils import generate_verification_code
from dip.adapters import ProfileAdapter

logger = logging.getLogger(__name__)


class AuthViewSet(viewsets.GenericViewSet):
    permission_classes = [AllowAny]

    @action(detail=False, methods=['post'])
    def registration_request(self, request):
        """First step of registration - request verification code"""
        serializer = RegistrationRequestSerializer(data=request.data)

        if serializer.is_valid():
            email = serializer.validated_data.get('email')
            phone = serializer.validated_data.get('phone')

            generate_verification_code(
                email=email,
                phone=phone,
                code_type='registration',
                additional_data=serializer.validated_data
            )

            return Response({"message": "Verification code sent", "email": email, "phone": phone},
                            status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def registration_confirm(self, request):
        """Second step of registration - verify code and create user"""
        serializer = RegistrationConfirmSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data.get('email')
            phone = serializer.validated_data.get('phone')
            code = serializer.validated_data.get('code')

            VerificationCode.increment_attempts_for_last_code(
                email=email,
                phone=phone,
                code_type='registration')

            # Verify code
            try:
                # Handle fixed verification code if enabled
                if (settings.CORE_AUTH_USE_FIXED_VERIFICATION_CODE and
                        code == settings.CORE_AUTH_FIXED_VERIFICATION_CODE):
                    logger.debug(f"Using fixed verification code for registration: {code}")

                    # Get the latest unused verification code for this email/phone
                    if email:
                        verification = VerificationCode.objects.filter(
                            email=email,
                            code_type='registration',
                            is_used=False
                        ).latest('created_at')
                    else:
                        verification = VerificationCode.objects.filter(
                            phone=phone,
                            code_type='registration',
                            is_used=False
                        ).latest('created_at')
                else:
                    # Normal verification code
                    if email:
                        verification = VerificationCode.objects.filter(
                            email=email,
                            code=code,
                            code_type='registration',
                            is_used=False
                        ).latest('created_at')
                    else:
                        verification = VerificationCode.objects.filter(
                            phone=phone,
                            code=code,
                            code_type='registration',
                            is_used=False
                        ).latest('created_at')

                    if not verification.is_valid():
                        return Response({"error": "Verification code expired"},
                                        status=status.HTTP_400_BAD_REQUEST)

                # Create user
                username = email if email else phone
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=verification.additional_data['password'],
                    first_name=verification.additional_data.get('first_name', ''),
                    last_name=verification.additional_data.get('last_name', '')
                )

                # create profile
                ProfileAdapter().create_profile(user)

                # Create phone if provided
                if phone:
                    UserPhone.objects.create(user=user, phone_number=phone, is_current=True)

                # Mark code as used
                verification.is_used = True
                verification.save()

                tokens = get_or_create_tokens_for_user(user)
                return Response(tokens, status=status.HTTP_200_OK)

            except VerificationCode.DoesNotExist:
                return Response({"error": "Invalid verification code"},
                                status=status.HTTP_400_BAD_REQUEST)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def login(self, request):
        """Login with email/phone and password, return tokens"""
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            tokens = get_or_create_tokens_for_user(user)
            return Response(tokens, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def password_reset_request(self, request):
        """First step of password reset - request verification code"""
        serializer = PasswordResetRequestSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data.get('email')
            phone = serializer.validated_data.get('phone')

            if email:
                user = User.objects.get(email=email)
                verification_code = generate_verification_code(
                    user=user,
                    email=email,
                    code_type='password_reset'
                )
            else:
                user_phone = UserPhone.objects.get(phone_number=phone, is_current=True)
                verification_code = generate_verification_code(
                    user=user_phone.user,
                    phone=phone,
                    code_type='password_reset'
                )

            return Response({"message": "Password reset verification code sent"},
                            status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def password_reset_confirm(self, request):
        """Second step of password reset - verify code and set new password"""
        serializer = PasswordResetConfirmSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data.get('email')
            phone = serializer.validated_data.get('phone')
            code = serializer.validated_data.get('code')
            new_password = serializer.validated_data.get('new_password')

            VerificationCode.increment_attempts_for_last_code(
                email=email,
                phone=phone,
                code_type='password_reset')

            try:
                # Handle fixed verification code if enabled
                if (settings.CORE_AUTH_USE_FIXED_VERIFICATION_CODE and
                        code == settings.CORE_AUTH_FIXED_VERIFICATION_CODE):
                    logger.debug(f"Using fixed verification code for password reset: {code}")

                    if email:
                        user = User.objects.get(email=email)
                        verification = VerificationCode.objects.filter(
                            user=user,
                            email=email,
                            code_type='password_reset',
                            is_used=False
                        ).latest('created_at')
                    else:
                        user_phone = UserPhone.objects.get(phone_number=phone, is_current=True)
                        user = user_phone.user
                        verification = VerificationCode.objects.filter(
                            user=user,
                            phone=phone,
                            code_type='password_reset',
                            is_used=False
                        ).latest('created_at')
                else:
                    if email:
                        user = User.objects.get(email=email)
                        verification = VerificationCode.objects.filter(
                            user=user,
                            email=email,
                            code=code,
                            code_type='password_reset',
                            is_used=False
                        ).latest('created_at')
                    else:
                        user_phone = UserPhone.objects.get(phone_number=phone, is_current=True)
                        user = user_phone.user
                        verification = VerificationCode.objects.filter(
                            user=user,
                            phone=phone,
                            code=code,
                            code_type='password_reset',
                            is_used=False
                        ).latest('created_at')

                if not verification.is_valid():
                    return Response({"error": "Verification code expired"},
                                    status=status.HTTP_400_BAD_REQUEST)

                # Set new password
                user.set_password(new_password)
                user.save()

                # Mark code as used
                verification.is_used = True
                verification.save()

                return Response({"message": "Password reset successful"},
                                status=status.HTTP_200_OK)

            except (User.DoesNotExist, UserPhone.DoesNotExist, VerificationCode.DoesNotExist):
                return Response({"error": "Invalid verification code"},
                                status=status.HTTP_400_BAD_REQUEST)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def change_contact_request(self, request):
        """First step of email/phone change - request verification code"""
        serializer = ChangeContactRequestSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data.get('email')
            phone = serializer.validated_data.get('phone')

            # Generate verification code for either email or phone
            code_type = 'contact_change'
            verification_code = generate_verification_code(
                user=request.user,
                email=email,
                phone=phone,
                code_type=code_type
            )

            message = "Verification code sent" + (" to new email" if email else " to new phone number")
            return Response({"message": message}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def change_contact_confirm(self, request):
        """Second step of email/phone change - verify code and change contact information"""
        serializer = ChangeContactConfirmSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data.get('email')
            phone = serializer.validated_data.get('phone')
            code = serializer.validated_data.get('code')

            # Common code_type for both contact types
            code_type = 'contact_change'

            # Increment attempts counter (only one will have effect as the other is None)
            VerificationCode.increment_attempts_for_last_code(
                email=email,
                phone=phone,
                code_type=code_type)

            try:
                # Query will automatically filter based on email or phone
                # Since one of them is None, it will work correctly
                verification = VerificationCode.objects.filter(
                    user=request.user,
                    email=email,
                    phone=phone,
                    code=code,
                    code_type=code_type,
                    is_used=False
                ).latest('created_at')

                if not verification.is_valid():
                    return Response({"error": "Verification code expired"},
                                    status=status.HTTP_400_BAD_REQUEST)

                # Apply changes based on which field is not None
                if email:
                    # Change email
                    request.user.email = email
                    request.user.save()
                    message = "Email changed successfully"
                else:
                    # Update user phones
                    # Set all existing phones to not current
                    UserPhone.objects.filter(user=request.user).update(is_current=False)

                    # Create new phone as current
                    UserPhone.objects.create(
                        user=request.user,
                        phone_number=phone,
                        is_current=True
                    )
                    message = "Phone number changed successfully"

                # Mark code as used
                verification.is_used = True
                verification.save()

                return Response({"message": message}, status=status.HTTP_200_OK)

            except VerificationCode.DoesNotExist:
                return Response({"error": "Invalid verification code"},
                                status=status.HTTP_400_BAD_REQUEST)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def refresh_token(self, request):
        """Refresh access token"""
        serializer = RefreshTokenSerializer(data=request.data)
        if serializer.is_valid():
            refresh_token_value = serializer.validated_data.get('refresh_token')
            tokens = refresh_access_token(refresh_token_value)

            return Response(tokens, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
