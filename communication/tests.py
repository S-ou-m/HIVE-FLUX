from django.test import TestCase, RequestFactory
from django.utils import timezone
from core.models import College
from accounts.models import User, Role, UserRole, Student
from academics.models import Department
from communication.models import Notice, NoticeReadStatus
from communication.services import NoticeService
from communication.views import notice_list_partial

class NoticeTargetingTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.college = College.objects.create(name="Test College", code="TC")
        self.admin_user = User.objects.create_user(username="admin", email="admin@tc.com", password="password", college=self.college)
        self.student_user = User.objects.create_user(username="student", email="student@tc.com", password="password", college=self.college)
        
        self.admin_role = Role.objects.create(name="Admin", college=self.college)
        self.student_role = Role.objects.create(name="Student", college=self.college)
        
        UserRole.objects.create(user=self.admin_user, role=self.admin_role, college=self.college)
        UserRole.objects.create(user=self.student_user, role=self.student_role, college=self.college)
        
        self.dept_cs = Department.objects.create(name="Computer Science", code="CS", college=self.college)
        self.dept_me = Department.objects.create(name="Mechanical", code="ME", college=self.college)
        
        self.student = Student.objects.create(
            user=self.student_user, 
            college=self.college, 
            enrollment_no="ST001", 
            department=self.dept_cs,
            admission_year=2024
        )

    def test_role_targeting(self):
        """Notices targeted at 'Admin' should not be visible to 'Student'."""
        notice = Notice.objects.create(
            college=self.college,
            title="Admin Notice",
            content="For admins only",
            target_roles=["Admin"],
            status="PUBLISHED",
            published_at=timezone.now()
        )
        
        users = NoticeService.get_targeted_users(notice)
        self.assertIn(self.admin_user, users)
        self.assertNotIn(self.student_user, users)

    def test_department_targeting(self):
        """Notices targeted at 'CS' department should not be visible to students in other departments."""
        notice = Notice.objects.create(
            college=self.college,
            title="CS Notice",
            content="For CS students only",
            target_roles=["Student"],
            status="PUBLISHED",
            published_at=timezone.now()
        )
        notice.target_departments.add(self.dept_cs)
        
        users = NoticeService.get_targeted_users(notice)
        self.assertIn(self.student_user, users)
        
        # Change student department and check
        self.student.department = self.dept_me
        self.student.save()
        
        users = NoticeService.get_targeted_users(notice)
        self.assertNotIn(self.student_user, users)

    def test_read_status_engagement(self):
        """Marking as read should create a NoticeReadStatus record."""
        notice = Notice.objects.create(
            college=self.college,
            title="General Notice",
            content="Hello",
            status="PUBLISHED",
            published_at=timezone.now()
        )
        
        self.assertFalse(NoticeReadStatus.objects.filter(user=self.student_user, notice=notice).exists())
        
        NoticeReadStatus.objects.create(user=self.student_user, notice=notice)
        self.assertTrue(NoticeReadStatus.objects.filter(user=self.student_user, notice=notice).exists())
