from django.db import transaction
from django.core.exceptions import ValidationError
from operations.models import ExecutionControl, SessionStateLog, AttendanceSession
from operations.events import EventDispatcher, SESSION_STARTED, SESSION_COMPLETED, SESSION_PAUSED, SESSION_RESUMED
import logging

logger = logging.getLogger(__name__)

class SessionStateService:
    """
    Central Orchestrator for Session State Transitions.
    Enforces valid transitions, concurrency safety, and audit logging.
    """

    VALID_TRANSITIONS = {
        'PENDING': ['READY', 'CANCELLED'],
        'READY': ['LIVE', 'CANCELLED', 'EXPIRED'],
        'LIVE': ['PAUSED', 'COMPLETED', 'FAILED'],
        'PAUSED': ['LIVE', 'COMPLETED', 'FAILED'],
        'COMPLETED': [], # Terminal
        'CANCELLED': [], # Terminal
        'FAILED': ['READY', 'LIVE'], # Recovery states
        'EXPIRED': ['READY'], # Recovery
    }

    @classmethod
    def transition_to(cls, execution_id, target_status, user=None, reason=None, metadata=None):
        """
        Main entry point for all state changes.
        Uses optimistic locking (version) and atomic transactions.
        """
        with transaction.atomic():
            # 1. Fetch & Lock
            execution = ExecutionControl.objects.select_for_update().get(id=execution_id)
            old_status = execution.status

            # 2. Validate Transition
            if target_status not in cls.VALID_TRANSITIONS.get(old_status, []):
                raise ValidationError(f"Invalid transition from {old_status} to {target_status}")

            # 3. Update State
            execution.status = target_status
            execution.version += 1
            if user:
                execution.override_by = user
                execution.override_reason = reason
            
            # 4. Handle Specific Logic (Side Effects)
            cls._handle_side_effects(execution, old_status, target_status, user, metadata)
            
            execution.save()
            
            # 5. Log Transition
            cls._log_transition(execution, old_status, target_status, user, metadata)
            
            return execution

    @classmethod
    def _handle_side_effects(cls, execution, old_status, target_status, user, metadata):
        from django.utils import timezone
        now = timezone.now()

        # PENDING/READY -> LIVE: Start the AttendanceSession
        if target_status == 'LIVE':
            execution.actual_start = now
            # Create or resume AttendanceSession
            session, created = AttendanceSession.objects.get_or_create(
                slot_instance=execution.slot_instance,
                defaults={
                    'college': execution.college,
                    'session_owner': execution.slot_instance.timetable_slot.assignment.faculty,
                    'faculty_snapshot_name': execution.slot_instance.timetable_slot.assignment.faculty.user.get_full_name(),
                    'subject_snapshot_name': execution.slot_instance.timetable_slot.assignment.subject.name,
                    'status': 'LIVE',
                    'started_at': now
                }
            )
            
            if created:
                # Capture Snapshot Metadata
                session.snapshot_metadata = {
                    'room': execution.slot_instance.timetable_slot.room.name if execution.slot_instance.timetable_slot.room else 'N/A',
                    'scheduled_start': execution.scheduled_start.isoformat(),
                    'faculty_id': str(session.session_owner.id)
                }
                session.save()
                EventDispatcher.dispatch(SESSION_STARTED, execution.college.id, {'session_id': str(session.id)})
            else:
                session.status = 'LIVE'
                session.save()
                EventDispatcher.dispatch(SESSION_RESUMED, execution.college.id, {'session_id': str(session.id)})

        # LIVE -> PAUSED
        elif target_status == 'PAUSED':
            session = getattr(execution.slot_instance, 'session', None)
            if session:
                session.status = 'PAUSED'
                session.save()
                EventDispatcher.dispatch(SESSION_PAUSED, execution.college.id, {'session_id': str(session.id)})

        # LIVE/PAUSED -> COMPLETED
        elif target_status == 'COMPLETED':
            execution.actual_end = now
            session = getattr(execution.slot_instance, 'session', None)
            if session:
                session.status = 'COMPLETED'
                session.ended_at = now
                session.save()
                EventDispatcher.dispatch(SESSION_COMPLETED, execution.college.id, {
                    'session_id': str(session.id),
                    'faculty_id': str(session.session_owner.id)
                })

    @classmethod
    def _log_transition(cls, execution, old_status, target_status, user, metadata):
        session = getattr(execution.slot_instance, 'session', None)
        if session:
            SessionStateLog.objects.create(
                session=session,
                from_state=old_status,
                to_state=target_status,
                action_type='MANUAL' if user else 'AUTO',
                trigger_source='ADMIN' if user else 'SYSTEM',
                changed_by=user,
                metadata=metadata or {}
            )
