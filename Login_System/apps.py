from django.apps import AppConfig


class LoginSystemConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'Login_System'

    def ready(self):
        import Login_System.signals
