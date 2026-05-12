import os
import django
import sys
from datetime import datetime, time, date, timedelta
from django.utils import timezone

# Set up Django environment
sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'college_erp.settings')
django.setup()

from accounts.models import User, Faculty, College
from operations.models import (
    Room, Timetable, TimetableSlot, SubjectAssignment, 
    TimetableSlotInstance, ExecutionControl
)
from academics.models import Department, Subject, Program, Semester

def seed():
    # 0. Get or Create College
    college, _ = College.objects.get_or_create(
        name="IIT Bombay",
        defaults={'code': 'IITB'}
    )

    # 1. Get or Create Faculty
    faculty_user = User.objects.filter(email='faculty@test.com').first()
    if not faculty_user:
        faculty_user = User.objects.create_user(
            username='faculty_test',
            email='faculty@test.com',
            password='Password123!',
            first_name='Dr. Richard',
            last_name='Feynman'
        )
        faculty_user.college = college
        faculty_user.save()
    
    dept, _ = Department.objects.get_or_create(
        college=college,
        name='Computer Science',
        defaults={'code': 'CSE'}
    )

    faculty, _ = Faculty.objects.get_or_create(
        user=faculty_user,
        defaults={
            'college': college,
            'department': dept,
            'designation': 'Professor',
            'phone_no': '9876543210'
        }
    )

    print(f"Seeding sessions for: {faculty_user.get_full_name()} ({faculty_user.email})")

    # 2. Academic Core
    program, _ = Program.objects.get_or_create(
        college=college,
        department=dept,
        name='B.Tech CSE',
        defaults={'duration_years': 4}
    )
    semester, _ = Semester.objects.get_or_create(
        college=college,
        program=program,
        number=4
    )
    subject, _ = Subject.objects.get_or_create(
        college=college,
        semester=semester,
        name='Quantum Computing',
        defaults={'code': 'QC101', 'credits': 4}
    )
    room, _ = Room.objects.get_or_create(
        college=college,
        name='Room 101',
        defaults={'capacity': 60}
    )

    # 3. Timetable & Assignment
    timetable, _ = Timetable.objects.get_or_create(
        college=college,
        department=dept,
        program=program,
        semester=semester,
        section='A',
        defaults={'academic_year': '2026', 'is_active': True}
    )

    assignment, _ = SubjectAssignment.objects.get_or_create(
        college=college,
        faculty=faculty,
        subject=subject,
        semester=semester
    )

    # 4. Slots for Today
    now = timezone.now()
    today = now.date()
    # Django weekday() is 0=Mon, 6=Sun. Model is 1=Mon, 7=Sun.
    current_day_int = today.weekday() + 1

    # Slot 1: Past
    s1_start = (now - timedelta(hours=2)).replace(minute=0, second=0).time()
    s1_end = (now - timedelta(hours=1)).replace(minute=0, second=0).time()
    
    # Slot 2: Current (READY)
    s2_start = (now - timedelta(minutes=5)).time()
    s2_end = (now + timedelta(minutes=55)).time()
    
    # Slot 3: Future
    s3_start = (now + timedelta(hours=1)).replace(minute=0, second=0).time()
    s3_end = (now + timedelta(hours=2)).replace(minute=0, second=0).time()

    slots_data = [
        (s1_start, s1_end, 'COMPLETED'),
        (s2_start, s2_end, 'READY'),
        (s3_start, s3_end, 'PENDING'),
    ]

    for start, end, target_status in slots_data:
        slot, _ = TimetableSlot.objects.get_or_create(
            timetable=timetable,
            day_of_week=current_day_int,
            start_time=start,
            end_time=end,
            defaults={'assignment': assignment, 'room': room, 'is_active': True}
        )

        instance, _ = TimetableSlotInstance.objects.get_or_create(
            timetable_slot=slot,
            date=today,
            defaults={'status': 'SCHEDULED'}
        )

        execution, _ = ExecutionControl.objects.get_or_create(
            slot_instance=instance,
            defaults={
                'college': college,
                'status': target_status,
                'scheduled_start': timezone.make_aware(datetime.combine(today, start)),
                'scheduled_end': timezone.make_aware(datetime.combine(today, end)),
            }
        )
        print(f"Created/Updated Execution: {execution.id} - {target_status} at {start}")

if __name__ == "__main__":
    seed()
