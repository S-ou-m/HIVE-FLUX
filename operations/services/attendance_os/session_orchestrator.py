from django.utils import timezone
from django.shortcuts import get_object_or_404
from operations.models import AttendanceSession, TimetableSlotInstance, ScanLog, Attendance
from accounts.models import Student, Faculty
import uuid

class AttendanceSessionOrchestrator:
    """
    The Operational Authority for Attendance Scanning.
    Manages session lifecycles, scan integrity, and live metrics.
    """

    @staticmethod
    def get_active_context(faculty, college):
        """
        Contextual Intelligence: Auto-detects if a live timetable session exists.
        Returns the active session or None.
        """
        now = timezone.now()
        # Find if any session is currently LIVE for this faculty
        active_session = AttendanceSession.objects.filter(
            session_owner=faculty,
            college=college,
            status='LIVE'
        ).first()

        if active_session:
            return active_session

        # If no active session, look for scheduled instances starting around now
        # (Grace period: 15 mins before/after)
        window_start = now - timezone.timedelta(minutes=15)
        window_end = now + timezone.timedelta(minutes=15)
        
        instance = TimetableSlotInstance.objects.filter(
            timetable_slot__assignment__faculty=faculty,
            date=now.date(),
            timetable_slot__start_time__gte=window_start.time(),
            timetable_slot__start_time__lte=window_end.time()
        ).first()

        return instance

    @classmethod
    def start_session(cls, faculty, college, instance=None, mode='QR'):
        """
        Initializes an Operational Attendance Session.
        """
        session = AttendanceSession.objects.create(
            college=college,
            session_owner=faculty,
            slot_instance=instance,
            status='LIVE',
            mode=mode,
            started_at=timezone.now(),
            faculty_snapshot_name=faculty.user.get_full_name(),
            subject_snapshot_name=instance.timetable_slot.assignment.subject.name if instance else "Manual Session",
            expected_count=instance.expected_students if instance else 0
        )
        return session

    @staticmethod
    def process_scan(session, student_id, device_info=None):
        """
        Deterministic Scan Integrity Layer.
        Validates scan, checks for duplicates, and logs telemetry.
        """
        student = get_object_or_404(Student, id=student_id)
        
        # 1. Duplicate Prevention
        exists = Attendance.objects.filter(session=session, student=student).exists()
        if exists:
            ScanLog.objects.create(
                college=session.college,
                session=session,
                user=student.user,
                result='DUPLICATE',
                device_id=device_info.get('device_id') if device_info else None
            )
            return {'status': 'DUPLICATE', 'student': student.user.get_full_name()}

        # 2. Log Success & Create Attendance
        Attendance.objects.create(
            college=session.college,
            session=session,
            student=student,
            status='PRESENT',
            marked_by=session.session_owner.user
        )
        
        ScanLog.objects.create(
            college=session.college,
            session=session,
            user=student.user,
            result='SUCCESS',
            device_id=device_info.get('device_id') if device_info else None
        )

        # 3. Update Session Metrics
        session.present_count = session.records.count()
        session.save()

        return {
            'status': 'SUCCESS', 
            'student': student.user.get_full_name(),
            'enrollment': student.enrollment_no,
            'metrics': AttendanceSessionOrchestrator.get_session_metrics(session)
        }

    @staticmethod
    def get_session_metrics(session):
        """Calculates operational HUD metrics."""
        present = session.present_count
        expected = session.expected_count or 1 # Avoid div by zero
        rate = (present / expected) * 100 if expected > 0 else 0
        
        return {
            'present': present,
            'expected': expected,
            'scan_rate': f"{rate:.0f}%",
            'elapsed_minutes': int((timezone.now() - session.started_at).total_seconds() / 60)
        }

    @staticmethod
    def close_session(session):
        """Finalizes the session and locks it for audit."""
        session.status = 'COMPLETED'
        session.ended_at = timezone.now()
        session.save()
        return session
