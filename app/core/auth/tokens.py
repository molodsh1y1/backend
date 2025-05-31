import secrets

from typing import Any, Dict, Optional
from datetime import timedelta

from django.contrib.sessions.backends.base import SessionBase
from django.http import HttpRequest
from django.utils import timezone

from allauth.headless.tokens.base import AbstractTokenStrategy
from oauth2_provider.models import AccessToken, RefreshToken, Application
from oauth2_provider.settings import oauth2_settings

import settings



def get_or_create_tokens_for_user(user):
    try:
        application = Application.objects.get()
    except Application.DoesNotExist:
        return {"error": "OAuth2 Application not found"}

    access_token = AccessToken.objects.filter(
        user=user,
        application=application,
        expires__gt=timezone.now()
    ).first()

    if access_token and getattr(settings, "REUSE_TOKENS", False):
        refresh_token = RefreshToken.objects.filter(access_token=access_token).first()
    else:
        expires = timezone.now() + timedelta(seconds=oauth2_settings.ACCESS_TOKEN_EXPIRE_SECONDS)

        access_token = AccessToken.objects.create(
            user=user,
            application=application,
            token=secrets.token_urlsafe(32),
            expires=expires,
            scope="read write"
        )

        refresh_token = RefreshToken.objects.create(
            user=user,
            application=application,
            token=secrets.token_urlsafe(32),
            access_token=access_token
        )

    return {
        "access_token": access_token.token,
        "refresh_token": refresh_token.token,
        "expires_in": access_token.expires,
    }


class OAuthTokenStrategy(AbstractTokenStrategy):

    def create_session_token(self, request: HttpRequest) -> str:
        return ''

    def lookup_session(self, session_token: str) -> Optional[SessionBase]:
        return None

    def create_access_token_payload(
        self, request: HttpRequest
    ) -> Optional[Dict[str, Any]]:

        return get_or_create_tokens_for_user(request.user)


def refresh_access_token(refresh_token_value: str):
    try:
        refresh_token = RefreshToken.objects.get(token=refresh_token_value)

        if refresh_token.access_token.expires < timezone.now():
            old_access_token = refresh_token.access_token

            new_access_token = AccessToken.objects.create(
                user=refresh_token.user,
                application=refresh_token.application,
                token=secrets.token_urlsafe(32),
                expires=timezone.now() + timedelta(seconds=oauth2_settings.ACCESS_TOKEN_EXPIRE_SECONDS),
                scope="read write"
            )

            refresh_token.access_token = new_access_token
            refresh_token.save()

            old_access_token.revoke()

            return {
                "access_token": new_access_token.token,
                "refresh_token": refresh_token.token,
                "expires_in": new_access_token.expires,
            }
        else:
            return {
                "access_token": refresh_token.access_token.token,
                "refresh_token": refresh_token.token,
                "expires_in": refresh_token.access_token.expires,
            }

    except RefreshToken.DoesNotExist:
        return {"error": "Refresh token not found"}
