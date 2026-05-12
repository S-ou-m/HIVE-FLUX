import random
from faker import Faker
from django.contrib.auth import get_user_model
from core.models import College
from academics.models import Department, Semester, Program
from accounts.models import Student, Guardian, Address

User = get_user_model()
fake = Faker()

def seed_students():
    print("Seeding Students (Bulk Target: 3000)...")
    colleges = College.objects.all()
    if not colleges: return
    
    total_students = 0
    
    for college in colleges:
        programs = Program.objects.filter(college=college)
        for program in programs:
            semesters = Semester.objects.filter(program=program)
            dept = program.department
            
            # Target ~100 students per program per semester
            for semester in semesters:
                print(f"  Populating {program.name} - Sem {semester.number}...")
                students_to_create = []
                users_to_create = []
                
                for _ in range(random.randint(60, 80)): # ~3000 total across all
                    first_name = fake.first_name()
                    last_name = fake.last_name()
                    enrollment_no = f"{college.code}{random.randint(20, 26)}{dept.code}{random.randint(1000, 9999)}"
                    email = f"{enrollment_no.lower()}@student.hiveflux.edu"
                    
                    # Create User (Bulk preparation)
                    user = User(
                        username=enrollment_no,
                        email=email,
                        first_name=first_name,
                        last_name=last_name,
                        college=college
                    )
                    user.set_password('Changeme123!')
                    users_to_create.append(user)

                # Bulk Create Users first
                created_users = User.objects.bulk_create(users_to_create, ignore_conflicts=True)
                
                # Fetch created users back to get IDs
                actual_users = User.objects.filter(username__in=[u.username for u in users_to_create])
                
                students_list = []
                for user in actual_users:
                    student = Student(
                        user=user,
                        college=college,
                        department=dept,
                        current_semester=semester,
                        enrollment_no=user.username,
                        admission_year=random.randint(2022, 2025),
                        phone_no=fake.phone_number()[:15],
                        credit_balance=random.choice([0, 0, 0, 500, 1200, 0]) # Some have advance
                    )
                    students_list.append(student)
                
                Student.objects.bulk_create(students_list, ignore_conflicts=True)
                total_students += len(students_list)
                
                # Create Guardians for a subset (or all)
                # For speed in seeding 3000, we do it in smaller batches
                batch_students = Student.objects.filter(enrollment_no__in=[s.enrollment_no for s in students_list])
                guardians = []
                addresses = []
                for s in batch_students:
                    guardians.append(Guardian(
                        college=college,
                        student=s,
                        name=fake.name(),
                        relation=random.choice(['Father', 'Mother', 'Guardian']),
                        phone=fake.phone_number()[:15],
                        email=fake.email()
                    ))
                    # Polymorphic Address (simplified for seeder)
                    # We'll just create one address per student for realism
                
                Guardian.objects.bulk_create(guardians, ignore_conflicts=True)

    print(f"[OK] {total_students} Students seeded.")

if __name__ == "__main__":
    import django
    import os
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'college_erp.settings')
    django.setup()
    seed_students()
