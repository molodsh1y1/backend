from django.utils.deprecation import MiddlewareMixin
from django.contrib.auth.models import AnonymousUser
from dip.models import Profile

class AttachUserProfileMiddleware(MiddlewareMixin):
    def process_request(self, request):
        user = getattr(request, 'user', None)

        if user and not isinstance(user, AnonymousUser) and user.is_authenticated:
            try:
                request.profile = Profile.objects.get(user=user)
            except Profile.DoesNotExist:
                request.profile = None
        else:
            request.profile = None
