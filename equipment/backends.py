from django.contrib.auth.backends import BaseBackend
from django.contrib.auth.models import AnonymousUser
from .models import User  # Import your User model
from .views import *

class CustomUserBackend(BaseBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            user = User.objects.using("rit_e_approval").get(staff_id=username)
            if encrypt_password(password) == user.Password:  # Ensure encrypt_password is correct
                return user  # Return the user if authentication succeeds
        except User.DoesNotExist:
            return None
        return None

    def get_user(self, user_id):
        try:
            return User.objects.using("rit_e_approval").get(staff_id=user_id)
        except User.DoesNotExist:
            return None
