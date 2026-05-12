from django.utils import timezone
from .models import Notification, Notice
from finance.models import Invoice
from academics.models import Department, Program
from accounts.models import Student, User, Faculty
from django.urls import reverse
from django.db.models import Q

class NotificationService:
    @staticmethod
    def create_notification(user, college, title, message, priority='INFO', type='SYSTEM', action_url=None, group_key=None):
        """
        Creates a new notification or updates an existing unread one with the same group_key.
        """
        if group_key:
            existing = Notification.objects.filter(
                user=user, 
                college=college, 
                group_key=group_key, 
                is_read=False
            ).first()
            
            if existing:
                existing.title = title
                existing.message = message
                existing.priority = priority
                existing.created_at = timezone.now() # Bump to top
                existing.save()
                return existing

        return Notification.objects.create(
            user=user,
            college=college,
            title=title,
            message=message,
            priority=priority,
            type=type,
            action_url=action_url,
            group_key=group_key
        )

    @classmethod
    def generate_system_insights(cls, user, college):
        """
        Scans the system for critical issues and generates/updates notifications.
        """
        # 1. Finance: Overdue Invoices
        overdue_invoices = Invoice.objects.filter(college=college, status='OVERDUE').count()
        if overdue_invoices > 0:
            cls.create_notification(
                user=user,
                college=college,
                title="Finance Alert: Overdue Fees",
                message=f"{overdue_invoices} students have overdue fees. Immediate action recommended.",
                priority='CRITICAL',
                type='FINANCE',
                action_url=reverse('admin_finance_partial'),
                group_key='finance_overdue'
            )

        # 2. Academics: Empty Departments
        all_depts = Department.objects.filter(college=college)
        empty_depts_count = 0
        for dept in all_depts:
            if not Program.objects.filter(department=dept).exists():
                empty_depts_count += 1
        
        if empty_depts_count > 0:
            cls.create_notification(
                user=user,
                college=college,
                title="Academics: Empty Departments",
                message=f"{empty_depts_count} departments have no programs assigned. Impact: Students cannot enroll.",
                priority='WARNING',
                type='ACADEMIC',
                action_url=reverse('admin_academics_partial'),
                group_key='academics_empty_depts'
            )

        # 3. Students: New Admissions
        yesterday = timezone.now() - timezone.timedelta(days=1)
        new_students = Student.objects.filter(college=college, created_at__gte=yesterday).count()
        if new_students > 0:
            cls.create_notification(
                user=user,
                college=college,
                title="New Enrollments",
                message=f"{new_students} new students joined in the last 24 hours.",
                priority='INFO',
                type='STUDENT',
                action_url=reverse('admin_students_partial'),
                group_key='student_new_enrollments'
            )

class NoticeService:
    @staticmethod
    def get_targeted_users(notice):
        """
        Identifies all users who should see this notice based on targeting rules.
        """
        users = User.objects.filter(college=notice.college, is_active=True)
        
        # Role Filter
        if notice.target_roles:
            users = users.filter(userrole__role__name__in=notice.target_roles)
            
        # Department Filter
        if notice.target_departments.exists():
            depts = notice.target_departments.all()
            users = users.filter(
                Q(student__department__in=depts) | Q(faculty__department__in=depts)
            )
            
        # Semester Filter
        if notice.target_semesters.exists():
            sems = notice.target_semesters.all()
            users = users.filter(student__current_semester__in=sems)
            
        return users.distinct()

    @classmethod
    def publish_notice(cls, notice):
        """
        Publishes a notice and generates notifications for all targeted users.
        """
        if notice.status == 'PUBLISHED':
            return
            
        notice.status = 'PUBLISHED'
        notice.published_at = timezone.now()
        notice.save()
        
        # Push notifications to all targeted users
        targeted_users = cls.get_targeted_users(notice)
        
        # Batch create notifications to avoid N+1 issues
        notifications = []
        for user in targeted_users:
            notifications.append(Notification(
                college=notice.college,
                user=user,
                title=notice.title,
                message=notice.content[:200] + ('...' if len(notice.content) > 200 else ''),
                priority=notice.priority,
                type=notice.notice_type,
                action_url=reverse('notice_center') if not notice.action_url else notice.action_url,
                group_key=f"notice_{notice.id}"
            ))
        
        Notification.objects.bulk_create(notifications)
