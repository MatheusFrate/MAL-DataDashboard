from django.apps import AppConfig


class MalApiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'mal_api'

    def ready(self):
        import mal_api.dash_app  # Importe o arquivo dash_app.py