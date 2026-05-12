from datetime import datetime, timedelta
from django.utils import timezone
from accounts.models import IdentityScanEvent, PresencePolicy
from operations.models import Attendance, AttendanceSession

class InferenceOrchestrator:
    """
    Presence Intelligence Engine: Infers operational state from identity events.
    """
    
    def __init__(self, college):
        self.college = college
        self.policy = PresencePolicy.objects.filter(college=college, is_default=True).first()

    def process_identity_event(self, event):
        """
        Main entry point for broadcasting presence signals from an identity scan.
        """
        if event.verification_state != 'SUCCESS':
            return None

        # 1. Check for Active Classroom Context
        # Find sessions owned by this user that are currently LIVE
        active_sessions = AttendanceSession.objects.filter(
            session_owner__user=event.session.user,
            status='LIVE',
            college=self.college
        )

        for session in active_sessions:
            self.reconcile_faculty_presence(session, event)

    def reconcile_faculty_presence(self, session, event):
        """
        Logs faculty presence against their own session.
        """
        # In a real enterprise system, this might trigger a 'PresenceVerified' 
        # event on the session for audit purposes.
        session.snapshot_metadata['last_presence_verified'] = str(timezone.now())
        session.save()

    def infer_student_attendance(self, session, student, scan_event):
        """
        Infers student attendance based on policy rules.
        """
        if not self.policy:
            # Fallback to simple marking if no policy exists
            return self._mark_present(session, student)

        # Apply Policy Rules
        # Rule: Late Entry Threshold
        session_start = session.started_at
        scan_time = scan_event.timestamp
        
        minutes_late = (scan_time - session_start).total_seconds() / 60
        
        status = 'PRESENT'
        if minutes_late > self.policy.late_entry_threshold_mins:
            status = 'LATE'
            
        return self._mark_present(session, student, status)

    def _mark_present(self, session, student, status='PRESENT'):
        attendance, created = Attendance.objects.get_or_create(
            session=session,
            student=student,
            college=self.college,
            defaults={'status': status}
        )
        
        if not created and attendance.status != status:
            attendance.status = status
            attendance.save()
            
        return attendance
