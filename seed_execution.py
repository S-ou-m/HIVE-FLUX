from accounts.models import User, Student, Faculty
from academics.models import Department, Program, Semester, Subject, SubjectEnrollment
from operations.models import Room, Timetable, TimetableSlot, TimetableSlotInstance, AttendanceSession, SubjectAssignment, EnrollmentMapping
from django.utils import timezone
import datetime

def seed():
    print("Seeding SaaS-Grade Operational Data (v3.1 Architecture)...")
    
    # 1. Get/Create Core Dependencies
    faculty_user = User.objects.filter(is_staff=True).first()
    if not faculty_user:
        print("Error: No admin/staff user found.")
        return
    
    dept = Department.objects.first()
    if not dept:
        print("Error: No Department found.")
        return
        
    college = dept.college
    faculty, _ = Faculty.objects.get_or_create(
        user=faculty_user, 
        college=college,
        defaults={'designation': 'Senior Architect'}
    )
    
    program = Program.objects.filter(department=dept).first()
    semester = Semester.objects.filter(program=program).first()
    subject = Subject.objects.filter(semester=semester).first()
    
    if not all([program, semester, subject]):
        print("Error: Academic structure incomplete (Prog/Sem/Sub).")
        return

    # 2. Create Room
    room, _ = Room.objects.get_or_create(
        college=college,
        name="Nexus Command Lab 101",
        defaults={'capacity': 120, 'floor': 'Top Floor', 'building': 'Innovation Center'}
    )

    # 3. Create Subject Assignment
    assignment, _ = SubjectAssignment.objects.get_or_create(
        college=college,
        faculty=faculty,
        subject=subject,
        semester=semester
    )

    # 4. Create Master Timetable (Weekly Plan)
    timetable, _ = Timetable.objects.get_or_create(
        college=college,
        department=dept,
        program=program,
        semester=semester,
        section="A",
        academic_year="2026",
        defaults={'is_active': True}
    )

    # 5. Create Timetable Slot (Recurring Mon-Fri)
    today_num = timezone.now().isoweekday() # 1-7
    slot, _ = TimetableSlot.objects.get_or_create(
        timetable=timetable,
        day_of_week=today_num,
        start_time=datetime.time(9, 0),
        defaults={
            'end_time': datetime.time(18, 0),
            'assignment': assignment,
            'room': room,
            'slot_type': 'REGULAR'
        }
    )

    # 6. Create Runtime Instance (Today's Execution Anchor)
    instance, created = TimetableSlotInstance.objects.get_or_create(
        timetable_slot=slot,
        date=timezone.now().date(),
        defaults={'status': 'SCHEDULED'}
    )

    # 7. Create Enrollment Mapping (Student-Batch Binding)
    student = Student.objects.filter(college=college).first()
    if student:
        EnrollmentMapping.objects.get_or_create(
            college=college,
            student=student,
            department=dept,
            program=program,
            semester=semester,
            section="A",
            defaults={'is_active': True}
        )

    # 8. Orchestrate Attendance Session
    session, session_created = AttendanceSession.objects.get_or_create(
        college=college,
        slot_instance=instance,
        defaults={
            'faculty_snapshot_name': faculty_user.get_full_name(),
            'subject_snapshot_name': subject.name,
            'session_owner': faculty,
            'status': 'LIVE',
            'started_at': timezone.now()
        }
    )

    if session_created:
        print(f"Success: Created Session '{session.subject_snapshot_name}' linked to Timetable Slot Instance.")
    else:
        print(f"Info: Session already active for today.")

if __name__ == "__main__":
    seed()
