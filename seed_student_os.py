import os
import django
import uuid
from django.utils import timezone
from datetime import timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'college_erp.settings')
django.setup()

from accounts.models import User, Student, StudentOperationalEvent, IdentitySession, TrustedDevice
from core.models import College

def seed_student_data():
    college = College.objects.first()
    if not college:
        print("❌ No college found. Run seed_db.py first.")
        return

    # 1. Create/Get a Student User
    user, created = User.objects.get_or_create(
        username='student_alpha',
        defaults={
            'email': 'student@execution.os',
            'college': college,
            'first_name': 'Arian',
            'last_name': 'Nayak'
        }
    )
    if created:
        user.set_password('pass123')
        user.save()

    student, created = Student.objects.get_or_create(
        user=user,
        defaults={
            'college': college,
            'enrollment_no': 'EXE-STU-2026-001',
            'admission_year': 2026,
            'operational_state': 'ACTIVE',
            'reputation_score': 94
        }
    )

    # 2. Create Trusted Device & Session
    device, _ = TrustedDevice.objects.get_or_create(
        user=user,
        device_id='STU-DEV-99X',
        defaults={
            'platform': 'iOS (iPhone 15)',
            'trust_state': 'TRUSTED',
            'browser_signature': 'Mozilla/5.0...'
        }
    )

    IdentitySession.objects.get_or_create(
        user=user,
        device=device,
        defaults={
            'status': 'ACTIVE',
            'expires_at': timezone.now() + timedelta(days=7),
            'trust_score': 98
        }
    )

    # 3. Seed Operational Events (Telemetry)
    events = [
        ('CHECK_IN', 'Campus Access Verified at Main Gate.', 'SUCCESS', 'HIGH'),
        ('SESSION_ATTENDANCE', 'Attendance marked for Advanced Algorithms.', 'SUCCESS', 'NORMAL'),
        ('ASSIGNMENT_SUBMISSION', 'Assignment "Distributed Systems" submitted on time.', 'SUCCESS', 'NORMAL'),
        ('GPA_UPDATE', 'Mid-term GPA recalculated: 3.85', 'INFO', 'NORMAL'),
        ('SECURITY_LOGIN', 'New login detected from iPhone 15.', 'INFO', 'LOW'),
    ]

    for e_type, desc, sev, prio in events:
        StudentOperationalEvent.objects.create(
            college=college,
            student=student,
            actor=user,
            event_type=e_type,
            description=desc,
            severity=sev,
            priority=prio,
            context={'ip': '192.168.1.5'}
        )

    print(f"DONE: Student OS Seeded - {user.username} is now ACTIVE.")

if __name__ == "__main__":
    seed_student_data()
