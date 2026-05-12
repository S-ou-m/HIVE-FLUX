import logging
from django.db import transaction
from django.utils import timezone
from operations.models import StudentSubjectCache, EnrollmentMapping, TimetableSlot
from accounts.models import Student

logger = logging.getLogger(__name__)

class CacheService:
    """
    Manages the Performance Layer (StudentSubjectCache).
    Handles rebuilding and versioning of the cache.
    """

    @classmethod
    def rebuild_student_cache(cls, student_id):
        """
        Rebuilds the subject cache for a specific student.
        Triggered on enrollment or timetable changes.
        """
        try:
            student = Student.objects.get(id=student_id)
            
            with transaction.atomic():
                # 1. Clear existing cache for this student
                StudentSubjectCache.objects.filter(student=student).delete()
                
                # 2. Get active enrollments
                enrollments = EnrollmentMapping.objects.filter(student=student, is_active=True)
                
                new_entries = []
                for enrollment in enrollments:
                    # Find matching timetable slots
                    slots = TimetableSlot.objects.filter(
                        timetable__department=enrollment.department,
                        timetable__program=enrollment.program,
                        timetable__semester=enrollment.semester,
                        timetable__section=enrollment.section,
                        is_active=True
                    ).select_related('timetable', 'assignment__faculty', 'assignment__subject')
                    
                    for slot in slots:
                        new_entries.append(StudentSubjectCache(
                            college=student.college,
                            student=student,
                            subject=slot.assignment.subject,
                            faculty=slot.assignment.faculty,
                            timetable=slot.timetable,
                            cache_version=1 # Future: Increment based on global version
                        ))
                
                # 3. Bulk Create for performance
                if new_entries:
                    StudentSubjectCache.objects.bulk_create(new_entries, ignore_conflicts=True)
                    
                logger.info(f"Rebuilt Cache for Student {student_id} | Entries: {len(new_entries)}")
                
        except Exception as e:
            logger.error(f"Failed to rebuild cache for student {student_id}: {str(e)}")

    @classmethod
    def invalidate_all_in_college(cls, college_id):
        """
        Force rebuild for all students in a college (e.g., after a major timetable update).
        """
        students = Student.objects.filter(college_id=college_id, is_deleted=False).values_list('id', flat=True)
        for s_id in students:
            cls.rebuild_student_cache(s_id)
