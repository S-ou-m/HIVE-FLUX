from django.apps import AppConfig


class OperationsConfig(AppConfig):
    name = 'operations'

    def ready(self):
        import operations.signals
