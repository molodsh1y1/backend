from .models import Profile


class ProfileAdapter:
    def create_profile(self, user):
        profile, created = Profile.objects.get_or_create(
            user=user,
            defaults={
                'first_name': user.first_name,
                'last_name': user.last_name,
            }
        )
