from allauth.account.adapter import DefaultAccountAdapter
from django.core.exceptions import PermissionDenied

class CustomAccountAdapter(DefaultAccountAdapter):
    def is_open_for_signup(self, request):
        return True

    def clean_authentication(self, user, request):
        if not user.is_active:
            raise PermissionDenied("This account is disabled.")
