from django.utils import timezone
import datetime
import json
import hashlib
from django.db import transaction
from django.db.models import F
from operations.models import (
    AttendanceSession, Attendance, ScanLog, SessionEnrollmentSnapshot
)

class ValidationService:
    """
    Enterprise Scan Validation Engine.
    Implements cryptographically secure, pipeline-based validation.
    """
    
    SECRET_KEY = "IIT_GRADE_SECRET_2026"

    @staticmethod
    def verify_qr_signature(raw_data):
        try:
            data = json.loads(raw_data)
            payload = f"{data['user_id']}{data['issued_at']}{data['nonce']}"
            expected_sig = hashlib.sha256(f"{payload}{ValidationService.SECRET_KEY}".encode()).hexdigest()
            
            if data['signature'] != expected_sig:
                return False, "SIGNATURE_MISMATCH", data
            return True, "VALID", data
        except Exception:
            return False, "DECODE_ERROR", None

    @staticmethod
    def process_scan(session, raw_data, admin_user, device_id="WEBCAM_01", confidence_score=None, ip_address=None, location_data=None):
        start_time = datetime.datetime.now()
        
        # 1. Cryptographic Authentication
        is_authentic, error_code, payload = ValidationService.verify_qr_signature(raw_data)
        if not is_authentic:
            return ValidationService._log_failure(session, admin_user, 'INVALID', device_id, raw_data)

        user_id = payload['user_id']
        issued_at = datetime.datetime.fromisoformat(payload['issued_at'])
        
        # 2. Anti-Replay (15s TTL)
        if timezone.now() > issued_at + datetime.timedelta(seconds=15):
            return ValidationService._log_failure(session, admin_user, 'EXPIRED', device_id, raw_data, user_id)

        # 3. System Authority Check
        if session.status not in ['LIVE', 'GRACE']:
            return False, f"Session is currently {session.status}", "SESSION_NOT_OPERATIONAL"

        # 4. Snapshot Enrollment Check (High Integrity)
        from accounts.models import Student
        student = Student.objects.filter(user_id=user_id, college=session.college).first()
        
        if not student:
            return ValidationService._log_failure(session, admin_user, 'NOT_ENROLLED', device_id, raw_data, user_id)

        is_enrolled = SessionEnrollmentSnapshot.objects.filter(
            session=session,
            student=student
        ).exists()

        if not is_enrolled:
            return ValidationService._log_failure(session, admin_user, 'NOT_ENROLLED', device_id, raw_data, user_id)

        # 5. Atomic Persistence Pipeline
        with transaction.atomic():
            attendance, created = Attendance.objects.get_or_create(
                session=session,
                student=student,
                defaults={'college': session.college, 'marked_by': admin_user}
            )
            
            if not created:
                return ValidationService._log_failure(session, admin_user, 'DUPLICATE', device_id, raw_data, user_id)

            # Atomic Counter Sync
            AttendanceSession.objects.filter(id=session.id).update(present_count=F('present_count') + 1)
            
            latency = int((datetime.datetime.now() - start_time).total_seconds() * 1000)
            
            ScanLog.objects.create(
                college=session.college,
                session=session,
                user_id=user_id,
                result='SUCCESS',
                latency_ms=latency,
                device_id=device_id,
                raw_data=raw_data,
                session_version=session.version,
                confidence_score=confidence_score or 1.0,
                ip_address=ip_address,
                location_data=location_data
            )

        return True, f"Attendance marked for {student.user.get_full_name()}", "SUCCESS"

    @staticmethod
    def _log_failure(session, admin_user, result, device_id, raw_data, user_id=None):
        ScanLog.objects.create(
            college=session.college,
            session=session,
            user_id=user_id if user_id else admin_user.id,
            result=result,
            device_id=device_id,
            raw_data=raw_data,
            session_version=session.version
        )
        return False, f"Scan Failed: {result}", result
