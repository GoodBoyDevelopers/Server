from django.apps import AppConfig


class YoutubesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'youtubes'

    def ready(self):
        import youtubes.signals