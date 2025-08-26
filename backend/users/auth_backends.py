from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.db.models import Q

class UsernameOrEmailBackend(ModelBackend):
    """
    Позволяет логиниться одним полем:
    - если содержит '@' → ищем по email (без учёта регистра),
    - иначе → по username (без учёта регистра).
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        UserModel = get_user_model()
        if username is None:
            # Djoser может прислать email=..., но у нас LOGIN_FIELD=username.
            username = kwargs.get(UserModel.USERNAME_FIELD)

        if not username or not password:
            return None

        qs = None
        if "@" in username:
            qs = UserModel.objects.filter(email__iexact=username)
        else:
            qs = UserModel.objects.filter(username__iexact=username)

        user = qs.first()
        if not user:
            return None

        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None
