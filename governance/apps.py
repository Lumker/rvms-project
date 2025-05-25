from django.apps import AppConfig

class GovernanceConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'governance'
    verbose_name = 'Governance Management'

    def ready(self):
        import governance.signals