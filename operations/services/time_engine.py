import logging
from django.utils import timezone
from datetime import timedelta
from operations.models import ExecutionControl
from operations.services.state_service import SessionStateService

logger = logging.getLogger(__name__)

class TimeEvaluatorEngine:
    """
    Background engine to handle time-based state transitions.
    Typically run via a periodic task or triggered by dashboard loads.
    """

    @classmethod
    def process_pending_sessions(cls, college=None):
        """
        Transitions PENDING sessions to READY if they are within 15 mins of start.
        """
        now = timezone.now()
        ready_window = now + timedelta(minutes=15)
        
        queryset = ExecutionControl.objects.filter(
            status='PENDING',
            scheduled_start__lte=ready_window
        )
        
        if college:
            queryset = queryset.filter(college=college)
            
        count = 0
        for execution in queryset:
            try:
                SessionStateService.transition_to(execution.id, 'READY', metadata={'source': 'TIME_ENGINE'})
                count += 1
            except Exception as e:
                logger.error(f"TimeEngine failed to ready session {execution.id}: {str(e)}")
        
        return count

    @classmethod
    def process_expired_sessions(cls, college=None):
        """
        Transitions READY sessions to EXPIRED if they haven't started past the grace period.
        """
        now = timezone.now()
        
        # A session is expired if it's READY and now > scheduled_start + grace_minutes
        queryset = ExecutionControl.objects.filter(
            status='READY'
        )
        
        if college:
            queryset = queryset.filter(college=college)
            
        count = 0
        for execution in queryset:
            if now > (execution.scheduled_start + timedelta(minutes=execution.grace_minutes)):
                try:
                    SessionStateService.transition_to(execution.id, 'EXPIRED', metadata={'source': 'TIME_ENGINE'})
                    count += 1
                except Exception as e:
                    logger.error(f"TimeEngine failed to expire session {execution.id}: {str(e)}")
        
        return count
