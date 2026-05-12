from django.db.models import Avg, Count, Q
from academics.models import SubjectEnrollment, Subject
from operations.models import AttendanceSession, Attendance, TimetableSlotInstance
from lms.models import Submission

class AcademicRadarService:
    """
    🎯 Academic Radar Service
    Orchestrates subject-specific intelligence for the 'Guided Progression' UX.
    """

    @classmethod
    def get_subject_radar(cls, student):
        """Returns subject-wise progression and intelligence signals."""
        enrollments = SubjectEnrollment.objects.filter(student=student).select_related('subject')
        
        radar_data = []
        for enrollment in enrollments:
            # 1. Syllabus Progress (REAL CALCULATION)
            # Logic: (Completed Sessions / Total Scheduled Sessions)
            # We'll estimate total sessions as 45 (approx. 15 weeks * 3 sessions)
            # or better: count Scheduled + Completed instances for this semester.
            total_instances = TimetableSlotInstance.objects.filter(
                timetable_slot__assignment__subject=enrollment.subject,
                status__in=['SCHEDULED', 'COMPLETED', 'LOCKED']
            ).count()
            completed_instances = TimetableSlotInstance.objects.filter(
                timetable_slot__assignment__subject=enrollment.subject,
                status__in=['COMPLETED', 'LOCKED']
            ).count()
            
            syllabus_pct = int((completed_instances / total_instances) * 100) if total_instances > 0 else 0
            
            # 2. Subject-Specific Attendance (REAL CALCULATION)
            # ... (lines 25-40 in original remain mostly the same but I'll optimize)
            subject_sessions = AttendanceSession.objects.filter(
                slot_instance__timetable_slot__assignment__subject=enrollment.subject,
                status__in=['COMPLETED', 'LOCKED']
            )
            total_sessions = subject_sessions.count()
            
            if total_sessions > 0:
                present_sessions = Attendance.objects.filter(
                    student=student,
                    session__in=subject_sessions,
                    status='PRESENT'
                ).count()
                attendance_pct = int((present_sessions / total_sessions) * 100)
            else:
                attendance_pct = 0 # No sessions held yet
            
            # 3. Grade Trajectory (REAL CALCULATION from Submissions)
            subject_submissions = Submission.objects.filter(
                student=student,
                assignment__subject=enrollment.subject,
                marks__isnull=False
            )
            if subject_submissions.exists():
                grade_pct = int(subject_submissions.aggregate(Avg('marks'))['marks__avg'])
            else:
                grade_pct = 0
            
            # 4. Success Signal Tones
            if attendance_pct > 85:
                tone = 'emerald'
            elif attendance_pct > 75:
                tone = 'blue'
            elif attendance_pct > 60:
                tone = 'orange'
            else:
                tone = 'red'
            
            radar_data.append({
                'subject_code': enrollment.subject.code,
                'subject_name': enrollment.subject.name,
                'syllabus': syllabus_pct,
                'attendance': attendance_pct,
                'grade': grade_pct,
                'tone': tone,
                'signals': [
                    {'type': 'STABLE', 'icon': 'check-circle'} if tone == 'emerald' else {'type': 'RISK', 'icon': 'exclamation-triangle'}
                ]
            })
            
        return radar_data
