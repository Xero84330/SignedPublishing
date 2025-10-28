from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.contrib.auth import get_user_model

User = get_user_model()

class MySocialAccountAdapter(DefaultSocialAccountAdapter):
    def pre_social_login(self, request, sociallogin):
        """
        Automatically connect the social account to an existing user
        with the same email address, if it exists.
        """
        if not sociallogin.is_existing and sociallogin.user.email:
            try:
                existing_user = User.objects.get(email=sociallogin.user.email)
                sociallogin.connect(request, existing_user)
            except User.DoesNotExist:
                pass

    def populate_user(self, request, sociallogin, data):
        """
        Ensures the new user gets a username derived from their email
        if it's not provided by Google.
        """
        user = super().populate_user(request, sociallogin, data)
        if not user.username and user.email:
            user.username = user.email.split('@')[0]
        return user
