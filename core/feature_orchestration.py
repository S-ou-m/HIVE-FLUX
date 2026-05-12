from django.db import connection

class FeatureReadiness:
    """
    🏗️ Operational Feature Registry
    Determines if institutional modules are ready for execution 
    based on schema state and dependency health.
    """
    
    @classmethod
    def is_ready(cls, table_name: str) -> bool:
        """Safe check for table existence without throwing OperationalError."""
        try:
            return table_name in connection.introspection.table_names()
        except Exception:
            return False

    @classmethod
    def get_status_report(cls):
        """Returns a health report of the Intelligence Layer."""
        return {
            'core_erp': True, # Base assumption for now
            'intelligence_signals': cls.is_ready('accounts_successsignal'),
            'confidence_history': cls.is_ready('accounts_successconfidencehistory'),
            'intervention_bus': cls.is_ready('accounts_interventionorchestration'),
            'achievement_vault': cls.is_ready('accounts_academicachievement'),
        }

def safe_intelligence_execution(feature_table):
    """Decorator or wrapper to prevent execution on non-migrated features."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            if not FeatureReadiness.is_ready(feature_table):
                return None # Graceful degradation
            return func(*args, **kwargs)
        return wrapper
    return decorator
