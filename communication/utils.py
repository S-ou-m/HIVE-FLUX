from django.db.models import Q
from django.utils import timezone
from .models import Notice

def get_targeted_notices(user, college):
    """
    Returns a queryset of notices targeted at the given user and college.
    """
    # 1. Base Query: Published notices for this college
    notices = Notice.objects.filter(
        college=college,
        status='PUBLISHED',
        published_at__lte=timezone.now()
    )
    
    # Exclude expired notices
    notices = notices.filter(Q(expires_at__isnull=True) | Q(expires_at__gt=timezone.now()))
    
    # 2. Apply Targeting Filters
    role_names = user.userrole_set.values_list('role__name', flat=True)
    
    target_filter = Q(target_roles=[]) # All users if empty
    if role_names:
        for role in role_names:
            target_filter |= Q(target_roles__contains=role)
            
    # For students/faculty, check department
    student = getattr(user, 'student', None)
    faculty = getattr(user, 'faculty', None)
    
    dept_filter = Q(target_departments__isnull=True)
    if student and student.department:
        dept_filter |= Q(target_departments=student.department)
    if faculty and faculty.department:
        dept_filter |= Q(target_departments=faculty.department)
        
    sem_filter = Q(target_semesters__isnull=True)
    if student and student.current_semester:
        sem_filter |= Q(target_semesters=student.current_semester)
        
    return notices.filter(target_filter & dept_filter & sem_filter).distinct()
