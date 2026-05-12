import os
import sys
import django

# Setup Django Environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'college_erp.settings')

# Force InMemoryChannelLayer for seeding (avoids Redis dependency)
from django.conf import settings
if not settings.configured:
    django.setup()
settings.CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels.layers.InMemoryChannelLayer",
    },
}

import random
from datetime import timedelta
from django.utils import timezone
from core.models import College
from accounts.models import Student, Faculty
from operations.models import TimetableSlot, TimetableSlotInstance, AttendanceSession, Attendance, ScanLog

def seed_operations():
    print("Seeding Operational Telemetry (Attendance & Scans)...")
    colleges = College.objects.all()
    
    # We will seed the last 30 days
    today = timezone.now().date()
    
    for college in colleges:
        print(f"  Processing {college.name}...")
        slots = TimetableSlot.objects.filter(timetable__college=college).select_related('timetable', 'assignment__subject', 'assignment__faculty', 'room')
        students_by_semester = {} # Cache for performance
        
        for i in range(30, -1, -1): # Last 30 days up to today
            current_date = today - timedelta(days=i)
            day_of_week = current_date.weekday()
            
            if day_of_week > 4: continue # Skip weekends
            
            day_slots = slots.filter(day_of_week=day_of_week)
            
            for slot in day_slots:
                # 1. Create Instance
                instance, created = TimetableSlotInstance.objects.get_or_create(
                    timetable_slot=slot,
                    date=current_date,
                    defaults={'status': 'COMPLETED' if i > 0 else 'SCHEDULED'}
                )
                
                if i == 0: continue # Don't mark attendance for future/today's pending classes
                
                # 2. Create Attendance Session
                session, s_created = AttendanceSession.objects.get_or_create(
                    college=college,
                    slot_instance=instance,
                    defaults={
                        'session_owner': slot.assignment.faculty,
                        'faculty_snapshot_name': slot.assignment.faculty.user.get_full_name(),
                        'subject_snapshot_name': slot.assignment.subject.name,
                        'started_at': timezone.make_aware(timezone.datetime.combine(current_date, slot.start_time)),
                        'status': 'LOCKED'
                    }
                )
                
                if s_created:
                    # 3. Fetch students for this semester
                    sem_key = f"{slot.timetable.program_id}_{slot.timetable.semester_id}"
                    if sem_key not in students_by_semester:
                        students_by_semester[sem_key] = list(Student.objects.filter(
                            college=college,
                            department=slot.timetable.department,
                            current_semester=slot.timetable.semester
                        ))
                    
                    target_students = students_by_semester[sem_key]
                    attendance_records = []
                    scan_events = []
                    
                    present_count = 0
                    for student in target_students:
                        # Realism: Some students are toppers (95%+), some are at risk (40-60%)
                        # Deterministic hash based on student ID to keep behavior consistent across days
                        student_seed = hash(str(student.id)) % 100
                        
                        is_present = True
                        status = 'PRESENT'
                        
                        if student_seed < 5: # 5% Chronic absentees
                            is_present = random.random() > 0.8
                        elif student_seed < 15: # 10% At risk
                            is_present = random.random() > 0.4
                        else: # 85% Normal/Good
                            is_present = random.random() > 0.1
                        
                        if not is_present:
                            status = 'ABSENT'
                        else:
                            present_count += 1
                            if random.random() > 0.9: status = 'LATE'
                            
                            # Create Scan Log for presence
                            scan_events.append(ScanLog(
                                college=college,
                                session=session,
                                user=student.user,
                                result='SUCCESS',
                                device_id='SEEDER_SIM',
                                scan_source='QR_DYNAMIC'
                            ))

                        attendance_records.append(Attendance(
                            college=college,
                            session=session,
                            student=student,
                            status=status,
                            marked_at=session.started_at + timedelta(minutes=random.randint(5, 15))
                        ))

                    # Bulk create for the session
                    Attendance.objects.bulk_create(attendance_records)
                    ScanLog.objects.bulk_create(scan_events)
                    
                    # Update session counts
                    session.expected_count = len(target_students)
                    session.present_count = present_count
                    session.save()

            if i % 10 == 0: print(f"    ... day {30-i}/30 processed")

    print("[OK] Operational Telemetry Seeded.")

if __name__ == "__main__":
    import django
    import os
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'college_erp.settings')
    django.setup()
    seed_operations()
