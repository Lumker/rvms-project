from django.apps import AppConfig

class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = '_core'
    verbose_name = 'Core'
    
    def ready(self):
        # Import any signals here if needed
        pass