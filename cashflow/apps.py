from django.apps import AppConfig


class CashflowConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'cashflow'
# cashflow/apps.py
def ready(self):
    import cashflow.signals
