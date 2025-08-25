from djoser.email import PasswordResetEmail

class CustomPasswordResetEmail(PasswordResetEmail):
    template_name = "emails/password_reset.html"   # наш html-шаблон
