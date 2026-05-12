from dataclasses import dataclass
from typing import Any, Dict, Optional
import logging

logger = logging.getLogger(__name__)

@dataclass
class DomainEvent:
    name: str
    data: Dict[str, Any]
    college_id: Any
    timestamp: Any

# Event Names
SESSION_STARTED = "SESSION_STARTED"
SESSION_PAUSED = "SESSION_PAUSED"
SESSION_RESUMED = "SESSION_RESUMED"
SESSION_COMPLETED = "SESSION_COMPLETED"
SESSION_CANCELLED = "SESSION_CANCELLED"
FRAUD_DETECTED = "FRAUD_DETECTED"

class EventDispatcher:
    """Explicit Domain Event Dispatcher (Atomic & Traceable)"""
    
    @staticmethod
    def dispatch(event_name: str, college_id: Any, data: Dict[str, Any]):
        from django.utils import timezone
        
        event = DomainEvent(
            name=event_name,
            data=data,
            college_id=college_id,
            timestamp=timezone.now()
        )
        
        logger.info(f"[DOMAIN_EVENT] {event_name} | College: {college_id} | Data: {data}")
        
        # In a larger system, this would push to a message bus (Redis/Kafka)
        # For now, we trigger synchronous consumers (explicitly)
        
        if event_name == SESSION_COMPLETED:
            from operations.services.analytics_service import sync_faculty_worklog
            sync_faculty_worklog(event)
            
        if event_name == FRAUD_DETECTED:
            # Notify admins / update security logs
            pass
