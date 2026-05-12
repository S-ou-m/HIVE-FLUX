import os
import sys
import django

# Setup Django Environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'college_erp.settings')
django.setup()

import random
from core.models import College
from academics.models import Department, Program, Semester, Subject
from accounts.models import Faculty
from operations.models import Timetable, TimetableSlot, Room, SubjectAssignment

def seed_academics():
    print("Seeding Academic Orchestration (Subjects & Timetables)...")
    colleges = College.objects.all()
    
    subjects_by_dept = {
        "CSE": ["Data Structures", "Algorithms", "Operating Systems", "Database Systems", "Computer Networks", "Software Engineering"],
        "ECE": ["Digital Electronics", "Microprocessors", "Signal Processing", "VLSI Design", "Control Systems"],
        "MKT": ["Marketing Management", "Consumer Behavior", "Digital Marketing", "Brand Management", "Market Research"],
        "FIN": ["Corporate Finance", "Investment Analysis", "Portfolio Management", "Financial Modeling", "Derivatives"],
        "IT": ["Web Technologies", "Cyber Security", "Cloud Computing", "Mobile App Dev", "Big Data Analytics"],
        "AS": ["Engineering Physics", "Engineering Chemistry", "Mathematics I", "Mathematics II", "Professional Ethics"]
    }

    for college in colleges:
        departments = Department.objects.filter(college=college)
        for dept in departments:
            programs = Program.objects.filter(department=dept)
            faculty_list = list(Faculty.objects.filter(department=dept))
            if not faculty_list: continue
            
            for program in programs:
                semesters = Semester.objects.filter(program=program)
                for semester in semesters:
                    # Create 4-6 subjects per semester
                    subjects_to_seed = subjects_by_dept.get(dept.code, ["General Subject A", "General Subject B"])
                    
                    created_subjects = []
                    for i, s_name in enumerate(random.sample(subjects_to_seed, min(len(subjects_to_seed), 5))):
                        subject, created = Subject.objects.get_or_create(
                            college=college,
                            semester=semester,
                            code=f"{dept.code}{semester.number}{100+i}",
                            defaults={
                                'name': s_name,
                                'credits': random.choice([3, 4, 5])
                            }
                        )
                        created_subjects.append(subject)

                    # Create Timetable for this semester/section
                    timetable, _ = Timetable.objects.get_or_create(
                        college=college,
                        department=dept,
                        program=program,
                        semester=semester,
                        section="A",
                        defaults={'academic_year': "2025-26"}
                    )

                    # Create Slots (Mon-Fri)
                    rooms = list(Room.objects.filter(college=college))
                    if not rooms: continue
                    
                    for day in range(5): # Mon-Fri
                        # 4 slots per day
                        for slot_idx in range(4):
                            start_times = ["09:00:00", "11:00:00", "13:30:00", "15:30:00"]
                            end_times = ["10:30:00", "12:30:00", "15:00:00", "17:00:00"]
                            
                            subject = random.choice(created_subjects)
                            faculty = random.choice(faculty_list)
                            
                            assignment, _ = SubjectAssignment.objects.get_or_create(
                                college=college,
                                faculty=faculty,
                                subject=subject,
                                semester=semester,
                                defaults={'is_active': True}
                            )

                            TimetableSlot.objects.get_or_create(
                                timetable=timetable,
                                day_of_week=day,
                                start_time=start_times[slot_idx],
                                defaults={
                                    'end_time': end_times[slot_idx],
                                    'assignment': assignment,
                                    'room': random.choice(rooms)
                                }
                            )

    print("[OK] Academic Orchestration Seeded.")

if __name__ == "__main__":
    import django
    import os
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'college_erp.settings')
    django.setup()
    seed_academics()
